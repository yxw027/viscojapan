from os.path import join

from pylab import *
from mpl_toolkits.basemap import Basemap
from h5py import File

from ..utils import get_this_script_dir
from ..fault.mo import ComputeMoment
from ..epochal_data import \
     EpochalIncrSlip, EpochalDisplacement, EpochalSlip, EpochalData

this_test_path = get_this_script_dir(__file__)

def get_pos_dic():
    ''' Return a dictionary of position of all stations.
'''
    tp=loadtxt(join(this_test_path, 'sites_with_seafloor'),'4a, 2f')
    return {ii[0]:ii[1] for ii in tp}

def get_pos(sites):
    lons=[]
    lats=[]
    pos=get_pos_dic()
    for site in sites:
        tp=pos[site]
        lons.append(tp[0])
        lats.append(tp[1])
    return lons,lats

_fault_file='/home/zy/workspace/visinv2/flt_250/fault.h5'

def append_title(string):
    ax=gca()
    title = ax.get_title()
    ax.set_title(title+string)
    
class Map(Basemap):
    def __init__(self):
        self.region_box=(136,34,146,42)
        self.region_code=None
        self.x_interval=2.
        self.y_interval=2.        
        self.fault_model_file = _fault_file
        self.if_init=False

    def init(self):
        if self.region_code is not None:
            if self.region_code=='I':
                self.region_box=(128,30,132.5,34.5)
            elif self.region_code=='A':
                self.region_box=(136.2,35.8,142.6,38.2)
            elif self.region_code=='H':
                self.region_box=(131,33,137,36.5)
                self.region_box=(140,41.8,146.2,45.8)
            elif self.region_code=='near':
                self.region_box=(136,34,146,42)
            elif self.region_code=='all':
                self.region_box=(136,34,146,42)
            else:
                raise ValueError()
        
                
        self.lon_0=(self.region_box[0]+self.region_box[2])/2.
        self.lat_0=(self.region_box[1]+self.region_box[3])/2.
        super().__init__(llcrnrlon=self.region_box[0],llcrnrlat=self.region_box[1],
                         urcrnrlon=self.region_box[2],urcrnrlat=self.region_box[3],
                         resolution='l',area_thresh=100.,projection='eqdc',
                         lon_0=self.lon_0,lat_0=self.lat_0,
                         lat_1=self.lat_0-5,lat_2=self.lat_0+5,
                         celestial=False)

        self.drawcoastlines(color='green',zorder=-1)

        # draw parallels and meridians.
        self.drawparallels(arange(-80.,81.,self.y_interval),zorder=-1,labels=[1,1,0,0])
        self.drawmeridians(arange(-180.,181.,self.x_interval),zorder=-1,labels=[0,0,0,1])
        self.drawmapboundary(color='k')

        self.if_init=True

        return self

    def plot_disp(self,d,sites,
                  X=0.1,Y=0.1,U=1.,label='1m',
                  color='black',scale=None):
        ''' Plot displacment
'''
        if not self.if_init:
            self.init()
            
        lons,lats=get_pos(sites)
        es=d[0::3]
        ns=d[1::3]
        us=d[2::3]
        Qu=self.quiver(lons,lats,es,ns,
                    color=color,scale=scale,edgecolor=color,latlon=True)
        qk=quiverkey(Qu,X,Y,U,label,
                            labelpos='N')

    def plot_fslip(self,m,cmap=None,clim=None):
        '''
'''
        if not self.if_init:
            self.init()
            
        with File(self.fault_model_file) as fid:
            LLons=fid['grids/LLons'][...]
            LLats=fid['grids/LLats'][...]

        mm=m.reshape([-1,25])
        self.pcolor(LLons,LLats,mm,latlon=True,cmap=cmap)        
        cb=colorbar()
        plt.clim(clim)
        cb.set_label('slip(m)')

        com_mo = ComputeMoment()
        com_mo.fault_model_file = self.fault_model_file
        
        mo, mw = com_mo.moment(m)
        
        title('Mo=%.3g,Mw=%.2f'%(mo,mw))
        

    def plot_fault(self,fno=None,ms=15):
        if not self.if_init:
            self.init()
            
        with File(self.fault_model_file) as fid:
            LLons=fid['grids/LLons'][...]
            LLats=fid['grids/LLats'][...]
        assert ms<250 and ms>=0, "Fault No. out of range."
            
        self.plot(LLons,LLats,color='gray',latlon=True)
        self.plot(ascontiguousarray(LLons.T),
                  ascontiguousarray(LLats.T),
                  color='gray',latlon=True)
        if fno is not None:
            xpt,ypt=self(LLons,LLats)
            xpt1=xpt[0:-1,0:-1]
            ypt1=ypt[0:-1,0:-1]

            xpt2=xpt[1:,1:]
            ypt2=ypt[1:,1:]

            x0=(xpt1.flatten()[fno]+xpt2.flatten()[fno])/2.
            y0=(ypt1.flatten()[fno]+ypt2.flatten()[fno])/2.

            
            self.plot(x0,y0,marker='*',color='red',ms=ms)

    def plot_incr_slip_file(self, f_slip, epoch):
        slip_obj = EpochalIncrSlip(f_slip)
        slip = slip_obj(epoch)

        self.plot_fslip(slip)

    def plot_slip_file(self, f_slip, epoch):
        slip_obj = EpochalSlip(f_slip)
        slip = slip_obj(epoch)

        self.plot_fslip(slip)

    def plot_disp_file(self, f_disp, epoch):
        disp_obj = EpochalData(f_disp)
        disp = disp_obj(epoch)
        sites = disp_obj.get_info('sites')
        self.plot_disp(disp, sites)


    


    