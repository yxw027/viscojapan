import unittest
from os.path import join

from viscojapan.pollitz.pollitz_wrapper import decay
from viscojapan.test_utils import MyTestCase
from viscojapan.utils import delete_if_exists

class Test_Pollitz_decay(MyTestCase):
    def setUp(self):
        self.this_script = __file__
        MyTestCase.setUp(self)

        self.out_file = join(self.outs_dir, 'decay.out')
        delete_if_exists(self.out_file)

    def test(self):
        cmd = decay(
            earth_model = join(self.share_dir,'earth.model'),
            decay_out = self.out_file,
            l_min = 1,
            l_max = 3,

            if_skip_on_existing_output = True,
            stdout = None,
            stderr = None)
        cmd()

if __name__=='__main__':
    unittest.main()
    



