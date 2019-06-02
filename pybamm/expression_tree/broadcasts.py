#
# Unary operator classes and methods
#
import numbers
import pybamm


class Broadcast(pybamm.SpatialOperator):
    """A node in the expression tree representing a broadcasting operator.
    Broadcasts a child (which *must* have empty domain) to a specified domain. After
    discretisation, this will evaluate to an array of the right shape for the specified
    domain.

    Parameters
    ----------
    child : :class:`Symbol`
        child node
    domain : iterable of string
        the domain to broadcast the child to
    name : str
        name of the node

    **Extends:** :class:`SpatialOperator`
    """

    def __init__(self, child, domain, name=None):
        # Convert child to scalar if it is a number
        if isinstance(child, numbers.Number):
            child = pybamm.Scalar(child)

        # Check domain
        if child.domain not in [[], domain, ["current collector"]]:
            raise pybamm.DomainError(
                """
                Domain of a broadcasted child must be [], ['current collector'],
                or same as 'domain' ('{}'), but is '{}'
                """.format(
                    domain, child.domain
                )
            )
        if name is None:
            name = "broadcast"
        super().__init__(name, child)
        # overwrite child domain ([]) with specified broadcasting domain
        self.domain = domain

    def _unary_simplify(self, child):
        """ See :meth:`pybamm.UnaryOperator.simplify()`. """

        return Broadcast(child, self.domain)

    def _unary_new_copy(self, child):
        """ See :meth:`pybamm.UnaryOperator.simplify()`. """

        return Broadcast(child, self.domain)
