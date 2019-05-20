#
# Matrix class
#
import pybamm

from scipy.sparse import issparse


class Matrix(pybamm.Array):
    """node in the expression tree that holds a matrix type (e.g. :class:`numpy.array`)

    **Extends:** :class:`Array`

    Parameters
    ----------

    entries : numpy.array
        the array associated with the node
    name : str, optional
        the name of the node

    """

    def __init__(self, entries, name=None, domain=[], entries_string=None):
        if name is None:
            name = "Matrix {!s}".format(entries.shape)
            if issparse(entries):
                name = "Sparse " + name
        super().__init__(entries, name, domain, entries_string)
