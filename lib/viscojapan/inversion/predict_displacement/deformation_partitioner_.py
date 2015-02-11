import numpy as np
import h5py

from ..result_file import ResultFileReader
from ...epochal_data import EpochalSitesFileReader, EpochalFileReader, \
     DiffED, EpochalG, EpochalIncrSlipFileReader
from ...utils import as_string
from ...sites import Site
from ...displacement import Disp

__all__ =['DeformPartitioner']
__author__ = 'zy'

class DeformPartitioner(object):
    def __init__(self,
                 file_G0,
                 result_file,
                 fault_file,
                 files_Gs = None,
                 file_incr_slip0 = None,
                 ):

        result_file_reader = ResultFileReader(result_file)
        self.result_file_reader = result_file_reader

        self.epochs = result_file_reader.epochs
        self.num_epochs = len(self.epochs)

        self.file_G0 = file_G0
        self.file_G0_reader = EpochalSitesFileReader(
            epoch_file = self.file_G0,
            )

        self.slip = result_file_reader.get_slip(fault_file=fault_file)

        self.files_Gs = files_Gs

        self._assert_all_G_files_have_the_same_sites_list()

        self.sites_for_prediction = self.file_G0_reader.filter_sites

        self.nlin_par_names = result_file_reader.nlin_par_names
        self.delta_nlin_pars = result_file_reader.delta_nlin_par_values

        self.file_incr_slip0 = file_incr_slip0
        self._check_incr_slip0_file_spacing()


    def _assert_all_G_files_have_the_same_sites_list(self):
        reader = EpochalFileReader(self.file_G0)
        sites = as_string(reader['sites'])

        for G in self.files_Gs:
            reader = EpochalFileReader(G)
            assert sites == as_string(reader['sites'])

    def _check_incr_slip0_file_spacing(self):
        reader  = EpochalIncrSlipFileReader(self.file_incr_slip0)
        assert reader.epochs == self.epochs, \
               '''Epochs of initial slip input is the same as that is in the result file
{slip0}
{result}
'''.format(slip0 = reader.epochs, result=self.epochs)


    def E_cumu_slip(self, nth_epoch):
        cumuslip = self.slip.get_cumu_slip_at_nth_epoch(nth_epoch).reshape([-1,1])
        G0 = self.file_G0_reader[0]
        disp = np.dot(G0, cumuslip)
        if self.files_Gs is not None:
            disp += self._nlin_correction_E_cumu_slip(nth_epoch)
        return disp

    def _nlin_correction_E_cumu_slip(self, nth_epoch):
        reader = EpochalIncrSlipFileReader(self.file_incr_slip0)

        slip0 = reader.get_cumu_slip_at_nth_epoch(nth_epoch)

        dGs = []
        for file_G, par in zip(self.files_Gs, self.nlin_par_names):
            G0 = EpochalG(self.file_G0)
            G = EpochalG(file_G)
            diffG = DiffED(ed1=G0, ed2=G, wrt=par)
            dGs.append(diffG[0])

        corr = None
        for dG, dpar in zip(dGs, self.delta_nlin_pars):
            if corr is None:
                corr  = np.dot(dG, slip0)*dpar
            else:
                corr += np.dot(dG, slip0)*dpar
        return corr


    def E_co(self):
        return self.E_cumu_slip(0)

    def E_aslip(self, nth_epoch):
        return self.E_cumu_slip(nth_epoch) - self.E_co()

    def R_nth_epoch(self, from_nth_epoch, to_epoch):
        epochs = self.epochs
        from_epoch = epochs[from_nth_epoch]

        del_epoch = to_epoch - from_epoch
        del_epoch = int(del_epoch)

        if del_epoch <= 0:
            return np.zeros([self.file_G0_reader[0].shape[0],1])

        G = self.file_G0_reader[del_epoch] - self.file_G0_reader[0]
        s = self.slip.get_incr_slip_at_nth_epoch(from_nth_epoch).reshape([-1,1])
        disp = np.dot(G, s)
        if self.files_Gs is not None:
            corr = self._nlin_correction_R_nth_epoch(from_nth_epoch, to_epoch)
            disp += corr
        return disp

    def _nlin_correction_R_nth_epoch(self, from_nth_epoch, to_epoch):
        from_epoch = int(self.epochs[from_nth_epoch])
        reader = EpochalIncrSlipFileReader(self.file_incr_slip0)
        slip0 = reader[from_epoch]

        del_epoch = int(to_epoch - from_epoch)

        dGs = []
        for file_G, par in zip(self.files_Gs, self.nlin_par_names):
            G0 = EpochalG(self.file_G0)
            G = EpochalG(file_G)
            diffG = DiffED(ed1=G0, ed2=G, wrt=par)
            dG0 = diffG[0]
            dG = diffG[del_epoch]
            dGs.append(dG-dG0)

        corr = None
        for dG, dpar in zip(dGs, self.delta_nlin_pars):
            if corr is None:
                corr  = np.dot(dG, slip0)*dpar
            else:
                corr += np.dot(dG, slip0)*dpar
        return corr

    def R_co(self, epoch):
        return self.R_nth_epoch(0, epoch)

    def R_co_at_nth_epoch(self, nth):
        return self.R_co(self.epochs[nth])

    def R_aslip(self, epoch):
        num_epochs = self.num_epochs
        disp = None
        for nth in range(num_epochs):
            if nth == 0:
                continue
            if disp is None:
                disp = self.R_nth_epoch(nth, epoch)
            else:
                arr = self.R_nth_epoch(nth, epoch)
                disp += arr
        return disp

    def R_aslip_at_nth_epoch(self, nth):
        return self.R_aslip(self.epochs[nth])

    # output to displacement object

    def E_cumu_slip_to_disp_obj(self):
        return self._form_disp_obj(self.E_cumu_slip)

    def E_aslip_to_disp_obj(self):
        return self._form_disp_obj(self.R_aslip)

    def R_co_to_disp_obj(self):
        return self._form_disp_obj(self.R_co_at_nth_epoch)

    def R_aslip_to_disp_obj(self):
        return self._form_disp_obj(self.R_aslip_at_nth_epoch)

    def _form_disp_obj(self, func):
        res = []
        for nth, epoch in enumerate(self.epochs):
            res.append(func(nth).reshape([-1, 3]))

        res = np.asarray(res)

        sites = [Site(s) for s in self.file_G0_reader.filter_sites]
        disp = Disp(cumu_disp3d=res,
             epochs=self.epochs,
             sites = sites
        )

        return disp

    def _save_prediction_from_result_file(self, fid):
        fid['result_file/d_pred'] = self.result_file_reader.d_pred
        fid['result_file/sites'] = self.result_file_reader.sites


    # save to a file
    def save(self,fn):
        with h5py.File(fn,'w') as fid:
            print('Ecumu ...')
            disp3d_Ecumu = self.E_cumu_slip_to_disp_obj().cumu3d
            fid['Ecumu'] = disp3d_Ecumu

            print('Rco ...')
            disp3d_Rco = self.R_co_to_disp_obj().cumu3d
            fid['Rco'] = disp3d_Rco

            print('Raslip ...')
            disp3d_Raslip = self.R_aslip_to_disp_obj().cumu3d
            fid['Raslip'] = disp3d_Raslip

            fid['d_added'] = disp3d_Ecumu + disp3d_Rco + disp3d_Raslip

            print('epochs ...')
            fid['epochs'] = self.epochs

            print('sites ...')
            fid['sites'] = [site.id.encode() for site in disp.sites]

            print('Prediction from the result file')
            self._save_prediction_from_result_file(fid)