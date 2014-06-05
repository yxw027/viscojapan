from numpy import asarray

from .slip import EpochalIncrSlip, EpochalSlip
from .ed_sites_filtered import EDSitesFiltered
from .epochal_data import EpochalData

class PostInversionProcessing(object):
    def __init__(self, inversion):
        self.inversion = inversion
        
    def init(self):
        assert hasattr(self.inversion, 'solution'), "Have you run the program?"
        self.m = asarray(self.inversion.solution['x'],float)
        
        self.num_of_nlin_pars = len(self.formulate_occam.non_lin_par_vals)
        
        self.incr_slip_arr = self.m[0:-self.num_of_nlin_pars]
        self.nlin_par_vals = self.m[-self.num_of_nlin_pars:]
        
        for pn, val in zip(self.formulate_occam.nlin_par_names,
                           self.formulate_occam.nlin_par_vals):
            setattr(self,pn,val)

    def gen_inverted_incr_slip_file(self, incr_slip_file, info_dic={}):
        incr_slip = EpochalIncrSlip(incr_slip_file)
        for nth, epoch in enumerate(self.epochs):
            incr_slip.set_epoch_value(epoch,self.incr_slip_arr[
                nth*self.num_of_subfaults:(nth+1)*self.num_of_subfaults, 0])

        incr_slip.set_info('incr_slip_arr', self.incr_slip_arr)
        incr_slip.set_info('num_of_subfaults', self.num_of_subfaults)
        
        for par in self.nlin_par_names:
            incr_slip.set_info(par, getattr(self,par))
        incr_slip.set_info_dic(info_dic)

    def gen_inverted_slip_file(self, slip_file):
        slip = EpochalSlip(slip_file)
        for nth, epoch in enumerate(self.epochs):
            if nth == 0:
                val0 = self.incr_slip_arr[nth*self.num_of_subfaults:
                                          (nth+1)*self.num_of_subfaults,0]
            else:
                val = self.incr_slip_arr[nth*self.num_of_subfaults:
                                         (nth+1)*self.num_of_subfaults,0]
                val0 += val
            slip.set_epoch_value(epoch,val0)

    def get_predicated_obs(self):
        G1 = self.G[:,0:-self.num_of_nlin_pars]
        G2 = self.G[-self.num_of_nlin_pars:]

        res = dot(G1, self.incr_slip_arr)
        delta = self.nlin_par_vals - self.nlin_par_vals0
        res += dot(G2, delta)

        pred =  EpochalData(self.file_pred)

        
        for nth, epoch in enumerate(epochs):
            val = res[nth*self.num_obs : (nth+1)*self.num_obs]
            pred.set_epochal_value(epoch,nth)
            
            
        