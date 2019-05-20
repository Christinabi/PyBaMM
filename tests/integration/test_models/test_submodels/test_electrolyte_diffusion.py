#
# Tests for the electrolyte submodels
#
import pybamm
import tests

import unittest


class TestStefanMaxwellDiffusion(unittest.TestCase):
    def test_make_tree(self):
        # Parameter values
        param = pybamm.standard_parameters_lithium_ion

        # Variables and parameters
        c_e = pybamm.standard_variables.c_e
        onen = pybamm.Broadcast(1, ["negative electrode"])
        onep = pybamm.Broadcast(1, ["positive electrode"])
        reactions = {
            "main": {"neg": {"s_plus": 1, "aj": onen}, "pos": {"s_plus": 1, "aj": onep}}
        }
        model = pybamm.electrolyte_diffusion.StefanMaxwell(param)
        model.set_differential_system(c_e, reactions)

    def test_basic_processing(self):
        # Parameter values
        param = pybamm.standard_parameters_lithium_ion

        # Variables and parameters
        c_e = pybamm.standard_variables.c_e
        onen = pybamm.Broadcast(1, ["negative electrode"])
        onep = pybamm.Broadcast(1, ["positive electrode"])
        reactions = {
            "main": {"neg": {"s_plus": 1, "aj": onen}, "pos": {"s_plus": 1, "aj": onep}}
        }
        model = pybamm.electrolyte_diffusion.StefanMaxwell(param)
        model.set_differential_system(c_e, reactions)

        modeltest = tests.StandardModelTest(model)
        # Either
        # 1. run the tests individually (can pass options to individual tests)
        # modeltest.test_processing_parameters()
        # modeltest.test_processing_disc()
        # modeltest.test_solving()

        # Or
        # 2. run all the tests in one go
        modeltest.test_all()

    def test_basic_processing_different_bcs(self):
        "Change the boundary conditions and test"
        # Parameter values
        param = pybamm.standard_parameters_lithium_ion

        # Variables and parameters
        c_e = pybamm.standard_variables.c_e
        onen = pybamm.Broadcast(1, ["negative electrode"])
        onep = pybamm.Broadcast(1, ["positive electrode"])
        reactions = {
            "main": {"neg": {"s_plus": 1, "aj": onen}, "pos": {"s_plus": 1, "aj": onep}}
        }
        model = pybamm.electrolyte_diffusion.StefanMaxwell(param)
        model.set_differential_system(c_e, reactions)

        # Dirichlet conditions (don't clash with events)
        model.boundary_conditions = {
            c_e: {"left": (0.1, "Dirichlet"), "right": (0.1, "Dirichlet")}
        }
        modeltest = tests.StandardModelTest(model)
        modeltest.test_all()

        # Dirichlet and Neumann conditions
        model2 = pybamm.electrolyte_diffusion.StefanMaxwell(param)
        model2.set_differential_system(c_e, reactions)
        model2.boundary_conditions = {
            c_e: {"left": (0, "Dirichlet"), "right": (0, "Neumann")}
        }
        modeltest2 = tests.StandardModelTest(model2)
        modeltest2.test_all()

        model3 = pybamm.electrolyte_diffusion.StefanMaxwell(param)
        model3.set_differential_system(c_e, reactions)
        model3.boundary_conditions = {
            c_e: {"left": (0, "Neumann"), "right": (0, "Dirichlet")}
        }
        modeltest3 = tests.StandardModelTest(model3)
        modeltest3.test_all()


if __name__ == "__main__":
    print("Add -v for more debug output")
    import sys

    if "-v" in sys.argv:
        debug = True
    unittest.main()
