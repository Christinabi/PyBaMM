#
# Tests for the Concatenation class and subclasses
#
import pybamm
from tests import get_discretisation_for_testing
import numpy as np
import unittest


class TestConcatenations(unittest.TestCase):
    def test_base_concatenation(self):
        a = pybamm.Symbol("a")
        b = pybamm.Symbol("b")
        c = pybamm.Symbol("c")
        conc = pybamm.Concatenation(a, b, c)
        self.assertEqual(conc.name, "concatenation")
        self.assertIsInstance(conc.children[0], pybamm.Symbol)
        self.assertEqual(conc.children[0].name, "a")
        self.assertEqual(conc.children[1].name, "b")
        self.assertEqual(conc.children[2].name, "c")
        d = pybamm.Scalar(2)
        e = pybamm.Scalar(1)
        f = pybamm.Scalar(3)
        conc2 = pybamm.Concatenation(d, e, f)
        with self.assertRaises(NotImplementedError):
            conc2.evaluate()

    def test_concatenation_domains(self):
        a = pybamm.Symbol("a", domain=["negative electrode"])
        b = pybamm.Symbol("b", domain=["separator", "positive electrode"])
        c = pybamm.Symbol("c", domain=["test"])
        conc = pybamm.Concatenation(a, b, c)
        self.assertEqual(
            conc.domain,
            ["negative electrode", "separator", "positive electrode", "test"],
        )

        # Can't concatenate nodes with overlapping domains
        d = pybamm.Symbol("d", domain=["separator"])
        with self.assertRaises(pybamm.DomainError):
            pybamm.Concatenation(a, b, d)

        # ensure concatenated domains are sorted correctly
        conc = pybamm.Concatenation(c, a, b)
        self.assertEqual(
            conc.domain,
            ["negative electrode", "separator", "positive electrode", "test"],
        )

    def test_numpy_concatenation_vectors(self):
        # with entries
        y = np.linspace(0, 1, 15)
        a = pybamm.Vector(y[:5])
        b = pybamm.Vector(y[5:9])
        c = pybamm.Vector(y[9:])
        conc = pybamm.NumpyConcatenation(a, b, c)
        np.testing.assert_array_equal(conc.evaluate(None, y), y)
        # with y_slice
        a = pybamm.StateVector(slice(0, 10))
        b = pybamm.StateVector(slice(10, 15))
        c = pybamm.StateVector(slice(15, 23))
        conc = pybamm.NumpyConcatenation(a, b, c)
        y = np.linspace(0, 1, 23)
        np.testing.assert_array_equal(conc.evaluate(None, y), y)

    def test_numpy_concatenation_vector_scalar(self):
        # with entries
        y = np.linspace(0, 1, 10)
        a = pybamm.Vector(y)
        b = pybamm.Scalar(16)
        c = pybamm.Scalar(3)
        conc = pybamm.NumpyConcatenation(a, b, c)
        np.testing.assert_array_equal(
            conc.evaluate(None, y), np.concatenate([y, np.array([16]), np.array([3])])
        )

        # with y_slice
        a = pybamm.StateVector(slice(0, 10))
        conc = pybamm.NumpyConcatenation(a, b, c)
        np.testing.assert_array_equal(
            conc.evaluate(None, y), np.concatenate([y, np.array([16]), np.array([3])])
        )

        # with time
        b = pybamm.t
        conc = pybamm.NumpyConcatenation(a, b, c)
        np.testing.assert_array_equal(
            conc.evaluate(16, y), np.concatenate([y, np.array([16]), np.array([3])])
        )

    def test_numpy_domain_concatenation(self):
        # create discretisation
        disc = get_discretisation_for_testing()
        mesh = disc.mesh

        a_dom = ["negative electrode"]
        b_dom = ["positive electrode"]
        a = pybamm.NumpyBroadcast(pybamm.Scalar(2), a_dom, mesh)
        b = pybamm.Vector(np.ones_like(mesh[b_dom[0]][0].nodes), domain=b_dom)

        # concatenate them the "wrong" way round to check they get reordered correctly
        conc = pybamm.DomainConcatenation([b, a], mesh)
        np.testing.assert_array_equal(
            conc.evaluate(),
            np.concatenate(
                [np.full(mesh[a_dom[0]][0].npts, 2), np.full(mesh[b_dom[0]][0].npts, 1)]
            ),
        )
        # test size and shape
        self.assertEqual(conc.size, mesh[a_dom[0]][0].npts + mesh[b_dom[0]][0].npts)
        self.assertEqual(conc.shape, (mesh[a_dom[0]][0].npts + mesh[b_dom[0]][0].npts,))

        # check the reordering in case a child vector has to be split up
        a_dom = ["separator"]
        b_dom = ["negative electrode", "positive electrode"]
        a = pybamm.NumpyBroadcast(pybamm.Scalar(2, domain=a_dom), a_dom, mesh)
        b = pybamm.Vector(
            np.concatenate(
                [np.full(mesh[b_dom[0]][0].npts, 1), np.full(mesh[b_dom[1]][0].npts, 3)]
            ),
            domain=b_dom,
        )

        conc = pybamm.DomainConcatenation([a, b], mesh)
        np.testing.assert_array_equal(
            conc.evaluate(),
            np.concatenate(
                [
                    np.full(mesh[b_dom[0]][0].npts, 1),
                    np.full(mesh[a_dom[0]][0].npts, 2),
                    np.full(mesh[b_dom[1]][0].npts, 3),
                ]
            ),
        )
        # test size and shape
        self.assertEqual(
            conc.size,
            mesh[b_dom[0]][0].npts + mesh[a_dom[0]][0].npts + mesh[b_dom[1]][0].npts,
        )
        self.assertEqual(
            conc.shape,
            (mesh[b_dom[0]][0].npts + mesh[a_dom[0]][0].npts + mesh[b_dom[1]][0].npts,),
        )

    def test_domain_concatenation_simplify(self):
        # create discretisation
        disc = get_discretisation_for_testing()
        mesh = disc.mesh

        a_dom = ["negative electrode"]
        b_dom = ["positive electrode"]
        a = pybamm.NumpyBroadcast(pybamm.Scalar(2), a_dom, mesh)
        b = pybamm.Vector(np.ones_like(mesh[b_dom[0]][0].nodes), domain=b_dom)

        conc = pybamm.DomainConcatenation([a, b], mesh)
        conc_simp = conc.simplify()

        # should be simplified to a vector
        self.assertIsInstance(conc_simp, pybamm.Vector)
        np.testing.assert_array_equal(
            conc_simp.evaluate(),
            np.concatenate(
                [np.full(mesh[a_dom[0]][0].npts, 2), np.full(mesh[b_dom[0]][0].npts, 1)]
            ),
        )

    def test_concatenation_orphans(self):
        a = pybamm.Variable("a")
        b = pybamm.Variable("b")
        c = pybamm.Variable("c")
        conc = pybamm.Concatenation(a, b, c)
        a_new, b_new, c_new = conc.orphans

        # We should be able to manipulate the children without TreeErrors
        self.assertIsInstance(2 * a_new, pybamm.Multiplication)
        self.assertIsInstance(3 + b_new, pybamm.Addition)
        self.assertIsInstance(4 - c_new, pybamm.Subtraction)

        # ids should stay the same
        self.assertEqual(a.id, a_new.id)
        self.assertEqual(b.id, b_new.id)
        self.assertEqual(c.id, c_new.id)
        self.assertEqual(conc.id, pybamm.Concatenation(a_new, b_new, c_new).id)

    def test_broadcast_and_concatenate(self):
        # create discretisation
        disc = get_discretisation_for_testing()
        mesh = disc.mesh

        # Piecewise constant scalars
        a = pybamm.Broadcast(1, domain=["negative electrode"])
        b = pybamm.Broadcast(2, domain=["separator"])
        c = pybamm.Broadcast(3, domain=["positive electrode"])
        conc = pybamm.Concatenation(a, b, c)

        self.assertEqual(
            conc.domain, ["negative electrode", "separator", "positive electrode"]
        )
        self.assertEqual(conc.children[0].domain, ["negative electrode"])
        self.assertEqual(conc.children[1].domain, ["separator"])
        self.assertEqual(conc.children[2].domain, ["positive electrode"])
        processed_conc = disc.process_symbol(conc)
        np.testing.assert_array_equal(
            processed_conc.evaluate(),
            np.concatenate(
                [
                    np.ones(mesh["negative electrode"][0].npts),
                    2 * np.ones(mesh["separator"][0].npts),
                    3 * np.ones(mesh["positive electrode"][0].npts),
                ]
            ),
        )

        # Piecewise constant functions of time
        a_t = pybamm.Broadcast(pybamm.t, domain=["negative electrode"])
        b_t = pybamm.Broadcast(2 * pybamm.t, domain=["separator"])
        c_t = pybamm.Broadcast(3 * pybamm.t, domain=["positive electrode"])
        conc = pybamm.Concatenation(a_t, b_t, c_t)

        self.assertEqual(
            conc.domain, ["negative electrode", "separator", "positive electrode"]
        )
        self.assertEqual(conc.children[0].domain, ["negative electrode"])
        self.assertEqual(conc.children[1].domain, ["separator"])
        self.assertEqual(conc.children[2].domain, ["positive electrode"])

        processed_conc = disc.process_symbol(conc)
        np.testing.assert_array_equal(
            processed_conc.evaluate(t=2),
            np.concatenate(
                [
                    2 * np.ones(mesh["negative electrode"][0].npts),
                    4 * np.ones(mesh["separator"][0].npts),
                    6 * np.ones(mesh["positive electrode"][0].npts),
                ]
            ),
        )

        # Piecewise constant state vectors
        a_sv = pybamm.Broadcast(pybamm.StateVector(slice(0, 1)), ["negative electrode"])
        b_sv = pybamm.Broadcast(pybamm.StateVector(slice(1, 2)), ["separator"])
        c_sv = pybamm.Broadcast(pybamm.StateVector(slice(2, 3)), ["positive electrode"])
        conc = pybamm.Concatenation(a_sv, b_sv, c_sv)

        self.assertEqual(
            conc.domain, ["negative electrode", "separator", "positive electrode"]
        )
        self.assertEqual(conc.children[0].domain, ["negative electrode"])
        self.assertEqual(conc.children[1].domain, ["separator"])
        self.assertEqual(conc.children[2].domain, ["positive electrode"])

        processed_conc = disc.process_symbol(conc)
        y = np.array([1, 2, 3])
        np.testing.assert_array_equal(
            processed_conc.evaluate(y=y),
            np.concatenate(
                [
                    np.ones(mesh["negative electrode"][0].npts),
                    2 * np.ones(mesh["separator"][0].npts),
                    3 * np.ones(mesh["positive electrode"][0].npts),
                ]
            ),
        )

        # Mixed
        conc = pybamm.Concatenation(a, b_t, c_sv)

        self.assertEqual(
            conc.domain, ["negative electrode", "separator", "positive electrode"]
        )
        self.assertEqual(conc.children[0].domain, ["negative electrode"])
        self.assertEqual(conc.children[1].domain, ["separator"])
        self.assertEqual(conc.children[2].domain, ["positive electrode"])

        processed_conc = disc.process_symbol(conc)
        np.testing.assert_array_equal(
            processed_conc.evaluate(t=2, y=y),
            np.concatenate(
                [
                    np.ones(mesh["negative electrode"][0].npts),
                    4 * np.ones(mesh["separator"][0].npts),
                    3 * np.ones(mesh["positive electrode"][0].npts),
                ]
            ),
        )

    def test_domain_error(self):
        a = pybamm.Symbol("a")
        b = pybamm.Symbol("b")
        with self.assertRaisesRegex(pybamm.DomainError, "domain cannot be empty"):
            pybamm.DomainConcatenation([a, b], None)

    def test_simplify_concatenation_state_vectors(self):
        disc = get_discretisation_for_testing()
        mesh = disc.mesh

        a = pybamm.Variable("a", domain=["negative electrode"])
        b = pybamm.Variable("b", domain=["separator"])
        c = pybamm.Variable("c", domain=["positive electrode"])
        conc = pybamm.Concatenation(a, b, c)
        disc.set_variable_slices([a, b, c])
        conc_disc = disc.process_symbol(conc)
        conc_simp = conc_disc.simplify()

        y = mesh.combine_submeshes(*conc.domain)[0].nodes ** 2
        self.assertIsInstance(conc_simp, pybamm.StateVector)
        self.assertEqual(conc_simp.y_slice.start, 0)
        self.assertEqual(conc_simp.y_slice.stop, len(y))
        np.testing.assert_array_equal(conc_disc.evaluate(y=y), conc_simp.evaluate(y=y))


if __name__ == "__main__":
    print("Add -v for more debug output")
    import sys

    if "-v" in sys.argv:
        debug = True
    unittest.main()
