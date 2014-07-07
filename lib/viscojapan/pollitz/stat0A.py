import sys
##from os.path import exists,join,basename, dirname
##from os import makedirs
##from subprocess import Popen, check_output
##import sys
from tempfile import TemporaryFile
##from time import time
##from shutil import copyfile, rmtree

from .pollitz_wrapper import PollitzWrapper

class stat0A(PollitzWrapper):
    def __init__(self,
                 earth_model_stat = None,
                 stat0_out = None,
                 l_min = None,
                 l_max = None,
                 fault_bottom_depth = None,
                 fault_top_depth = None,
                 obs_dep = 0.,
                 output_dir = None,
                 if_skip_on_existing_output = True,
                 stdout = sys.stdout,
                 stderr = sys.stderr,
                 ):

        self.l_min = l_min
        self.l_max = l_max
        self.fault_bottom_depth = fault_bottom_depth
        self.fault_top_depth = fault_top_depth
        self.obs_dep = obs_dep
        
        super().__init__(
            input_files = {'earth.model_stat':earth_model_stat},
            output_files = {'stat0.out':stat0_out},
            if_skip_on_existing_output = if_skip_on_existing_output,
            stdout = stdout,
            stderr = stderr,
            )
        self._cmd = 'stat0A'

    def gen_stdin(self):
        stdin=TemporaryFile('r+')
        stdin.write('%d  %d\n'%(self.l_min, self.l_max))
        stdin.write('%d  %d\n'%(self.fault_bottom_depth, self.fault_top_depth))
        stdin.write('%d\n'%self.obs_dep)
        stdin.seek(0)
        return stdin
        
        
