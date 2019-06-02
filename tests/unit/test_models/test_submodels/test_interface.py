import pybamm
import unittest


class TestInterface(unittest.TestCase):
    def test_domain_failures(self):
        model = pybamm.interface.InterfacialCurrent(None)

        with self.assertRaises(pybamm.DomainError):
            model.get_homogeneous_interfacial_current(None, "not a domain")

        with self.assertRaises(pybamm.DomainError):
            model.get_butler_volmer(None, None, "not a domain")

        with self.assertRaises(pybamm.DomainError):
            model.get_inverse_butler_volmer(None, None, "not a domain")

        c = pybamm.Variable("c", "not a domain")
        lead_acid_model = pybamm.interface.LeadAcidReaction(None)
        with self.assertRaises(pybamm.DomainError):
            lead_acid_model.get_exchange_current_densities(c, "not a domain")

        lithium_ion_model = pybamm.interface.LithiumIonReaction(None)
        with self.assertRaises(pybamm.DomainError):
            lithium_ion_model.get_exchange_current_densities(c, "not a domain")


if __name__ == "__main__":
    print("Add -v for more debug output")
    import sys

    if "-v" in sys.argv:
        debug = True
    unittest.main()
