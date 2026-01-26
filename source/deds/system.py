import abc
import sage
import sage.manifolds.differentiable.diff_form
import sage.manifolds.differentiable.diff_map
import sage.manifolds.differentiable.vectorfield
import sage.manifolds.manifold
import sage.manifolds.vector_bundle
from sage.symbolic.expression import Expression
import sage.geometry
import sage.manifolds
import sage.manifolds.differentiable
import sympy
from typing import *
import warnings

from .errors import *
from .errors import _InvalidControlSystemErrorMessages


class TimeInvariantControlSystemSpecification:
    """
    Time-Invariant Control System Specification.

    This class captures the user's description of their control system that takes the form

    .. math::
        \\dot{x} = f(x, u).

    The list of states :math:`(x^1, \\ldots, x^n)` and controls :math:`(u^1,\\ldots,u^m)` are sympy Symbols.
    The smooth vector field :math:`f` is expressed as a sympy ImmutableDenseMatrix where the order of the elements align with the order of the states provided.
    The control system cannot have more controls than states, and must have at least one control.
    In addition to this, an operating point, expressed as a map from :math:`(x, u)` to constants :math:`(\\bar{x},\\bar{u})`, is required.
    If any preconditions are violated, then the constructor will raise an :py:class:`deds.errors.InvalidControlSystemError`.

    :param List[Symbol] states: sympy symbolic variables of the states.
    :param List[Symbol] controls: sympy symbolic varaibles of the controls.
    :param ImmutableDenseMatrix dynamics: vector field :math:`f(x, u)`.
    :param Mapping[Symbol, complex] operating_point: operating point :math:`(\\bar{x}, \\bar{u})`.
    """

    n: int
    """Dimension of the state-space."""

    m: int
    """Dimension of the control-space."""

    states: List[sympy.Symbol]
    """Sympy symbolic variables of the states."""

    controls: List[sympy.Symbol]
    """Sympy symbolic variables of the controls."""

    dynamics: sympy.ImmutableDenseMatrix
    """Vector field :math:`f(x, u)`."""

    operating_point: Mapping[sympy.Symbol, complex]
    """Operating point :math:`(\\bar{x}, \\bar{u})`."""

    def __init__(
        self,
        states: List[sympy.Symbol],
        control: List[sympy.Symbol],
        dynamics: sympy.ImmutableDenseMatrix,
        operating_point: Mapping[sympy.Basic, sympy.Basic | complex],
    ):

        self.n = len(states)
        self.m = len(control)

        # Dimensions must make sense...
        if not (0 < self.m <= self.n):
            raise InvalidControlSystemError(
                _InvalidControlSystemErrorMessages.invalidDimensions
            )

        # Dynamics must be defined for exactly every state.
        if not len(dynamics) == self.n:
            raise InvalidControlSystemError(
                _InvalidControlSystemErrorMessages.invalidDynamicsLength
            )

        # We expect the dynamics to be a pure function of the state
        # controls.
        if not set(dynamics.free_symbols) <= set(states + control):
            raise InvalidControlSystemError(
                _InvalidControlSystemErrorMessages.invalidDynamics
            )

        # Operating point must map every state and control to a value,
        # no more, no less.
        if not set(operating_point.keys()) == set(states + control):
            raise InvalidControlSystemError(
                _InvalidControlSystemErrorMessages.undeterminedOperatingPoint
            )

        # Operating point value must be constant.
        if not all(map(lambda e: e.is_constant(), operating_point.values())):
            raise InvalidControlSystemError(
                _InvalidControlSystemErrorMessages.invalidOperatingPoint
            )

        self.states = list(states)
        self.controls = list(control)
        self.dynamics = sympy.ImmutableDenseMatrix([dynamics[:]])
        self.operating_point = operating_point

        self.deds_states = [sympy.Symbol(f"x{k}") for k in range(1, self.n + 1)]
        self.deds_controls = [sympy.Symbol(f"u{k}") for k in range(1, self.m + 1)]

        self.deds_to_user_map = dict(
            zip(self.deds_states + self.deds_controls, self.states + self.controls)
        )
        self.user_to_deds_map = dict(
            zip(self.states + self.controls, self.deds_states + self.deds_controls)
        )

    def pullback_onto_user_mfld(self, h: sympy.Basic) -> sympy.Basic:
        """
        Pullback function into user's original coordinate system.

        Pulls back the smooth function `h` described in the DEDS (lifted) coordinate system into the user's specification coordinate system.
        """
        return h.subs(self.deds_to_user_map)

    def pullback_onto_deds_mfld(self, h: sympy.Basic) -> sympy.Basic:
        """
        Pullback function into DEDS lifted coordinate system.

        Pulls back the smooth function `h` described in the user's specification coordinate system into the DEDS (lifted) coordinate system.
        """
        if not (set(h.free_symbols) <= set(self.user_to_deds_map.keys())):
            print(set(h.free_symbols))
            raise InvalidOutputFunctionError()

        return h.subs(self.user_to_deds_map)

    def __str__(self) -> str:
        """
        Generate a user-friendly string documenting system specification.
        """

        return f"""Time-invariant, Control System Specification (# states = {self.n}, # controls = {self.m})
            States      
                x := {self.states}
            Controls    
                u := {self.controls}
            Dynamics
                f(x, u) := {self.dynamics}
            Operating Point
                {self.operating_point}
        """


