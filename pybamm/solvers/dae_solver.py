#
# Base solver class
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import pybamm
import numpy as np
from scipy import optimize


class DaeSolver(pybamm.BaseSolver):
    """Solve a discretised model.

    Parameters
    ----------
    tolerance : float, optional
        The tolerance for the solver (default is 1e-8).
    """

    def __init__(self, tol=1e-8):
        super().__init__(tol)

    def solve(self, model, t_eval):
        """Calculate the solution of the model at specified times.

        Parameters
        ----------
        model : :class:`pybamm.BaseModel`
            The model whose solution to calculate. Must have attributes rhs and
            initial_conditions
        t_eval : numeric type
            The times at which to compute the solution

        """

        # create simplified rhs algebraic and event expressions
        concatenated_rhs = model.concatenated_rhs.simplify()
        concatenated_algebraic = model.concatenated_algebraic.simplify()
        events = [event.simplify() for event in model.events]

        def residuals(t, y, ydot):
            rhs_eval, known_evals = concatenated_rhs.evaluate(t, y, known_evals={})
            # reuse known_evals
            concat_evals = concatenated_algebraic.evaluate(
                t, y, known_evals=known_evals
            )[0]
            return np.concatenate((rhs_eval - ydot[: rhs_eval.shape[0]], concat_evals))

        def rhs(t, y):
            return concatenated_rhs.evaluate(t, y, known_evals={})[0]

        def algebraic(t, y):
            return concatenated_algebraic.evaluate(t, y, known_evals={})[0]

        # Create event-dependent function to evaluate events
        def event_fun(event):
            def eval_event(t, y):
                return event.evaluate(t, y)

            return eval_event

        events = [event_fun(event) for event in events]

        y0 = self.calculate_consistent_initial_conditions(
            rhs, algebraic, model.concatenated_initial_conditions
        )

        self.t, self.y = self.integrate(
            residuals,
            y0,
            t_eval,
            events=events,
            mass_matrix=model.mass_matrix.entries,
            jacobian=model.jacobian,
        )

    def calculate_consistent_initial_conditions(self, rhs, algebraic, y0_guess):
        """
        Calculate consistent initial conditions for the algebraic equations through
        root-finding

        Parameters
        ----------
        rhs : method
            Function that takes in t and y and returns the value of the differential
            equations
        algebraic : method
            Function that takes in t and y and returns the value of the algebraic
            equations
        y0_guess : array-like
            Array of the user's guess for the initial conditions, used to initialise
            the root finding algorithm

        Returns
        -------
        y0_consistent : array-like, same shape as y0_guess
            Initial conditions that are consistent with the algebraic equations (roots
            of the algebraic equations)
        """
        # Split y0_guess into differential and algebraic
        len_rhs = rhs(0, y0_guess).shape[0]
        y0_diff, y0_alg_guess = np.split(y0_guess, [len_rhs])

        def root_fun(y0_alg):
            "Evaluates algebraic using y0_diff (fixed) and y0_alg (changed by algo)"
            y0 = np.concatenate([y0_diff, y0_alg])
            return algebraic(0, y0)

        # Find the values of y0_alg that are roots of the algebraic equations
        sol = optimize.root(root_fun, y0_alg_guess, method="hybr")
        # Return full set of consistent initial conditions (y0_diff unchanged)
        y0_consistent = np.concatenate([y0_diff, sol.x])

        return y0_consistent

    def integrate(
        self, residuals, y0, t_eval, events=None, mass_matrix=None, jacobian=None
    ):
        """
        Solve a DAE model defined by residuals with initial conditions y0.

        Parameters
        ----------
        residuals : method
            A function that takes in t, y and ydot and returns the residuals of the
            equations
        y0 : numeric type
            The initial conditions
        t_eval : numeric type
            The times at which to compute the solution
        events : method, optional
            A function that takes in t and y and returns conditions for the solver to
            stop
        mass_matrix : array_like, optional
            The (sparse) mass matrix for the chosen spatial method.
        jacobian : method, optional
            A function that takes in t, y and ydot and returns the Jacobian
        """
        raise NotImplementedError
