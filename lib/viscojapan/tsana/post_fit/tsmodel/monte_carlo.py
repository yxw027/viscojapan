from os import mkdir, listdir
from os.path import join, exists
import pickle

from copy import deepcopy

from numpy import mean, std

from scipy.stats import norm
from tsana.stations import CStation

def mc_test(cfs, n = 1000, opath = 'mc/', verbose = True):
    cfs0 = deepcopy(cfs)

    if not exists(opath):
        mkdir(opath)

    out = dict()
    for cf in cfs0.cfs:
        out['%s.%s'%(cf.SITE,cf.CMPT)] = cf.func
    fid = file(join(opath, 'mc_0.func'),'w')
    pickle.dump(out,fid)
    fid.close()        

    for m in range(1,n+1):
        print("Monte Carlo %d:"%m)
        for cf in cfs0.cfs:
            s = CStation(cf.SITE)
            cmpt = cf.CMPT

            ts = s.ts(cmpt)
            sz = len(ts)

            cf.y0 = norm.rvs(loc = ts, scale = s.ts_sd(cmpt), size = sz)
            cf.data_mask()
        cfs0.go(verbose)
        out = dict()
        for cf in cfs0.cfs:
            out['%s.%s'%(cf.SITE,cf.CMPT)] = cf.func
        if not exists(opath):
            mkdir(opath)
        fid = file(join(opath, 'mc_%d.func'%m),'w')
        pickle.dump(out,fid)
        fid.close()
        
def out_stat(stat,cmpt,pn,ftag = [], datapath = 'mc'):
    if not exists(datapath):
        raise ValueError("Output dir doesn't exist!")

    n = 1
    vs = []
    while(exists(join(datapath,'mc_%d.func'%n))):
        fid = file(join(datapath,'mc_%d.func'%n))
        fcs = pickle.load(fid)
        fid.close()
        vs.append(fcs["%s.%s"%(stat,cmpt)].getp(pn,ftag))
        n += 1
    return mean(vs),std(vs),n

def out_stat2file(datapath = 'mc',ofile = './out_stat'):
    if not exists(datapath):
        raise ValueError("Output dir doesn't exist!")

    fid = file(join(datapath,'mc_0.func'))
    fcs = pickle.load(fid)
    fid.close()

    fid = file(ofile,'w')
    fid.write('# number of test: %d'%n)
    fid.write('# individual pars\n')
    fid.write('# SITE.CMPT %5s %5s %15s %15s %15s\n\n'%('tag','par','estimated','mean','std'))
    for keys, fs in fcs.items():
        for f in fs.subfcs:
            for p in f.ipns:
                ave, st, n =  out_stat(keys[0:4],keys[5:],p,f.tag())
                fid.write('%s %10s %5s %15.3g %15.3g %15.3g\n'%(keys, f.tag(), p, getattr(f,p),ave, st))
    
    fid.write('\n# common pars\n')
    fid.write('# %8s %5s %15s %15s %15s\n'%('tag','par','estimated','mean','std'))
    fs = fcs[keys]
    for f in fs.subfcs:
        for p in f.cpns:
            ave, st, n =  out_stat(keys[0:4],keys[5:],p,f.tag())
            fid.write('%010s %5s %15.3g %15.3g %15.3g\n'%(f.tag(), p, getattr(f,p),ave, st))
    fid.close()


    