class AbstractLocalControlSystem(abc.ABC):
    """
    A local, nonlinear control system.

    This class represents a control system :math:`\\dot{x} = f(x, u)` with states :math:`x \\in \\mathbb{R}^n` and controls :math:`u \\in \\mathbb{R}^m` on the lifted manifold :math:`\\mathcal{M} = \\mathbb{R} \\times \\mathbb{R}^m \\times \\mathbb{R}^n` as the exterior differential system,

    .. math::
        \\mathcal{I}^{(0)} = \\left\\langle dx^1 - f^1(x, u)\\,dt, \\ldots, dx^n - f^n(x, u)\\,dt \\right\\rangle,

    and computes the associated derived flag,

    .. math::
        \\mathcal{I}^{(0)} \\supset \\mathcal{I}^{(1)} \\supset \\cdots \\supset \\mathcal{I}^{(N - 1)} \\supset \\mathcal{I}^{(N)} = \\mathcal{I}^{(N+1)}.
    """

    n: int
    """Dimension of the state-space."""

    m: int
    """Dimension of the control-space."""

    M: sage.manifolds.manifold.Manifold
    """Lifted manifold."""

    U: sage.manifolds.chart.Chart
    """Local coordinate system."""

    p0: Mapping[Expression, complex]
    """Operating point."""

    f: sage.manifolds.differentiable.vectorfield.VectorField
    """System dynamics."""

    def __init__(
        self,
        n: int,
        m: int,
        M: sage.manifolds.manifold.Manifold,
        U: sage.manifolds.chart.Chart,
        p0: Mapping[Expression, complex],
        f: sage.manifolds.differentiable.vectorfield.VectorField,
    ):
        self.m = m
        self.n = n
        self.M = M
        self.U = U
        self.p0 = p0
        self.f = f
        self.regularity = True
        self._compute_system_properties()

    def relative_degree_of(self, h: Expression, well_defined_to_order=0) -> int:
        """
        Computes the relative degree of the provided smooth output function ``h`` of the states.

        Let an output :math:`h: \\mathbb{R}^n \\to \\mathbb{R}` be a smooth function of the states.
        The output :math:`h` has a well-defined, finite relative degree :math:`k > 0` if there exists an open neighbourhood containing the operating point where the differential :math:`dh` satisfies,

        .. math:: dh \\in \\langle \\mathcal{I}^{(k-1)}, dt \\rangle,
            :label: relative-degree-well-defined

        and at the operating point the differential satisfies,

        .. math:: dh_{\\bar{p}} \\not\\in \\langle \\mathcal{I}^{(k)}, dt \\rangle.
            :label: relative-degree-finite

        The relative degree is infinite if no such finite index :math:`k` exists.
        The condition :eq:`relative-degree-well-defined` is what determines whether the relative degree is "well-defined".
        Unlike :eq:`relative-degree-finite`, this is not a checkable condition and is not verified explicitly by this method.
        The method instead verifies :eq:`relative-degree-well-defined` at just the operating point to the provided polynomial order ``well_defined_to_order``;
        when ``well_defined_to_order`` is zero, the check decays to a one-point test.
        If the output fails this test, then the :py:class:`deds.errors.OutputHasIllDefinedRelativeDegreeError` is raised.

        :param Expression h: A Sage expression of the user's output function in terms of the DED's variables.
        :returns: a non-negative number equal to the finite relative degree of ``h`` if it exists, or -1 to indicate infinite relative degree.
        :rtype: int
        """
        from itertools import islice, accumulate
        from sage.calculus.functional import taylor

        # Check h is a smooth function of the states and inputs.
        if not set(h._sympy_().free_symbols) <= set(
            map(lambda e: e._sympy_(), self.x + self.u)
        ):
            raise InvalidOutputFunctionError()

        # Differential of h.
        dh = self.U.function(h).scalar_field().exterior_derivative()

        # Compute Relative Degree.
        for degree in range(len(self.derived_flag)):
            # H^k = <w^1, ..., w^r>
            ideal = self._time_augment_ideal(self.derived_flag[degree])

            # w^1 /\ ... /\ w^r
            basis_form = next(
                islice(
                    accumulate(ideal[1:], lambda a, b: a.wedge(b), initial=ideal[0]),
                    len(ideal) - 1,
                    None,
                )
            )

            # dh /\ w^1 /\ ... /\ w^r
            dh_wedge_basis = dh.wedge(basis_form)

            # Stop if dh /\ w^1 /\ ... /\ w^r =/= 0.
            dh_wedge_basis_comp = dh_wedge_basis.comp()
            if any(
                [
                    not dh_wedge_basis_comp[k]
                    .expr("sympy")
                    .subs(self.p0)
                    .nsimplify()
                    .is_zero
                    for k in dh_wedge_basis_comp.non_redundant_index_generator()
                ]
            ):
                break
            elif well_defined_to_order > 0:
                # Check if it is going to have well-defined relative
                # degree. This is not technically a checkable
                # condition, but we can do it analytically to a given
                # polynomial order.
                if any(
                    [
                        not taylor(
                            dh_wedge_basis_comp[k],
                            *self.p0.items(),
                            well_defined_to_order,
                        )
                        ._sympy_()
                        .nsimplify()
                        .is_zero
                        for k in dh_wedge_basis_comp.non_redundant_index_generator()
                    ]
                ):
                    raise OutputHasIllDefinedRelativeDegreeError()

        else:
            # This means dh was in every ideal up until the invariant
            # terminal ideal. Thus, conclude h has infinite relative
            # degree
            return -1

        # Broke the for loop, implying that we found a k >= 0 where,
        # dh \notin < I^k, dt >.
        # Relative degree is that index k.
        return degree

    def relative_degree_of_user_output(
        self, h: sympy.Basic, well_defined_to_order=0
    ) -> int:
        """
        Computes the relative degree of the provided smooth output function ``h`` of the states written in the user's coordinate system.

        Pulls back the user's output function into the DEDS coordinate system, and calls upon :py:meth:`AbstractLocalControlSystem.relative_degree_of`.

        :param sympy.Basic h: A sympy expression of the user's output function in terms of the user's variables.
        :returns: a non-negative number equal to the finite relative degree of ``h`` if it exists, or -1 to indicate infinite relative degree.
        :rtype: int
        """
        # Lift h.
        h = self.pullback_user_function(h)
        return self.relative_degree_of(h, well_defined_to_order=well_defined_to_order)

    @abc.abstractmethod
    def pullback_user_function(self, h: sympy.Basic) -> Expression:
        """
        Writes the smooth output function ``h`` of the states, written in the user's coordinate system, in terms of the DEDS (lifted) coordinate system for this control system.

        :param Expression h: A sympy.Basic expression of the user's output function in terms of the user's coordinate system.
        :returns: a Sage expression for the output function on this control system's manifold.
        :rtype: sage.symbolic.expression.Expression
        """
        ...

    def _compute_system_properties(self):
        self.t = self.U[0]
        self.u = [self.U[k] for k in range(1, 1 + self.m)]
        self.x = [self.U[k] for k in range(1 + self.m, 1 + self.m + self.n)]

        self.frame = self.U.frame()
        self.coframe = self.U.coframe()

        self.Dt = self.frame[0]
        self.Du = [self.frame[k] for k in range(1, 1 + self.m)]
        self.Dx = [self.frame[k] for k in range(1 + self.m, 1 + self.m + self.n)]

        self.dt = self.coframe[0]
        self.du = [self.coframe[k] for k in range(1, 1 + self.m)]
        self.dx = [self.coframe[k] for k in range(1 + self.m, 1 + self.m + self.n)]

        self.system_ideal = [
            self.dx[k] + (-self.dt) * self.dx[k].interior_product(self.f)
            for k in range(self.n)
        ]

        self._compute_derived_flag()
        self._compute_integrability_defect()

    def _compute_derived_flag(self):
        self.derived_flag = self._derive_flag(self.system_ideal)

    def _compute_integrability_defect(self):
        defect = list()

        for I in map(self._time_augment_ideal, self.derived_flag):
            If = self._derive_flag(I)

            if len(If) == 1:
                defect.append(0)
                continue

            defect.append(len(I) - len(If[1]))

        self.defect_index = defect

    def _time_augment_ideal(self, I):
        I = I.copy()
        H = [self.dt]
        H.extend(I)

        # Gram-Schmidt.
        for k in range(1, len(H)):
            f = sum(map(lambda v: v[0] * v[1], zip(H[0].comp(), H[k].comp()))) / sum(
                map(lambda v: v[0] * v[1], zip(H[0].comp(), H[0].comp()))
            )
            H[k] = H[k] - f * H[0]

        return H

    def _derive_ideal(self, Ik):
        from itertools import islice, accumulate
        from sympy import Matrix

        p0_dict = self.p0

        Ik1 = list()
        dI0wI0_coords = list()

        if len(Ik) == 0:
            return Ik, True

        # Ik = < w1, ..., wn >
        # omega is the n-form w1 /\ ... /\ wn.
        omega = next(
            islice(
                accumulate(Ik[1:], lambda a, b: a.wedge(b), initial=Ik[0]),
                len(Ik) - 1,
                None,
            )
        )

        omega_comp = omega.comp()
        regularity = True

        if all(
            [
                omega_comp[k].expr("sympy").subs(p0_dict).nsimplify().is_zero
                for k in omega_comp.non_redundant_index_generator()
            ]
        ):
            warnings.warn(
                "Encountered an ideal that is degenerately generated. Behaviour is undefined.",
                RuntimeWarning,
            )
            regularity = False

        for w in Ik:
            # dwk /\ omega is a (n + 2)-form.
            # Identically zero if dwk is generated by w1 through wn.
            dw_wedge_omega = w.exterior_derivative().wedge(omega)

            # Put it in coordinates of the (n + 2)-form vector space.
            c = dw_wedge_omega.comp()
            dw_wedge_omega_coords = [c[k] for k in c.non_redundant_index_generator()]

            dI0wI0_coords.append([e.expr("sympy") for e in dw_wedge_omega_coords])

        # Construct a map from the space of coefficients of the forms
        # dwk /\ omega to the space of (n + 2)-forms.
        # This map has a kernel, and that kernel precisely characterizes
        # the space of closed forms in ideal Ik.
        M = Matrix(dI0wI0_coords)
        Mt = M.transpose()

        # Compute the derived ideal.
        for nullVector in Mt.nullspace(
            iszerofunc=lambda e: e.subs(p0_dict).nsimplify().is_zero
        ):
            beta = sum(map(lambda z: z[0] * z[1]._sage_(), zip(Ik, nullVector)))
            Ik1.append(beta)

        return Ik1, regularity

    def _derive_flag(self, I0):
        J = [I0.copy()]

        while True:
            Ik = J[-1]
            Ik1, regularity = self._derive_ideal(Ik)
            self.regularity = self.regularity and regularity

            if len(Ik) == len(Ik1):
                # Ideal is invariant on derivation, derived flag
                # terminates.
                break

            J.append(Ik1)
        return J


