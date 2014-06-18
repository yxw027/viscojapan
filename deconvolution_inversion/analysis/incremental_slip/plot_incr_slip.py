from pylab import *

from viscojapan.plot_utils import Map, append_title
from viscojapan.epochal_data import EpochalIncrSlip
from days import days as epochs

def plot_incr_slip(ano,epoch):
    slip = EpochalIncrSlip('../../outs/slip_%02d.h5'%ano)
    epochs = slip.get_epochs()

    #alpha = slip.get_info('alpha')

    s = slip.get_epoch_value(epoch)

    m = Map()
    m.region_code = 'near'
    m.init()
    m.plot_fslip(s)
    
    #append_title(', ano = %d, alpha=%.3f, epoch=%d'%(ano,alpha,epoch))

ano = 0

for epoch in epochs:
    plot_incr_slip(ano, epoch)
    savefig('incr_slip_%04d.png'%epoch)
    close()
