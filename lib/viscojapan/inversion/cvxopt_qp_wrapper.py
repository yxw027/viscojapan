import numpy as np
from cvxopt import matrix, solvers

from ..utils import assert_col_vec_and_get_nrow,\
     assert_square_array_and_get_nrow

class CvxoptQpWrapper(object):
    def __init__(self,*,
                 P,
                 q
                 ):
        self.P = P
        self.q = q
        
        self._check_input()

    def _check_input(self):
        nrow_P = assert_square_array_and_get_nrow(self.P)
        nrow_q = assert_col_vec_and_get_nrow(self.q)
        assert  nrow_P == nrow_q
        self.nrow_P = nrow_P

    def invert(self, nonnegative=True):
        # non-negative constraint
        if nonnegative:
            GG = -1.0 * np.identity(self.nrow_P, dtype='float')
            h = np.zeros((self.nrow_P, 1), dtype='float')
            self.solution = solvers.qp(matrix(self.P),matrix(self.q),
                                       matrix(GG),matrix(h))
        else:
            self.solution = solvers.qp(matrix(self.P),matrix(self.q))

    @classmethod
    def create_from_inversion_parameters_set(cls, inv_par_set):
        P, q = inv_par_set.gen_inputs_for_cvxopt_qp()
        return cls(P=P, q=q)
        