class LocalControlSystem(AbstractLocalControlSystem):
    """
    A user-specified, local, nonlinear control system.
    """

    def __init__(
        self, specification: TimeInvariantControlSystemSpecification, M, U, f, p0
    ):
        super().__init__(specification.n, specification.m, M, U, p0, f)
        self.specification = specification

    def pullback_user_function(self, h: sympy.Basic) -> Expression:
        h = self.specification.pullback_onto_deds_mfld(h)
        return h._sage_()


class DynamicallyExtendedLocalControlSystem(AbstractLocalControlSystem):
    """
    A one-step dynamically extended, local control system.
    """

    def __init__(
        self,
        control_system: LocalControlSystem,
        pi: sage.manifolds.differentiable.diff_map.DiffMap,
        M: sage.manifolds.manifold.Manifold,
        U: sage.manifolds.chart.Chart,
        p0: Mapping[Expression, complex],
        f: sage.manifolds.differentiable.vectorfield.VectorField,
    ):
        m = control_system.m
        n = M.dim() - m - 1
        super().__init__(n, m, M, U, p0, f)

        self.base_system = control_system
        self.pi = pi

    def pullback_user_function(self, h: sympy.Basic) -> Expression:
        h = self.base_system.pullback_user_function(h)

        # Use projection map to pullback into the new coordinate system.
        h = self.pi.pullback(self.base_system.U.function(h).scalar_field())

        return h.expr(self.U)


