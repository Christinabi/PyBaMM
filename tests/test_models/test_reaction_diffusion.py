#
# Tests for the Reaction diffusion model
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
import pybamm
import tests

import copy
import numpy as np
import unittest


class TestReactionDiffusionModel(unittest.TestCase):
    @unittest.skip("")
    def test_basic_processing(self):
        model = pybamm.ReactionDiffusionModel()

        modeltest = tests.StandardModelTest(model)
        modeltest.test_all()

    @unittest.skip("")
    def test_optimisations(self):
        model = pybamm.ReactionDiffusionModel()
        optimtest = tests.OptimisationsTest(model)

        original = optimtest.evaluate_model()
        simplified = optimtest.evaluate_model(simplify=True)
        using_known_evals = optimtest.evaluate_model(use_known_evals=True)
        simp_and_known = optimtest.evaluate_model(simplify=True, use_known_evals=True)
        np.testing.assert_array_almost_equal(original, simplified)
        np.testing.assert_array_almost_equal(original, using_known_evals)
        np.testing.assert_array_almost_equal(original, simp_and_known)

    @unittest.skip("")
    def test_convergence(self):
        # Convergence of c at x=0.5
        model = pybamm.ReactionDiffusionModel()
        # Process model and geometry
        param = model.default_parameter_values
        param.process_model(model)
        geometry = model.default_geometry
        param.process_geometry(geometry)
        # Set up solver
        t_eval = np.linspace(0, 0.01, 5)
        solver = model.default_solver

        # Function for convergence testing
        def get_c_at_x(n):
            model_copy = copy.deepcopy(model)
            # Set up discretisation
            var = pybamm.standard_spatial_vars
            submesh_pts = {var.x_n: n, var.x_s: n, var.x_p: n, var.r_n: 1, var.r_p: 1}
            mesh = pybamm.Mesh(geometry, model_copy.default_submesh_types, submesh_pts)
            disc = pybamm.Discretisation(mesh, model_copy.default_spatial_methods)

            # Discretise and solve
            disc.process_model(model_copy)
            solver.solve(model_copy, t_eval)
            t, y = solver.t, solver.y
            conc = pybamm.ProcessedVariable(
                model_copy.variables["Electrolyte concentration"], t, y, mesh=disc.mesh
            )

            # Calculate concentration at ln
            ln = mesh["negative electrode"][0].nodes[-1]
            return conc(t, ln)

        # Get concentrations
        ns = 100 * (2 ** np.arange(4))
        concs = [get_c_at_x(int(n)) for n in ns]

        # Get errors
        norm = np.linalg.norm
        errs = np.array(
            [norm(concs[i + 1] - concs[i]) / norm(concs[i]) for i in range(len(ns) - 1)]
        )
        # Get rates: expect h**2 convergence, check for h convergence only
        rates = np.log2(errs[:-1] / errs[1:])
        np.testing.assert_array_less(0.99 * np.ones_like(rates), rates)

    def test_manufactured_solution(self):
        model = pybamm.ReactionDiffusionModel()
        errs = tests.get_manufactured_solution_errors(model)
        rates = np.log2(errs[:-1] / errs[1:])
        np.testing.assert_array_less(1.99 * np.ones_like(rates), rates)


if __name__ == "__main__":
    print("Add -v for more debug output")
    import sys

    if "-v" in sys.argv:
        debug = True
    unittest.main()
