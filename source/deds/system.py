import abc
import sage
from sympy import ImmutableDenseMatrix, Basic, Expr, Symbol, Matrix
from typing import *
import warnings

from sage.symbolic.expression import Expression

from .errors import *


class TimeInvariantControlSystemSpecification:
    """
    Time-Invariant Control System Specification.

    This class captures the user's description of their control system that takes the form

    .. math::
        \\dot{x} = f(x, u).
    
    The list of states :math:`(x^1, \\ldots, x^n)` and controls :math:`(u^1,\\ldots,u^m)` are sympy Symbols.
    The smooth vector field :math:`f` is expressed as a sympy ImmutableDenseMatrix where the order of the elements align with the order of the states provided.
    The control system cannot have more controls than states, and must have at least one control.
    In addition to this, an operating point, expressed as a map from :math:`(x, u)` to constants :math:`(\\bar{x},\\bar{u})`, is required and must be an equilibrium configuration.
    That is,

    .. math::
        f(\\bar{x}, \\bar{u}) = 0.

    If any preconditions are violated, then the constructor will raise an :py:class:`deds.errors.InvalidControlSystemError`.

    :param List[Symbol] states: sympy symbolic variables of the states.
    :param List[Symbol] controls: sympy symbolic varaibles of the controls.
    :param ImmutableDenseMatrix dynamics: vector field :math:`f(x, u)`.
    :param Mapping[Symbol, complex] operating_point: operating point :math:`(\\bar{x}, \\bar{u})`.
    """

    n: int 
    '''Dimension of the state-space.'''
    
    m: int
    '''Dimension of the control-space.'''

    states: List[Symbol]
    '''Sympy symbolic variables of the states.'''

    controls: List[Symbol]
    '''Sympy symbolic variables of the controls.'''

    dynamics: ImmutableDenseMatrix
    '''Vector field :math:`f(x, u)`.'''

    operating_point: Mapping[Symbol, complex]
    '''Operating point :math:`(\\bar{x}, \\bar{u})`.'''

    def __init__(
        self,
        states: List[Symbol],
        control: List[Symbol],
        dynamics: ImmutableDenseMatrix,
        operating_point: Mapping[Basic, Basic | complex],
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
        if not set(dynamics.free_symbols) == set(states + control):
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
        self.dynamics = ImmutableDenseMatrix([dynamics[:]])
        self.operating_point = operating_point

        self.deds_states = [Symbol(f"x{k}") for k in range(1, self.n + 1)]
        self.deds_controls = [Symbol(f"u{k}") for k in range(1, self.m + 1)]

        self.deds_to_user_map = dict(
            zip(self.deds_states + self.deds_controls, self.states + self.controls)
        )
        self.user_to_deds_map = dict(
            zip(self.states + self.controls, self.deds_states + self.deds_controls)
        )

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


class LocalControlSystem:
    """
    Internal representation of a local control system.

    This class represents the control system :math:`\\dot{x} = f(x, u)` on the lifted manifold :math:`\\mathcal{M} = \\mathbb{R} \\times \\mathbb{R}^m \\times \\mathbb{R}^n` as the exterior differential system,

    .. math::
        \\mathcal{I}^{(0)} = \\left\\langle dx^1 - f^1(x, u)\\,dt, \\ldots, dx^n - f^n(x, u)\\,dt \\right\\rangle,

    and computes the associated derived flag,

    .. math::
        \\mathcal{I}^{(0)} \\supset \\mathcal{I}^{(1)} \\supset \cdots \\supset \\mathcal{I}^{(N - 1)} \\supset \\mathcal{I}^{(N)} = \\mathcal{I}^{(N+1)}.
    
    The user **should not** construct this class directly, and instead should rely on the :py:class:`deds.system.LocalControlSystemFactory` to build the control system from a user-specified :py:class:`deds.system.TimeInvariantControlSystemSpecification`.
    """

    def __init__(
        self, specification: TimeInvariantControlSystemSpecification, M, U, f, p0
    ):
        self.specification = specification
        self.m = specification.m
        self.n = specification.n
        self.M = M
        self.U = U
        self.p0 = p0
        self.f = f
        self.regularity = True
        self._compute_system_properties()

    def relative_degree_of(self, h: Basic, well_defined_to_order=0) -> int:
        """
        Computes the relative degree of the provided smooth output function of the states.

        Let an output :math:`h: \\mathbb{R}^n \\to \\mathbb{R}` be a smooth function of the states.
        The output :math:`h` has a (well-defined) (finite) relative degree :math:`k > 0` if, on an open neighbourhood containing the operating point, the differential :math:`dh` satisfies,

        .. math:: dh \\in \\langle \\mathcal{I}^{(k-1)}, dt \\rangle,
            :label: relative-degree-well-defined

        and at the operating point,

        .. math:: dh_{\\bar{p}} \\in \\langle \\mathcal{I}^{(k)}, dt \\rangle.
            :label: relative-degree-finite
        
        The relative degree is considered infinite if no such index :math:`k` exists where condition :eq:`relative-degree-finite` holds.
        The condition :eq:`relative-degree-well-defined` is what ensures the relative degree is "well-defined".
        This is not a checkable condition and, as a result, is not checked by default.
        The default is to verify :eq:`relative-degree-well-defined` at just the operating point.
        The condition :eq:`relative-degree-finite` is checkable, however.
        As a result, this function technically only computes the proposed relative degree assuming it is well-defined (or if it is infinite).
        
        To aid in cases where users wish to attempt to check whether condition :eq:`relative-degree-well-defined` holds, the option well_defined_to_order is provided.
        If it is positive, the condition :eq:`relative-degree-well-defined` is checked via a Taylor series expansion about the operating point to the provided order;
        observe that when well_defined_to_order=0, we recover the original operating point test.
        If the output fails this test, then the :py:class:`deds.errors.OutputHasIllDefinedRelativeDegreeError` is raised.

        :param sympy.Basic h: A sympy expression of the user's output function in terms of the user's variables.
        :returns: a non-negative number equal to the finite relative degree of h if it exists, or -1 to indicate infinite relative degree.
        :rtype: int
        """

        from itertools import islice, accumulate
        from sage.calculus.functional import taylor

        # Check h is a smooth function of the states and inputs.
        if not set(h.free_symbols) <= set(
            self.specification.states + self.specification.controls
        ):
            raise InvalidOutputFunctionError()

        # Lift h.
        h = h.subs(self.specification.user_to_deds_map)._sage_()

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

    def _compute_system_properties(self):
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


class DynamicallyExtendedLocalControlSystem(LocalControlSystem):

    def __init__(self, control_system: LocalControlSystem, output_function):
        self.original_control_system = control_system
        self.output_function = output_function

        n = control_system.n + 1
        m = control_system.m

        M = Manifold(1 + m + n, "M")

        vvars = map(lambda k: f"u{k}", range(1, self.m + 1))
        yvars = map(lambda k: f"x{k}", range(1, self.n + 1))

        super().__init__(n, m, M, U, f, p0)


class AbstractLocalControlSystemFactory(abc.ABC):
    """
    Factory for building an instance of :py:class:`deds.system.LocalControlSystem`.
    """
    
    @abc.abstractmethod
    def make_control_system(self) -> LocalControlSystem:
        """
        Make a :py:class:`deds.system.LocalControlSystem` using current configuration.
        """
        ...

class LocalControlSystemFactory(AbstractLocalControlSystemFactory):
    """
    Factory for :py:class:`deds.system.LocalControlSystem`.

    Use this factory to construct a :py:class:`deds.system.LocalControlSystem` from the user configured :py:class:`deds.system.TimeInvariantControlSystemSpecification`.
    The factory properly lifts the user specified control system into a higher manifold 
    
    .. math::
        \\mathcal{M} = \\mathbb{R} \\times \\mathbb{R}^m \\times \\mathbb{R}^n
        
    which contains coordinates for time :math:`t`, controls :math:`u` and states :math:`x`.
    Variables are normalized and a mapping is preserved between the internal representation and the user's presentation of these variables.

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
    However, we can instead ask that the control distribution have maximal dimension at the operating point, i.e. :math:`\\mathrm{dim}\,\\left.\\mathscr{G}_0\\right|_{\\bar{p}} = m`.
    Equivalently, this asks that all inputs act in different directions without redundancy at the operating point.
    This is sufficient to ensure that there exists an open neighbourhood of the operating point where the system is regular in the manner required.

    :param deds.system.TimeInvariantControlSystemSpecification specification: control system specification.
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

        self.dt = coframe[0]
        self.du = [coframe[k] for k in range(1, 1 + self.specification.m)]
        self.dx = [
            coframe[k]
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
        G0_p0 = Matrix(
            [
                [comp.expr("sympy").subs(self.p0).nsimplify() for comp in g_j.comp()]
                for g_j in G0
            ]
        )

        if G0_p0.rank() != self.specification.m:
            raise InvalidControlSystemError(
                _InvalidControlSystemErrorMessages.irregularControlSystem
            )

    def make_control_system(self) -> LocalControlSystem:
        return LocalControlSystem(
            self.specification, self.manifold, self.neighbourhood, self.F, self.p0
        )