class AbstractLocalControlSystemFactory(abc.ABC):
    """
    Factory for building an instance of :py:class:`AbstractLocalControlSystem`.
    """

    @abc.abstractmethod
    def make_control_system(self) -> AbstractLocalControlSystem:
        """
        Make a :py:class:`AbstractLocalControlSystem` using current configuration.
        """
        ...


class LocalControlSystemFactory(AbstractLocalControlSystemFactory):
    """
    Factory for :py:class:`LocalControlSystem`.

    Use this factory to construct a :py:class:`LocalControlSystem` from the user configured :py:class:`TimeInvariantControlSystemSpecification`.
    The factory properly lifts the user specified control system into a higher manifold

    .. math::
        \\mathcal{M} = \\mathbb{R} \\times \\mathbb{R}^m \\times \\mathbb{R}^n

    which contains coordinates for time :math:`t`, controls :math:`u` and states :math:`x`.

    The factory fails to construct the local control system and raises an :py:class:`deds.errors.InvalidControlSystemError` if the system is not sufficiently regular.
    What does this mean?
    For the control system,

    .. math::
        \\dot{x} = f(x, u),

    define the lifted vector field,

    .. math::
        X = \\partial_{t} + f^k(x, u) \\partial_{x^k} \\in \\Gamma(\\mathsf{T}\\mathcal{M}).

    Letting :math:`[\\cdot, \\cdot]` denote the Lie bracket, define the control distribution,

    .. math::
        \\mathscr{G}_0 = \\mathrm{span}\\left\\{ \\left[X, \\partial_{u^j}\\right] \\colon 1 \\leq j \\leq m  \\right\\}.

    The local control system expects that the control distribution :math:`\\mathscr{G}_0` has constant dimension in an open neighbourhood of the operating point;
    this is impossible to check.
    However, we can instead ask that the control distribution have maximal dimension at the operating point, i.e. :math:`\\mathrm{dim}\\,\\left.\\mathscr{G}_0\\right|_{\\bar{p}} = m`.
    Equivalently, this asks that all inputs act in different directions without redundancy at the operating point.
    This is sufficient to ensure that there exists an open neighbourhood of the operating point where the system is regular in the manner required.

    :param TimeInvariantControlSystemSpecification specification: control system specification.
    """

    def __init__(self, specification: TimeInvariantControlSystemSpecification):
        from itertools import starmap
        from operator import mul
        from sage.manifolds.manifold import Manifold

        self.specification = specification
        self.manifold = Manifold(1 + specification.m + specification.n, "M")

        tvars = ["t"]
        uvars = list(map(str, self.specification.deds_controls))
        xvars = list(map(str, self.specification.deds_states))

        self.neighbourhood = self.manifold.chart(" ".join(tvars + uvars + xvars))

        frame = self.neighbourhood.frame()
        coframe = self.neighbourhood.coframe()

        self.t = self.neighbourhood[0]
        self.u = self.neighbourhood[1 : (self.specification.m + 1)]
        self.x = self.neighbourhood[(self.specification.m + 1) :]

        self.Dt = frame[0]
        self.Du = [frame[k] for k in range(1, 1 + self.specification.m)]
        self.Dx = [
            frame[k]
            for k in range(
                1 + self.specification.m,
                1 + self.specification.m + self.specification.n,
            )
        ]

        # Operating point.
        self.p0 = dict()
        for k, v in self.specification.operating_point.items():
            self.p0[self.specification.user_to_deds_map[k]._sage_()] = v
        self.p0[self.t] = 0

        # Compute the vector field on the lifted manifold.
        f = map(
            lambda e: e.subs(self.specification.user_to_deds_map)._sage_(),
            self.specification.dynamics,
        )
        self.F = self.Dt + sum(starmap(mul, zip(self.Dx, f)))

        # Compute the first control distribution.
        G0 = [self.F.bracket(Du) for Du in self.Du]

        # We now expect that G0 is regular and maximal rank. Because
        # maximal rank at a point p0 ensures regularity on an open
        # set containing p0, we can simply check for maximal rank at
        # p0.
        G0_p0 = sympy.Matrix(
            [
                [comp.expr("sympy").subs(self.p0).nsimplify() for comp in g_j.comp()]
                for g_j in G0
            ]
        )

        if G0_p0.rank() != self.specification.m:
            raise InvalidControlSystemError(
                _InvalidControlSystemErrorMessages.irregularControlSystem
            )

    def make_control_system(self) -> AbstractLocalControlSystem:
        return LocalControlSystem(
            self.specification, self.manifold, self.neighbourhood, self.F, self.p0
        )


