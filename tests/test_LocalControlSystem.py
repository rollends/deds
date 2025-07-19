import deds 
from sympy import Symbol, Matrix, ImmutableDenseMatrix, sympify
import unittest

class InvalidControlSystemSpecifications(unittest.TestCase):

    def test_no_input(self):
        x = Symbol('x')
        f = ImmutableDenseMatrix([x])

        def make_bad_specification():
            return deds.TimeInvariantControlSystemSpecification([x], [], f, {x : sympify(0)})
        
        self.assertRaises(deds.InvalidControlSystemError, make_bad_specification)

    def test_no_state(self):
        x = Symbol('x')
        f = ImmutableDenseMatrix([])

        def make_bad_specification():
            return deds.TimeInvariantControlSystemSpecification([], [x], f, {x : sympify(0)})
        
        self.assertRaises(deds.InvalidControlSystemError, make_bad_specification)

    def test_too_many_inputs(self):
        x = Symbol('x')
        u = Symbol('u')
        v = Symbol('v')
        f = ImmutableDenseMatrix([x - u + v])

        def make_bad_specification():
            return deds.TimeInvariantControlSystemSpecification([x], [u, v], f, {x : sympify(0), u: sympify(0), v : sympify(0)})
        
        self.assertRaises(deds.InvalidControlSystemError, make_bad_specification)

    def test_dynamics_not_specified(self):
        x = Symbol('x')
        u = Symbol('u')
        f = ImmutableDenseMatrix([])

        def make_bad_specification():
            return deds.TimeInvariantControlSystemSpecification([x], [u], f, {x : sympify(0), u: sympify(0)})
        
        self.assertRaises(deds.InvalidControlSystemError, make_bad_specification)

    def test_dynamics_not_well_defined(self):
        x = Symbol('x')
        u = Symbol('u')
        v = Symbol('v')
        f = ImmutableDenseMatrix([x - u + v])

        def make_bad_specification():
            return deds.TimeInvariantControlSystemSpecification([x], [u], f, {x : sympify(0), u: sympify(0), v : sympify(0)})
        
        self.assertRaises(deds.InvalidControlSystemError, make_bad_specification)

    def test_operating_point_unset(self):
        x = Symbol('x')
        u = Symbol('u')
        f = ImmutableDenseMatrix([x - u])

        def make_bad_specification():
            return deds.TimeInvariantControlSystemSpecification([x], [u], f, { })
        
        self.assertRaises(deds.InvalidControlSystemError, make_bad_specification)

    def test_operating_point_not_constant(self):
        x = Symbol('x')
        u = Symbol('u')
        v = Symbol('v')
        f = ImmutableDenseMatrix([x - u])

        def make_bad_specification():
            return deds.TimeInvariantControlSystemSpecification([x], [u], f, { x : sympify(0), u : v })
        
        self.assertRaises(deds.InvalidControlSystemError, make_bad_specification)


