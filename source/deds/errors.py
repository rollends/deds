
class _InvalidControlSystemErrorMessages:
    
    invalidDimensions = """
The time-invariant, control system specification only supports systems
with the following properties:

  - The number of states is positive.
  - The number of control inputs is positive.
  - The number of states is greater than or equal to the number of 
    control inputs.

One of these three has been violated by the provided specification.
    """

    invalidDynamicsLength = """
The time-invariant, control system specification requires dynamics to
be specified for each state. The provided dynamics must be a row or
column vector that has exactly the same number of elements as the 
number of states.
    """


    invalidDynamics = """
The time-invariant, control system specification received an 
expression for the dynamics that was not a pure function of the states
and control input.
    """

    undeterminedOperatingPoint = """
The time-invariant, control system specification requires an operating
equilibrium configuration. The provided operating point does not 
determine all the states and control inputs.
    """
                
    invalidOperatingPoint = """
The time-invariant, control system specification requires an operating
equilibrium configuration. The provided operating point is not 
constant.
    """

    irregularControlSystem = """
The local control system class only supports maximal and locally
regular control systems. Specifically, the initial control
distribution must have maximal rank at the operating point.
    """


class InvalidControlSystemError(Exception):
    """
    Error raised when one of the (many) assumptions made by the package on local nonlinear control systems is violated.
    """
    pass


class InvalidOutputFunctionError(Exception):
    """
    Error raised when an output function is not a smooth function of the states and inputs.
    """
    pass

class OutputHasIllDefinedRelativeDegreeError(Exception):
    """
    Error raised when an output function does not have a well-defined relative degree at the operating point.
    """
    pass