class DynamicallyExtendedLocalControlSystemFactory(AbstractLocalControlSystemFactory):
    """
    Factory for :py:class:`DynamicallyExtendedLocalControlSystem`.

    Use this factory to perform a one-step dynamic extension of an existing :py:class:`LocalControlSystem` with a smooth output function ``h`` that has finite relative degree.
    If successful, then the factor builds an instance of a :py:class:`DynamicallyExtendedLocalControlSystem`.

    Formally, the factory does the following.
    Let the existing ``base_system`` model a nonlinear control system,

    .. math::
        \\dot{x} = f(x, u),

    on the lifted manifold

    .. math::
        \\mathcal{M} = \\mathbb{R} \\times \\mathbb{R}^m \\times \\mathbb{R}^n.

    Since the output function :math:`h: \\mathcal{M}\\to\\mathbb{R}` has finite relative degree :math:`k > 0`, there exists an input :math:`u^j` so that,

    .. math::
        \\mathcal{L}_{\\partial{u^j}} \\mathcal{L}_f^k h \\neq 0.

    When viewing :math:`\\mathcal{L}_f^k h: \\mathcal{M}\\to\\mathbb{R}` as a smooth function, the precondition for implicit function theorem applies.
    Combining this with the fact that :math:`\\mathcal{L}_f^k h` must be zero at the operating point, we can find a smooth function :math:`g` so that, for any :math:`v^j` near zero,

    .. math::
        \\mathcal{L}_f^k h(x, u^1, \\ldots, u^{j-1}, g(x, u^1, \\ldots, \\hat{u}^j, \\ldots, u^m), u^{j+1}, \\ldots, u^m) = v^j,

    where the :math:`\\hat{\\cdot}` indicates exclusion of the argument.
    The function :math:`g` can then be used to construct a static feedback transformation treating :math:`v^j` as a new input that replaces :math:`u^j` and satisfies the property that along the dynamics :math:`f`,

    .. math::
        \\mathcal{L}_f^k h = v^j

    Finally, we can perform a dynamic extension of this new input :math:`v^j`.
    Define a new lifted manifold,

    .. math::
        \\mathcal{M}' = \\mathcal{M} \\times \\mathbb{R},

    with an additional state :math:`x^{n+1} = v^j` and an input :math:`u^j = \\dot{v}^j` that is the time-derivative of the redefined input :math:`v^j`.

    This method may spuriously fail when trying to construct the implicit function :math:`g`.
    If this happens, the method raises :py:class:`deds.errors.CouldNotComputeStaticFeedbackTransformationError`.
    In this case, dynamic extension is feasible, but the solver simply cannot compute the required implicit function to proceed (even though one exists).

    :param TimeInvariantControlSystemSpecification specification: control system specification.
    """

    def __init__(
        self, base_system: AbstractLocalControlSystem, output_function: sympy.Basic
    ) -> AbstractLocalControlSystem:
        from itertools import chain, starmap
        from operator import mul
        from sage.manifolds.manifold import Manifold

        # First verify that this is even a valid extension. We
        # need a finite relative degree.
        relative_degree = base_system.relative_degree_of_user_output(output_function)
        if relative_degree <= 0:
            raise OutputHasInfiniteRelativeDegreeError()

        # Lift h.
        h = base_system.pullback_user_function(output_function)

        # Lie derivatives of h up to relative degree.
        Lfkh = base_system.U.function(h).scalar_field()
        for k in range(relative_degree):
            Lfkh = Lfkh.lie_derivative(base_system.f)

        # Find an input to throw away as part of the feedback
        # transformation.
        for j in range(base_system.m):
            LgLfkh = Lfkh.lie_derivative(base_system.Du[j])

            if not LgLfkh.expr()._sympy_().subs(base_system.p0).nsimplify().is_zero:
                break
        else:
            raise OutputHasIllDefinedRelativeDegreeError()

        # Input j is the input we are going to change by the static
        # feedback transformation. Rest of the inputs stay the same.
        # Time to define the diffeomorphism.
        self.n = base_system.n + 1
        self.m = base_system.m
        self.manifold = Manifold(1 + self.m + self.n, "M")

        tvars = ["t"]
        uvars = list(map(lambda k: f"u{k}", range(1, self.m + 1)))
        xvars = list(map(lambda k: f"x{k}", range(1, self.n + 1)))
        self.neighbourhood = self.manifold.chart(" ".join(tvars + uvars + xvars))

        t = self.neighbourhood[0]
        u = self.neighbourhood[1 : (self.m + 1)]
        x = self.neighbourhood[(self.m + 1) :]

        vj = sympy.Symbol("vj")

        # Compute the non-trivial part of the static feedback
        # transformation. We want to solve,
        #   y^{n+1} = (L_f^k h)(x, u)
        # for u^j in terms of x and y^{n+1}.
        # Then we will use the fact that the x variables do not
        # change to find a function that determines the input u^j
        # from the states y of the extended system.
        local_inverses = sympy.solve(
            vj - Lfkh.expr()._sympy_(), [base_system.u[j]._sympy_()]
        )
        p0_sympy = dict(
            chain(
                map(lambda t: (t[0]._sympy_(), t[1]), base_system.p0.items()), [(vj, 0)]
            )
        )
        for inverse in local_inverses:
            if (
                (inverse - base_system.u[j]._sympy_())
                .subs(p0_sympy)
                .nsimplify()
                .is_zero
            ):
                break
        else:
            raise CouldNotComputeStaticFeedbackTransformationError()

        inverse = inverse.subs({vj : x[self.n-1]})

        pullback = dict(
            zip(
                chain([base_system.t], base_system.u, base_system.x),
                chain([t], u[0:j], [inverse._sage_()], u[(j + 1) :], x[0:self.n]),
            )
        )

        self.pi = self.manifold.diff_map(
            base_system.M,
            {
                (self.neighbourhood, base_system.U): [
                    t,
                    *u[:j],
                    inverse.subs(pullback),
                    *u[(j + 1) :],
                    *x[0 : base_system.n],
                ]
            },
        )

        self.p0 = dict()
        for var, value in base_system.p0.items():
            if var == u[j]:
                self.p0[x[self.n-1]] = 0
            else:
                self.p0[pullback[var]] = value
        self.p0[u[j]] = Lfkh.expr()._sympy_().subs(base_system.p0).nsimplify()

        frame = self.neighbourhood.frame()

        self.Dt = frame[0]
        self.Du = [frame[k] for k in range(1, 1 + self.m)]
        self.Dx = [
            frame[k]
            for k in range(
                1 + self.m,
                1 + self.m + self.n,
            )
        ]

        self.f = self.Dt
        for i, dxi in enumerate(base_system.dx):
            self.f = self.f + self.Dx[i] * self.pi.pullback(
                dxi.interior_product(base_system.f)
            )
        self.f = self.f + self.Dx[self.n - 1] * u[j]
        self.base_system = base_system

    def make_control_system(self) -> LocalControlSystem:
        return DynamicallyExtendedLocalControlSystem(
            self.base_system,
            self.pi,
            self.manifold,
            self.neighbourhood,
            self.p0,
            self.f,
        )