class LTIControlSystem(unittest.TestCase):

    def test_simple_siso(self):
        x = Symbol('x')
        u = Symbol('u')
        f = ImmutableDenseMatrix([x - u])

        specification = deds.TimeInvariantControlSystemSpecification([x], [u], f, {x : sympify(0), u : sympify(0)})
        factory = deds.LocalControlSystemFactory(specification)
        system = factory.make_control_system()

        self.assertEqual(len(system.derived_flag), 2)
        self.assertEqual(len(system.derived_flag[0]), 1)
        self.assertEqual(len(system.derived_flag[1]), 0)

    def test_siso_controllable(self):
        x = Symbol('x')
        y = Symbol('y')
        z = Symbol('z')
        u = Symbol('u')
        f = ImmutableDenseMatrix([x - y, x + y - z, + z + u])

        specification = deds.TimeInvariantControlSystemSpecification([x, y, z], [u], f, {x : sympify(0), y : sympify(0), z : sympify(0), u : sympify(0)})
        factory = deds.LocalControlSystemFactory(specification)
        system = factory.make_control_system()

        self.assertEqual(len(system.derived_flag), 4)
        self.assertEqual(len(system.derived_flag[0]), 3)
        self.assertEqual(len(system.derived_flag[1]), 2)
        self.assertEqual(len(system.derived_flag[2]), 1)
        self.assertEqual(len(system.derived_flag[3]), 0)

        self.assertEqual(system.relative_degree_of(x), 3)
        self.assertEqual(system.relative_degree_of(y), 2)
        self.assertEqual(system.relative_degree_of(z), 1)

    def test_siso_controllable_bad_relative_degree(self):
        x = Symbol('x')
        y = Symbol('y')
        z = Symbol('z')
        u = Symbol('u')
        f = ImmutableDenseMatrix([x - y, x + y - z, + z + u])

        specification = deds.TimeInvariantControlSystemSpecification([x, y, z], [u], f, {x : sympify(0), y : sympify(0), z : sympify(0), u : sympify(0)})
        factory = deds.LocalControlSystemFactory(specification)
        system = factory.make_control_system()

        def bad_output_function():
            return system.relative_degree_of(x**2, well_defined_to_order=1)
        
        self.assertRaises(deds.OutputHasIllDefinedRelativeDegreeError, bad_output_function)

    def test_siso_uncontrollable(self):
        x = Symbol('x')
        y = Symbol('y')
        z = Symbol('z')
        u = Symbol('u')
        f = ImmutableDenseMatrix([-x, x + y - z, + z + u])

        specification = deds.TimeInvariantControlSystemSpecification([x, y, z], [u], f, {x : sympify(0), y : sympify(0), z : sympify(0), u : sympify(0)})
        factory = deds.LocalControlSystemFactory(specification)
        system = factory.make_control_system()

        self.assertEqual(len(system.derived_flag), 3)
        self.assertEqual(len(system.derived_flag[0]), 3)
        self.assertEqual(len(system.derived_flag[1]), 2)
        self.assertEqual(len(system.derived_flag[2]), 1)

        self.assertEqual(system.relative_degree_of(y), 2)
        self.assertEqual(system.relative_degree_of(z), 1)
        self.assertEqual(system.relative_degree_of(x), -1)


class NonlinearControlAffineSystem(unittest.TestCase):

    def test_simple_system(self):
        x = Symbol('x')
        y = Symbol('y')
        u = Symbol('u')
        v = Symbol('v')
        f = ImmutableDenseMatrix([(x+1)*u + v, (y-1)*v])

        specification = deds.TimeInvariantControlSystemSpecification([x, y], [u, v], f, {x : sympify(0), y : sympify(0), u : sympify(0), v : sympify(0)})
        factory = deds.LocalControlSystemFactory(specification)
        system = factory.make_control_system()

        self.assertEqual(len(system.derived_flag), 2)
        self.assertEqual(len(system.derived_flag[0]), 2)
        self.assertEqual(len(system.derived_flag[1]), 0)

        self.assertEqual(system.relative_degree_of(x, well_defined_to_order=2), 1)
        self.assertEqual(system.relative_degree_of(y, well_defined_to_order=2), 1)

    def test_one_active_one_passive(self):
        x = Symbol('x')
        y = Symbol('y')
        u = Symbol('u')
        v = Symbol('v')
        f = ImmutableDenseMatrix([(x+1)*u + v, (y-1)*v])

        specification = deds.TimeInvariantControlSystemSpecification([x, y], [u, v], f, {x : sympify(0), y : sympify(0), u : sympify(0), v : sympify(0)})
        factory = deds.LocalControlSystemFactory(specification)
        system = factory.make_control_system()

        self.assertEqual(len(system.derived_flag), 2)
        self.assertEqual(len(system.derived_flag[0]), 2)
        self.assertEqual(len(system.derived_flag[1]), 0)

        self.assertEqual(system.relative_degree_of(x, well_defined_to_order=2), 1)
        self.assertEqual(system.relative_degree_of(y, well_defined_to_order=2), 1)