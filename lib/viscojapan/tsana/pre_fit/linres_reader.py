''' A class is defined in this module to read linear residual time
series generated by preseismic time series modeling. '''

from os.path import join

from numpy import loadtxt

class LinResReader(object):
    def __init__(self,site,cmpt):
        self.dir_linres = '../pre_fit/linres/'
        self.site=site
        self.cmpt=cmpt

        # loading the data
        self._data=loadtxt(join(self.dir_linres,'%s.%s.lres'%(site,cmpt)))

    @property
    def t(self):
        ''' time
'''
        return self._data[:,0]

    @property
    def y(self):
        '''Linear residual'''
        return self._data[:,2]

    @property
    def ysd(self):
        '''Standard deviation of linear residual'''
        return self._data[:,3]
    
    
if __name__=='__main__':
    site='J550'
    cmpt='e'
    reader=LinResReader(site,cmpt)
