#
# Concatenation classes
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
import pybamm

import numpy as np
import copy


class Concatenation(pybamm.Symbol):
    """A node in the expression tree representing a concatenation of symbols

    **Extends**: :class:`pybamm.Symbol`

    Parameters
    ----------
    children : iterable of :class:`pybamm.Symbol`
        The symbols to concatenate

    """

    def __init__(self, *children, name=None, check_domain=True):
        if name is None:
            name = "concatenation"
        if check_domain:
            domain = self.get_children_domains(children)
        else:
            domain = []
        super().__init__(name, children, domain=domain)

    def get_children_domains(self, children):
        # combine domains from children
        domain = []
        for child in children:
            child_domain = child.domain
            if set(domain).isdisjoint(child_domain):
                domain += child_domain
            else:
                raise pybamm.DomainError("""domain of children must be disjoint""")

        # ensure domain is sorted according to KNOWN_DOMAINS
        domain_dict = {d: pybamm.KNOWN_DOMAINS.index(d) for d in domain}
        domain = sorted(domain_dict, key=domain_dict.__getitem__)

        return domain

    def _concatenation_evaluate(self, children_eval):
        """ Concatenate the evaluated children. """
        raise NotImplementedError

    def evaluate(self, t=None, y=None, known_evals=None):
        """ See :meth:`pybamm.Symbol.evaluate()`. """
        if known_evals is not None:
            if self.id not in known_evals:
                children_eval = [0] * len(self.children)
                for idx, child in enumerate(self.children):
                    children_eval[idx], known_evals = child.evaluate(t, y, known_evals)
                known_evals[self.id] = self._concatenation_evaluate(children_eval)
            return known_evals[self.id], known_evals
        else:
            children_eval = [0] * len(self.children)
            for idx, child in enumerate(self.children):
                children_eval[idx] = child.evaluate(t, y)
            return self._concatenation_evaluate(children_eval)


class NumpyConcatenation(Concatenation):
    """A node in the expression tree representing a concatenation of equations, when we
    *don't* care about domains. The class :class:`pybamm.DomainConcatenation`, which
    *is* careful about domains and uses broadcasting where appropriate, should be used
    whenever possible instead.

    Upon evaluation, equations are concatenated using numpy concatenation.

    **Extends**: :class:`Concatenation`

    Parameters
    ----------
    children : iterable of :class:`pybamm.Symbol`
        The equations to concatenate

    """

    def __init__(self, *children):
        children = list(children)
        # Turn objects that evaluate to scalars to objects that evaluate to vectors,
        # so that we can concatenate them
        for i, child in enumerate(children):
            if child.evaluates_to_number():
                children[i] = pybamm.NumpyBroadcast(child, [], None)
        super().__init__(*children, name="numpy concatenation", check_domain=False)

    def _concatenation_evaluate(self, children_eval):
        """ See :meth:`Concatenation._concatenation_evaluate()`. """
        if len(children_eval) == 0:
            return np.array([])
        else:
            return np.concatenate([child for child in children_eval])

    def simplify(self):
        """ See :meth:`pybamm.Symbol.simplify()`. """
        children = [child.simplify() for child in self.children]

        new_node = self.__class__(*children)

        return pybamm.simplify_if_constant(new_node)


class DomainConcatenation(Concatenation):
    """A node in the expression tree representing a concatenation of symbols, being
    careful about domains.

    It is assumed that each child has a domain, and the final concatenated vector will
    respect the sizes and ordering of domains established in pybamm.KNOWN_DOMAINS

    **Extends**: :class:`pybamm.Concatenation`

    Parameters
    ----------

    children : iterable of :class:`pybamm.Symbol`
        The symbols to concatenate

    mesh : :class:`pybamm.BaseMesh`
        The underlying mesh for discretisation, used to obtain the number of mesh points
        in each domain.

    copy_this : :class:`pybamm.DomainConcatenation` (optional)
        if provided, this class is initialised by copying everything except the children
        from `copy_this`. `mesh` is not used in this case

    """

    def __init__(self, children, mesh, copy_this=None):
        # Convert any constant symbols in children to a Vector of the right size for
        # concatenation

        children = list(children)

        # Allow the base class to sort the domains into the correct order
        super().__init__(*children, name="domain concatenation")

        if copy_this is None:
            # store mesh
            self._mesh = mesh

            # Check that there is a domain, otherwise the functionality won't work
            # and we should raise a DomainError
            if self.domain == []:
                raise pybamm.DomainError(
                    """
                    domain cannot be empty for a DomainConcatenation.
                    Perhaps the children should have been Broadcasted first?
                    """
                )

            # create dict of domain => slice of final vector
            self._slices = self.create_slices(self)

            # store size of final vector
            self._size = self._slices[self.domain[-1]].stop

            # create disc of domain => slice for each child
            self._children_slices = [
                self.create_slices(child) for child in self.children
            ]
        else:
            self._mesh = copy.copy(copy_this._mesh)
            self._slices = copy.copy(copy_this._slices)
            self._size = copy.copy(copy_this._size)
            self._children_slices = copy.copy(copy_this._children_slices)

    @property
    def mesh(self):
        return self._mesh

    @property
    def size(self):
        return self._size

    @property
    def shape(self):
        return (self.size,)

    def create_slices(self, node):
        slices = {}
        start = 0
        end = 0
        for dom in node.domain:
            prim_pts = self.mesh[dom][0].npts
            second_pts = len(self.mesh[dom])
            end += prim_pts * second_pts
            slices[dom] = slice(start, end)
            start = end
        return slices

    def _concatenation_evaluate(self, children_eval):
        """ See :meth:`Concatenation._concatenation_evaluate()`. """
        # preallocate vector
        vector = np.empty(self._size)

        # loop through domains of children writing subvectors to final vector
        for child_vector, slices in zip(children_eval, self._children_slices):
            for child_dom, child_slice in slices.items():
                vector[self._slices[child_dom]] = child_vector[child_slice]

        return vector

    def simplify(self):
        """ See :meth:`pybamm.Symbol.simplify()`. """
        children = self.children
        # Simplify Concatenation of StateVectors to a single StateVector
        if all([isinstance(x, pybamm.StateVector) for x in children]) and all(
            [
                children[idx].y_slice.stop == children[idx + 1].y_slice.start
                for idx in range(len(children) - 1)
            ]
        ):
            return pybamm.StateVector(
                slice(children[0].y_slice.start, children[-1].y_slice.stop)
            )

        # Otherwise just simplify children and convert to array if constant
        children = [child.simplify() for child in children]

        new_node = self.__class__(children, self.mesh, self)

        # TODO: this should not be needed, but somehow we are still getting domains in
        # the simplified children
        new_node.domain = []

        return pybamm.simplify_if_constant(new_node)
