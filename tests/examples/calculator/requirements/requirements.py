# These requirements were auto generated
# from software requirements specification (SRS)
# document by TestFlows v1.9.230815.1123444.
# Do not edit by hand but re-generate instead
# using 'tfs requirements generate' command.
from testflows.core import Specification
from testflows.core import Requirement

Heading = Specification.Heading

RQ_Google_Calculator_Open = Requirement(
    name="RQ.Google.Calculator.Open",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL open when the user searches for `calculator` or similar terms in the search box.\n"
        "\n"
    ),
    link=None,
    level=2,
    num="2.1",
)

RQ_Google_Calculator_UI_NormalView = Requirement(
    name="RQ.Google.Calculator.UI.NormalView",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL have the following graphical user interface.\n"
        "\n"
        "![Calculator](calculator.png)\n"
        "\n"
    ),
    link=None,
    level=3,
    num="3.1.1",
)

RQ_Google_Calculator_UI_InverseView = Requirement(
    name="RQ.Google.Calculator.UI.InverseView",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL have the following graphical user interface when `Inv` button is clicked.\n"
        "\n"
        "![Calculator](inverse.png)\n"
        "\n"
    ),
    link=None,
    level=3,
    num="3.2.1",
)

RQ_Google_Calculator_UI_KeyboardInput = Requirement(
    name="RQ.Google.Calculator.UI.KeyboardInput",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support entering operations and numbers using keyboard.\n"
        "\n"
        "| Keyboard Input | Description\n"
        "| --- | --- |\n"
        "| `0` | digit `0` |\n"
        "| `1` | digit `1` |\n"
        "| `2` | digit `2` |\n"
        "| `3` | digit `3` |\n"
        "| `4` | digit `4` |\n"
        "| `5` | digit `5` |\n"
        "| `6` | digit `6` |\n"
        "| `7` | digit `7` |\n"
        "| `8` | digit `8` |\n"
        "| `9` | digit `9` |\n"
        "| `+` | addition |\n"
        "| `-` | subtraction |\n"
        "| `*` | multiplication |\n"
        "| `÷` | division |\n"
        "| `BACKSPACE` | clear (AC/CE) |\n"
        "| `%` | percentage |\n"
        "| `(` | left parenthesis |\n"
        "| `)` | right parenthesis |\n"
        "| `.` | decimal point |\n"
        "| `=` | calculate result |\n"
        "| `ENTER` | calculate result |\n"
        "| `!` | factorial |\n"
        "| `s` | sin() |\n"
        "| `c` | cos() |\n"
        "| `t` | tan() |\n"
        "| `S` | arcsin() |\n"
        "| `C` | arccos() |\n"
        "| `T` | arctan() |\n"
        "| `l`, `L` | ln() |\n"
        "| `g`, `G` | log() |\n"
        "| `p`, `P` | π constant |\n"
        "| `e` | Euler's number e |\n"
        "| `E` | scientific notation `10E3` |\n"
        "| `q`, `Q` | `√()` square root |\n"
        "| `a`, `A` | `Ans` answer |\n"
        "| `^` | <code>x<sup>y</sup></code> x to the power of y |\n"
        "| `R` | `Rnd` random number |\n"
        "| `r` | <code><sup>y</sup>√x</code> |\n"
        "\n"
    ),
    link=None,
    level=3,
    num="3.3.1",
)

RQ_Google_Calculator_UI_MixedInput = Requirement(
    name="RQ.Google.Calculator.UI.MixedInput",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support entering operations using keyboard and buttons mixed input for the same expression.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="3.4.1",
)

RQ_Google_Calculator_EnteringNumbers_Digits = Requirement(
    name="RQ.Google.Calculator.EnteringNumbers.Digits",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support entering number digits using `0`-`9` buttons, and the digits SHALL be added to the display.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="4.1.1",
)

RQ_Google_Calculator_EnteringNumbers_Negative = Requirement(
    name="RQ.Google.Calculator.EnteringNumbers.Negative",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The `-` button SHALL allow defining negative numbers.\n"
        "\n"
        "For example,\n"
        "```\n"
        "-2.0\n"
        "2*-1\n"
        "(-3\n"
        "1-.2\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="4.2.1",
)

RQ_Google_Calculator_EnteringNumbers_Decimal = Requirement(
    name="RQ.Google.Calculator.EnteringNumbers.Decimal",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support entering decimal numbers using the `.` button to add the decimal point.\n"
        "\n"
        "The calculator SHALL not allow entering numbers with multiple decimal points.\n"
        "\n"
        "The `.` SHALL return an `Error`.\n"
        "\n"
        "The calculator SHALL allow omitting `0` before the `.`. For example,\n"
        "```\n"
        "-.2 = 0.2\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="4.3.1",
)

RQ_Google_Calculator_EnteringNumbers_Decimal_Accuracy = Requirement(
    name="RQ.Google.Calculator.EnteringNumbers.Decimal.Accuracy",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL display decimal numbers to the 11th place after the decimal point.\n"
        "\n"
        "```\n"
        "0.12345678901\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=4,
    num="4.3.2.1",
)

RQ_Google_Calculator_EnteringNumbers_Infinity = Requirement(
    name="RQ.Google.Calculator.EnteringNumbers.Infinity",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support handling positive `Infinity` and negative `-Infinity`.\n"
        "\n"
    ),
    link=None,
    level=2,
    num="5.1",
)

RQ_Google_Calculator_EnteringNumbers_Infinity_Positive = Requirement(
    name="RQ.Google.Calculator.EnteringNumbers.Infinity.Positive",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "Any number larger than the maximum positive number SHALL be treated as a positive `Infinity`.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="5.2.1",
)

RQ_Google_Calculator_EnteringNumbers_Infinity_Negative = Requirement(
    name="RQ.Google.Calculator.EnteringNumbers.Infinity.Negative",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "Any number smaller than the maximum negative number SHALL be treated as negative `Infinity`.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="5.3.1",
)

RQ_Google_Calculator_Limits_MaximumPositiveNumber = Requirement(
    name="RQ.Google.Calculator.Limits.MaximumPositiveNumber",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support the maximum positive number `1.7976931348623157e+308` (<code>2<sup>1024</sup>-1</code>).\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.1.1",
)

RQ_Google_Calculator_Limits_MaximumNegativeNumber = Requirement(
    name="RQ.Google.Calculator.Limits.MaximumNegativeNumber",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support the maximum negative number of `-1.7976931348623157e+308` (<code>-2<sup>1024</sup>-1</code>).\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.2.1",
)

RQ_Google_Calculator_Limits_MinimumPositiveNumber = Requirement(
    name="RQ.Google.Calculator.Limits.MinimumPositiveNumber",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support the minimum positive number of `5E-324`.\n"
        "\n"
        "Any number that is smaller SHALL be treated as `0`.\n"
        "\n"
        "```\n"
        "5E-324/2 = 0\n"
        "1E-324 = 0\n"
        "2E-324 = 0\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.3.1",
)

RQ_Google_Calculator_Limits_MinimumNegativeNumber = Requirement(
    name="RQ.Google.Calculator.Limits.MinimumNegativeNumber",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support the minimum positive number of `-5E-324`.\n"
        "\n"
        "Any number that is smaller SHALL be treated as `0`.\n"
        "\n"
        "```\n"
        "-5E-324/2 = 0\n"
        "-1E-324 = 0\n"
        "-2E-324 = 0\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.4.1",
)

RQ_Google_Calculator_EnteringNumbers_ScientificNotation = Requirement(
    name="RQ.Google.Calculator.EnteringNumbers.ScientificNotation",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support entering numbers in scientific notation using the `EXP` button that SHALL add the `E` to the display.\n"
        "The `E` SHALL be equivalent to the <code>x 10<sup>x</sup></code> where `x` is the number that follows the `E`.\n"
        "\n"
        "For example,\n"
        "\n"
        "```\n"
        "1E2 = 100\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="6.5.1",
)

RQ_Google_Calculator_LastAnswer = Requirement(
    name="RQ.Google.Calculator.LastAnswer",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support retrieving the last non-`Error` answer using the `ANS` button that SHALL add the `Ans` to the display.\n"
        "\n"
        "For example,\n"
        "```\n"
        "1 x Ans\n"
        "```\n"
        "\n"
        "The value of `Ans` by default SHALL be `0`.\n"
        "```\n"
        "Ans = 0\n"
        "```\n"
        "\n"
        "A multiplication operation SHALL be assumed if there is a current expression. For example,\n"
        "```\n"
        "5Ans\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=2,
    num="7.1",
)

RQ_Google_Calculator_SwitchingBetweenRadiansAndDegrees = Requirement(
    name="RQ.Google.Calculator.SwitchingBetweenRadiansAndDegrees",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support specifying angles for the trigonometric functions either in radians or degrees.\n"
        "\n"
        "The user SHALL be able to switch between them using the `Rad | Deg` button, where the`Rad` SHALL set the radians mode and `Deg` SHALL set the degrees mode.\n"
        "\n"
        "The default mode SHALL be `Deg`.\n"
        "\n"
    ),
    link=None,
    level=2,
    num="8.1",
)

RQ_Google_Calculator_ClearingDisplay_ClearEntry = Requirement(
    name="RQ.Google.Calculator.ClearingDisplay.ClearEntry",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support clearing the last entry using the `CE` button, which SHALL remove the current last character or operator from the display.\n"
        "\n"
        "If there are no characters or operators left to remove, then `0` SHALL be displayed.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="9.1.1",
)

RQ_Google_Calculator_ClearingDisplay_ClearAll = Requirement(
    name="RQ.Google.Calculator.ClearingDisplay.ClearAll",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support clearing the last result using the `AC` button, which SHALL remove the result of the last expression from the display and display SHALL be set to `0`.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="9.2.1",
)

RQ_Google_Calculator_CalculatingResult = Requirement(
    name="RQ.Google.Calculator.CalculatingResult",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL calculate the result of the current expression using the `=` button, which SHALL cause the display to be cleared and show the result of the calculation if and only if the expression is complete.\n"
        "\n"
        "The evaluation of a complete expression SHALL result in the following:\n"
        "\n"
        "1. The answer prompt SHALL be set to the expression that was evaluated.\n"
        "\n"
        "2. The calculation history SHALL be updated to contain the last evaluated expression.\n"
        "\n"
        "3. The value of `Ans` SHALL be set to the result value.\n"
        "\n"
    ),
    link=None,
    level=2,
    num="10.1",
)

RQ_Google_Calculator_Addition = Requirement(
    name="RQ.Google.Calculator.Addition",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support adding integers and decimal numbers using the `+` button, which SHALL add the addition operator to the display.\n"
        "\n"
        "For example,\n"
        "\n"
        "```\n"
        "2 + 2\n"
        "-9 + 4\n"
        "2.3 + 1.33\n"
        "```\n"
        "\n"
        "The `+` operator SHALL handle `Infinity` as one of its arguments as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `Infinity` + X | `Infinity`  |\n"
        "| `-Infinity` + X | `-Infinity` |\n"
        "| `Infinity` + `Infinity` | `Infinity` |\n"
        "| `Infinity` - `Infinity` | `Error` |\n"
        "\n"
        "The result of the addition operation when either argument is an `Error` SHALL be `Error`.\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | --- |\n"
        "| 1 + . | `Error` |\n"
        "| . + . | `Error` |\n"
        "\n"
        "An incomplete expression SHALL not be evaluated.\n"
        "```\n"
        "1 + = 1 +\n"
        "```\n"
        "\n"
        "Clicking `+` button SHALL be ignored when the expression does not contain a left argument.\n"
        "```\n"
        "(+\n"
        "```\n"
        "\n"
        "Incomplete `+` operation SHALL be overwritable by the following operators:\n"
        "\n"
        "| Operator | Description |\n"
        "| --- | --- |\n"
        "| `*` | multiplication |\n"
        "| `-` | subtraction |\n"
        "| `/` | division |\n"
        "| `!` | factorial |\n"
        "| <code>x<sup>2</sup></code> | X squared |\n"
        "| <code>x<sup>y</sup></code> | X to the power of Y |\n"
        "| `y√x` | nth root |\n"
        "\n"
        "For example,\n"
        "```\n"
        "2+- = 2-\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="11.1.1",
)

RQ_Google_Calculator_Subtraction = Requirement(
    name="RQ.Google.Calculator.Subtraction",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support subtracting integers and decimal numbers using the `-` button that SHALL add the `-` operation to the display.\n"
        "\n"
        "For example,\n"
        "```\n"
        "2.0 - 2\n"
        "-9 - 4\n"
        "```\n"
        "\n"
        "The `-` operator SHALL handle `Infinity` as one of its arguments as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `Infinity` - X | `Infinity`  |\n"
        "| X - `Infinity` | `-Infinity` |\n"
        "| `-Infinity` - X | `-Infinity` |\n"
        "| `Infinity` - `Infinity` | `Error` |\n"
        "| `-Infinity` - `Infinity` | `-Infinity` |\n"
        "\n"
        "The result of the subtraction operation when either argument is an `Error` SHALL be `Error`.\n"
        "For example,\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | --- |\n"
        "| 1 - . | `Error` |\n"
        "| . - . | `Error` |\n"
        "\n"
        "An incomplete expression SHALL not be evaluated.\n"
        "```\n"
        "1 -\n"
        "2 * -\n"
        "```\n"
        "\n"
        "An incomplete `-` operation, when `-` is not treated as being used to define a negative number, SHALL be overwritable by the following operators:\n"
        "\n"
        "| Operator | Description |\n"
        "| --- | --- |\n"
        "| `+` | addition |\n"
        "| `*` | multiplication |\n"
        "| `/` | division |\n"
        "| `!` | factorial |\n"
        "| <code>x<sup>2</sup></code> | X squared |\n"
        "| <code>x<sup>y</sup></code> | X to the power of Y |\n"
        "| `y√x` | nth root |\n"
        "\n"
        "For example,\n"
        "```\n"
        "2-+ = 2+\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="11.2.1",
)

RQ_Google_Calculator_Multiplication = Requirement(
    name="RQ.Google.Calculator.Multiplication",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support multiplication of integers and decimal numbers using the `×` button, which SHALL add the multiplication operator to the display.\n"
        "\n"
        "```\n"
        "-9 × 4\n"
        "2.3 × 1.33\n"
        "```\n"
        "\n"
        "The `×` operator SHALL handle `Infinity` as one of its arguments as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `Infinity` × X | `Infinity`  |\n"
        "| `-Infinity` × X | `-Infinity` |\n"
        "| `Infinity` × `Infinity` | `Infinity` |\n"
        "| `-Infinity` × `Infinity` | `-Infinity` |\n"
        "\n"
        "The result of the `×` operation when either argument is an `Error` SHALL be `Error`.\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | --- |\n"
        "| 1 × . | `Error` |\n"
        "| . × . | `Error` |\n"
        "\n"
        "An incomplete expression SHALL not be evaluated.\n"
        "```\n"
        "1 ×\n"
        "```\n"
        "\n"
        "Clicking `×` button SHALL be ignored when the expression does not contain a left argument.\n"
        "```\n"
        "(×\n"
        "```\n"
        "\n"
        "Incomplete `×` operation SHALL be overwritable by the following operators:\n"
        "\n"
        "| Operator | Description |\n"
        "| --- | --- |\n"
        "| `+` | addition |\n"
        "| `÷` | division |\n"
        "| `!` | factorial |\n"
        "| <code>x<sup>2</sup></code> | X squared |\n"
        "| <code>x<sup>y</sup></code> | X to the power of Y |\n"
        "| `y√x` | nth root |\n"
        "\n"
        "For example,\n"
        "```\n"
        "2×+ = 2 +\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="11.3.1",
)

RQ_Google_Calculator_Division = Requirement(
    name="RQ.Google.Calculator.Division",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support division of integers and decimal numbers using the `÷` button that SHALL add the `÷` operator to the display.\n"
        "\n"
        "```\n"
        "2 ÷ 2\n"
        "2.3 ÷ 1.33\n"
        "```\n"
        "\n"
        "Division of positive number by `0` SHALL return `Infinity`.\n"
        "\n"
        "Division of negative number by `0` SHALL return `-Infinity`.\n"
        "\n"
        "`0 ÷ 0` SHALL return an `Error`.\n"
        "\n"
        "The `÷` operator SHALL handle `Infinity` as one of its arguments as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `Infinity` ÷ X | `Infinity`  |\n"
        "| `-Infinity` ÷ X | `-Infinity` |\n"
        "| X ÷ `Infinity` | `0` |\n"
        "| X ÷ `-Infinity` | `0` |\n"
        "| `Infinity` ÷ `Infinity` | `Error` |\n"
        "| `-Infinity` ÷ `Infinity` | `Error` |\n"
        "\n"
        "The result of the `÷` operation when either argument is an `Error` SHALL be `Error`.\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | --- |\n"
        "| 1 ÷ . | `Error` |\n"
        "| . ÷ . | `Error` |\n"
        "\n"
        "An incomplete expression SHALL not be evaluated.\n"
        "```\n"
        "1 ÷\n"
        "```\n"
        "\n"
        "Clicking `÷` button SHALL be ignored when the expression does not contain a left argument.\n"
        "```\n"
        "(÷\n"
        "```\n"
        "\n"
        "Incomplete `÷` operation SHALL be overwritable by the following operators:\n"
        "\n"
        "| Operator | Description |\n"
        "| --- | --- |\n"
        "| `+` | addition |\n"
        "| `×` | multiplication |\n"
        "| `!` | factorial |\n"
        "| <code>x<sup>2</sup></code> | X squared |\n"
        "| <code>x<sup>y</sup></code> | X to the power of Y |\n"
        "| `y√x` | nth root |\n"
        "\n"
        "For example,\n"
        "```\n"
        "2÷+ = 2 +\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="11.4.1",
)

RQ_Google_Calculator_Operations_Factorial = Requirement(
    name="RQ.Google.Calculator.Operations.Factorial",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support factorial operation using the `x!` button that SHALL add the `!` symbol to the display.\n"
        "\n"
        "The factorial operation SHALL be defined as\n"
        "```\n"
        "n! = n × (n - 1)!\n"
        "```\n"
        "\n"
        "The `0!` SHALL be 1.\n"
        "\n"
        "The factorial of a negative integer number SHALL be an `Error`.\n"
        "```\n"
        "(-4)! = Error\n"
        "```\n"
        "\n"
        "The factorial SHALL support positive and negative decimal numbers.\n"
        "```\n"
        "3.5! = 11.6317283966\n"
        "(-0.1)! = 1.06862870212\n"
        "```\n"
        "\n"
        "The negative of factorial expression SHALL be the negative of the factorial of the positive number.\n"
        "\n"
        "```\n"
        "-4! = -(4!) = -24\n"
        "```\n"
        "\n"
        "The maximum factorial that can be calculated SHALL be `170!`.\n"
        "```\n"
        "170! = 7.257416e+306\n"
        "```\n"
        "\n"
        "The factorial SHALL handle `Infinity` as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `Infinity`! | `Infinity`  |\n"
        "| `-Infinity`! | `-Infinity` |\n"
        "| `(-Infinity)`! | `Error` |\n"
        "\n"
        "The result of the factorial operation when argument is an `Error` SHALL be `Error`.\n"
        "```\n"
        " .! =  Error\n"
        "```\n"
        "\n"
        "Clicking `!` button SHALL be ignored when the expression does not contain a left argument.\n"
        "```\n"
        "(!\n"
        "```\n"
        "\n"
        "The factorial operation SHALL not be overwritable.\n"
        "```\n"
        "2!+ = 2! +\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="12.1.1",
)

RQ_Google_Calculator_Operation_SquareRoot = Requirement(
    name="RQ.Google.Calculator.Operation.SquareRoot",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support square root operation using the `√` button that SHALL add the `√(`  to the display.\n"
        "```\n"
        "√(4)\n"
        "```\n"
        "\n"
        "The `√` of a negative number SHALL return an `Error`.\n"
        "```\n"
        "√(-1)\n"
        "```\n"
        "\n"
        "The `√()` with no arguments SHALL return an `Error`.\n"
        "```\n"
        "√()\n"
        "```\n"
        "\n"
        "The `√()` SHALL handle `Infinity` as one of its arguments as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `√`(`Infinity`) | `Infinity`  |\n"
        "| `√`(`-Infinity`) | `Error` |\n"
        "\n"
        "The result of the `√()` operation when argument is an `Error` SHALL be `Error`.\n"
        "```\n"
        "√(.) =  Error\n"
        "```\n"
        "\n"
        "The `√(` operation SHALL not be overwritable.\n"
        "```\n"
        "√(+\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="12.2.1",
)

RQ_Google_Calculator_Operation_Logarithm = Requirement(
    name="RQ.Google.Calculator.Operation.Logarithm",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support Logarithm operation using the `log` button that SHALL add the `log(`  to the display.\n"
        "\n"
        "```\n"
        "log(4)\n"
        "```\n"
        "\n"
        "The `log` of a negative number SHALL return an `Error`.\n"
        "```\n"
        "log(-5)\n"
        "```\n"
        "\n"
        "The `log` of `0` SHALL return `-Infinity`.\n"
        "```\n"
        "log(0)\n"
        "```\n"
        "\n"
        "The `log()` with no arguments SHALL return an `Error`.\n"
        "```\n"
        "log()\n"
        "```\n"
        "\n"
        "The `log()` function SHALL handle `Infinity` as one of its arguments as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `log`(`Infinity`) | `Infinity`  |\n"
        "| `log`(`-Infinity`) | `Error` |\n"
        "\n"
        "The result of the `log()` operation when the argument is an `Error` SHALL be `Error`.\n"
        "```\n"
        "log(.) =  Error\n"
        "```\n"
        "\n"
        "The `log(` operation SHALL not be overwritable.\n"
        "```\n"
        "log(+\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="12.3.1",
)

RQ_Google_Calculator_Operation_NaturalLogarithm = Requirement(
    name="RQ.Google.Calculator.Operation.NaturalLogarithm",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support natural logarithm operation using the `ln` button that SHALL add the `ln(`  to the display.\n"
        "\n"
        "```\n"
        "ln(6)\n"
        "```\n"
        "\n"
        "The `ln` of a negative number SHALL return an `Error`.\n"
        "```\n"
        "ln(-6)\n"
        "```\n"
        "\n"
        "The `ln` of `0` SHALL return `-Infinity`.\n"
        "```\n"
        "ln(0)\n"
        "```\n"
        "\n"
        "The `ln()` with no arguments SHALL return an `Error`.\n"
        "```\n"
        "ln()\n"
        "```\n"
        "\n"
        "The `ln()` function SHALL handle `Infinity` as one of its arguments as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `ln`(`Infinity`) | `Infinity`  |\n"
        "| `ln`(`-Infinity`) | `Error` |\n"
        "\n"
        "The result of the `ln()` operation when argument is an `Error` SHALL be `Error`.\n"
        "```\n"
        "ln(.) =  Error\n"
        "```\n"
        "\n"
        "The `ln(` operation SHALL not be overwritable.\n"
        "```\n"
        "ln(+\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="12.4.1",
)

RQ_Google_Calculator_Percentage = Requirement(
    name="RQ.Google.Calculator.Percentage",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support specifying percentage using the `%` button, which SHALL add the `%`  operator to the display right after any last number or expression and be equivalent to `/100`.\n"
        "\n"
        "```\n"
        "5% + 2\n"
        "```\n"
        "\n"
        "If the display is empty when the user enters the `%` operation, then `0%` SHALL be displayed.\n"
        "\n"
        "The `-%` SHALL return an `Error`.\n"
        "\n"
        "The `.%` SHALL return an `Error`.\n"
        "\n"
        "The `Infinity%` SHALL return `Infinity`.\n"
        "\n"
        "The `-Infinity%` SHALL return `-Infinity`.\n"
        "\n"
        "The `%` is not valid when entering an argument to any function if it is not preceded by the number, and therefore using `%` button SHALL result in no changes to the current expression.\n"
        "\n"
        "The `%` SHALL not be overwritable.\n"
        "```\n"
        "2%+\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="12.5.1",
)

RQ_Google_Calculator_Operation_XToThePowerOfY = Requirement(
    name="RQ.Google.Calculator.Operation.XToThePowerOfY",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support `x` to the power of `y` operation using the <code>x<sup>y</sup></code> button that SHALL add the <code><sup>□</sup></code> to the display.\n"
        "The next expression entered SHALL specify the exponent `y`.\n"
        "\n"
        "<code>2<sup>3</sup></code>\n"
        "\n"
        "If `x` is`-0` and `y` exponent is negative, then the result SHALL be `-Infinity`.\n"
        "\n"
        "<code>-0<sup>-3</sup></code>\n"
        "\n"
        "The <code>x<sup>y</sup></code> SHALL handle `Infinity` as the Y exponent as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| <code>x<sup>Infinity</sup></code> | `Error`  |\n"
        "| <code>x<sup>-Infinity</sup></code> | `0` |\n"
        "\n"
        "The result of the <code>x<sup>y</sup></code> operation when exponent expression is an `Error` SHALL be `Error`.\n"
        "\n"
        "An incomplete expression SHALL not be evaluated.\n"
        "\n"
        "<code>2<sup>□</sup></code>\n"
        "\n"
        "Clicking <code>x<sup>y</sup></code>  button SHALL be ignored when the expression does not contain a left argument.\n"
        "\n"
        "<code>(x<sup>□</sup></code>\n"
        "\n"
        "Incomplete <code>x<sup>y</sup></code> operation SHALL be overwritable by the following operators:\n"
        "\n"
        "| Operator | Description |\n"
        "| --- | --- |\n"
        "| `+` | addition |\n"
        "| `×` | multiplication |\n"
        "| `÷` | division |\n"
        "| `!` | factorial |\n"
        "| <code>x<sup>2</sup></code> | X squared |\n"
        "| `y√x` | nth root |\n"
        "\n"
        "<code>2<sup>□</sup>+ = 2 +</code>\n"
        "\n"
    ),
    link=None,
    level=3,
    num="12.6.1",
)

RQ_Google_Calculator_Operations_EToThePowerOfX = Requirement(
    name="RQ.Google.Calculator.Operations.EToThePowerOfX",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support Euler's number, `e`, to the power of `x` operation using the `Inv` <code>e<sup>x</sup></code> button that SHALL add the <code>e<sup>□</sup></code> to the display. The next expression entered SHALL specify the exponent `x`.\n"
        "\n"
        "<code>e<sup>2</sup></code>\n"
        "\n"
        "The <code>e<sup>x</sup></code> SHALL handle `Infinity` as the X exponent as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| <code>e<sup>Infinity</sup></code> | `Infinity`  |\n"
        "| <code>e<sup>-Infinity</sup></code> | `0` |\n"
        "\n"
        "The result of the <code>e<sup>x</sup></code> operation when exponent expression is an `Error` SHALL be `Error`.\n"
        "\n"
        "An incomplete expression SHALL not be evaluated.\n"
        "\n"
        "<code>e<sup>□</sup></code>\n"
        "\n"
        "Incomplete <code>e<sup>x</sup></code> operation SHALL not be overwritable.\n"
        "\n"
        "The <code>x<sup>2</sup></code> SHALL set the `x` exponent to `2` if `x` was not specified.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="12.7.1",
)

RQ_Google_Calculator_Operations_10ToThePowerOfX = Requirement(
    name="RQ.Google.Calculator.Operations.10ToThePowerOfX",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support ten to the power of `x` operation using the `Inv` <code>10<sup>x</sup></code> button that SHALL add the <code>10<sup>□</sup></code> to the display.\n"
        "The next expression entered SHALL specify the exponent value of `x`.\n"
        "The multiplication operation SHALL be added if the current expression is non empty before the <code>10<sup>□</sup></code>.\n"
        "\n"
        "For example,\n"
        "\n"
        "<code>10<sup>□</sup></code>\n"
        "<code>0 x 10<sup>□</sup></code>\n"
        "\n"
        "The <code>10<sup>x</sup></code> SHALL handle `Infinity` as the X exponent as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| <code>10<sup>Infinity</sup></code> | `Infinity`  |\n"
        "| <code>10<sup>-Infinity</sup></code> | `0` |\n"
        "\n"
        "The result of the <code>10<sup>x</sup></code> operation when the exponent expression is an `Error` SHALL be `Error`.\n"
        "\n"
        "Incomplete expression SHALL not be evaluated.\n"
        "\n"
        "<code>10<sup>□</sup></code>\n"
        "\n"
        "An incomplete <code>10<sup>x</sup></code> operation SHALL not be overwritable.\n"
        "\n"
        "The <code>x<sup>2</sup></code> SHALL set the `x` exponent to `2` if `x` was not specified.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="12.8.1",
)

RQ_Google_Calculator_Operations_XSquared = Requirement(
    name="RQ.Google.Calculator.Operations.XSquared",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support calculating the square value using the `Inv` <code>x<sup>2</sup></code> button.\n"
        "If the display is empty, then it SHALL add <code>0<sup>2</sup></code> to the display.\n"
        "\n"
        "<code>2<sup>2</sup></code>\n"
        "\n"
        "The <code>x<sup>2</sup></code> SHALL handle `Infinity` as the value to be squared as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| <code>Infinity<sup>2</sup></code> | `Infinity`  |\n"
        "| <code>-Infinity<sup>2</sup></code> | `Infinity` |\n"
        "\n"
        "The result of the <code>x<sup>2</sup></code> operation when the exponent expression is an `Error` SHALL be `Error`.\n"
        "\n"
        "An incomplete expression SHALL not be evaluated.\n"
        "\n"
        "<code>2<sup>□</sup></code>\n"
        "\n"
        "Incomplete <code>x<sup>2</sup></code> operation SHALL not be overwritable.\n"
        "\n"
        "Clicking <code>x<sup>2</sup></code>  button SHALL be ignored when the expression does not contain a left argument.\n"
        "\n"
        "<code>(x<sup>□</sup></code>\n"
        "\n"
    ),
    link=None,
    level=3,
    num="12.9.1",
)

RQ_Google_Calculator_Operations_NthRoot = Requirement(
    name="RQ.Google.Calculator.Operations.NthRoot",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support calculating the value of N<sup>th</sup> root using the `Inv` <code><sup>y</sup>√x</code> button.\n"
        "If the display is empty then the <code><sup>□</sup>√0</code> to the display.\n"
        "\n"
        "If `x` is`-0` and `y` is negative, then the result SHALL be `-Infinity`.\n"
        "\n"
        "For example,\n"
        "```\n"
        "-1√-0\n"
        "```\n"
        "\n"
        "The <code>x<sup>2</sup></code> SHALL handle `Infinity` as the value to be squared as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| <code><sup>Infinity</sup>√x</code> | `1` |\n"
        "| <code><sup>-Infinity</sup>√x</code> | `1` |\n"
        "| <code><sup>y</sup>√Infinity</code> | `Infinity` |\n"
        "| <code><sup>y</sup>√-Infinity</code> | `-Infinity` |\n"
        "| <code><sup>Infinity</sup>√Infinity</code> | `1` |\n"
        "| <code><sup>-Infinity</sup>√Infinity</code> | `1` |\n"
        "| <code><sup>Infinity</sup>√-Infinity</code> | `1` |\n"
        "| <code><sup>-Infinity</sup>√-Infinity</code> | `1` |\n"
        "\n"
        "The result of the <code><sup>y</sup>√x</code> operation when either `x` or `y` is an `Error` SHALL be `Error`.\n"
        "\n"
        "An incomplete expression SHALL not be evaluated.\n"
        "\n"
        "<code><sup>□</sup>√2</code>\n"
        "\n"
        "Incomplete <code><sup>y</sup>√x</code> operation SHALL not be overwritable.\n"
        "\n"
        "Clicking <code><sup>y</sup>√x</code>  button SHALL be ignored when the expression does not contain a left argument.\n"
        "\n"
        "<code>(<sup>□</sup>√x</code>\n"
        "\n"
    ),
    link=None,
    level=3,
    num="12.10.1",
)

RQ_Google_Calculator_TrigonometricFunctions_Sine = Requirement(
    name="RQ.Google.Calculator.TrigonometricFunctions.Sine",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support calculating the value of sine the trigonometric function using the `sin` button that SHALL add `sin(` to the display.\n"
        "\n"
        "The `sin` function SHALL treat the angle as specified in either degrees or radians based on the currently selected `Rad|Deg` mode.\n"
        "\n"
        "The `sin` function call with an empty value SHALL return an `Error`.\n"
        "\n"
        "The `sin()` SHALL handle `Infinity` as an argument value as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `sin(Infinity)` | `Error` |\n"
        "| `sin(-Infinity)` | `Error` |\n"
        "\n"
        "The result of the `sin` operation when argument is an `Error` SHALL be `Error`.\n"
        "```\n"
        "sin(.) = Error\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="13.1.1",
)

RQ_Google_Calculator_TrigonometricFunctions_Cosine = Requirement(
    name="RQ.Google.Calculator.TrigonometricFunctions.Cosine",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support calculating the value of the cosine trigonometric function using the `cos` button that SHALL add `cos(` to the display.\n"
        "\n"
        "The `cos` function SHALL treat the angle as specified in either degrees or radians based on the currently selected `Rad|Deg` mode.\n"
        "\n"
        "The `cos` function call with an empty value SHALL return an `Error`.\n"
        "\n"
        "The `cos()` function SHALL handle `Infinity` as an argument value as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `cos(Infinity)` | `Error` |\n"
        "| `cos(-Infinity)` | `Error` |\n"
        "\n"
        "The result of the `cos` operation when argument is an `Error` SHALL be `Error`.\n"
        "```\n"
        "cos(.) = Error\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="13.2.1",
)

RQ_Google_Calculator_TrigonometricFunctions_Tangent = Requirement(
    name="RQ.Google.Calculator.TrigonometricFunctions.Tangent",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support calculating the value of the tangent trigonometric function using the `tan` button that SHALL add `tan(` to the display.\n"
        "\n"
        "The `tan` function SHALL treat the angle as specified in either degrees or radians based on the currently selected `Rad|Deg` mode.\n"
        "\n"
        "The `tan` function call with an empty value SHALL return an `Error`.\n"
        "\n"
        "The `tan()` function SHALL handle `Infinity` as an argument value as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `tan(Infinity)` | `Error` |\n"
        "| `cos(-Infinity)` | `Error` |\n"
        "\n"
        "The result of the `tan` operation when argument is an `Error` SHALL be `Error`.\n"
        "```\n"
        "tan(.) = Error\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="13.3.1",
)

RQ_Google_Calculator_TrigonometricFunctions_Arcsine = Requirement(
    name="RQ.Google.Calculator.TrigonometricFunctions.Arcsine",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support calculating the value of the arcsine trigonometric function using the `Inv` `sin^-1` button that SHALL add `arcsin(` to the display.\n"
        "\n"
        "The `arcsin` function SHALL treat the angle as specified in either degrees or radians based on the currently selected `Rad|Deg` mode.\n"
        "\n"
        "The `arcsin` function call SHALL return an `Error` for any argument larger than `1`\n"
        "or smaller than `-1`.\n"
        "\n"
        "The `arcsin` function call with an empty value SHALL return an `Error`.\n"
        "\n"
        "The `arcsin()` function SHALL handle `Infinity` as an argument value as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `arcsin(Infinity)` | `Error` |\n"
        "| `arcsin(-Infinity)` | `Error` |\n"
        "\n"
        "The result of the `arcsin` operation when argument is an `Error` SHALL be `Error`.\n"
        "```\n"
        "arcsin(.) = Error\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="13.4.1",
)

RQ_Google_Calculator_TrigonometricFunctions_Arccosine = Requirement(
    name="RQ.Google.Calculator.TrigonometricFunctions.Arccosine",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support calculating the value of the arccosine trigonometric function using the `Inv` `cos^-1` button that SHALL add `arccos(` to the display.\n"
        "\n"
        "The `arccos` function SHALL treat the angle as specified in either degrees or radians based on the currently selected `Rad|Deg` mode.\n"
        "\n"
        "The `arccos` function call SHALL return an `Error` for any argument larger than `1`\n"
        "or smaller than `-1`.\n"
        "\n"
        "The `arccos` function call with an empty value SHALL return an `Error`.\n"
        "\n"
        "The `arcsin()` SHALL handle `Infinity` as an argument value as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `arccos(Infinity)` | `Error` |\n"
        "| `arccos(-Infinity)` | `Error` |\n"
        "\n"
        "The result of the `arccos` operation when argument is an `Error` SHALL be `Error`.\n"
        "```\n"
        "arccos(.) = Error\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="13.5.1",
)

RQ_Google_Calculator_TrigonometricFunctions_Arctangent = Requirement(
    name="RQ.Google.Calculator.TrigonometricFunctions.Arctangent",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support calculating the value of the arctangent trigonometric function using the `Inv` `tan^-1` button that SHALL add `arctan(` to the display.\n"
        "\n"
        "The `arctan` function SHALL treat the angle as specified in either degrees or radians based on the currently selected `Rad|Deg` mode.\n"
        "\n"
        "The `arctan` function call with an empty value SHALL return an `Error`.\n"
        "\n"
        "The `arctan()` function SHALL handle `Infinity` as an argument value as follows:\n"
        "\n"
        "| Operation | Result |\n"
        "| --- | ---|\n"
        "| `arctan(Infinity)` | `90` |\n"
        "| `arcsin(-Infinity)` | `-90` |\n"
        "\n"
        "The result of the `arctan` operation when argument is an `Error` SHALL be `Error`.\n"
        "```\n"
        "arctan(.) = Error\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="13.6.1",
)

RQ_Google_Calculator_Constants_Pi = Requirement(
    name="RQ.Google.Calculator.Constants.Pi",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support entering the constant value of pi using the `π` button, which SHALL add `π` symbol to the display and be equivalent to `3.14159265359`.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="14.1.1",
)

RQ_Google_Calculator_Constants_EulersNumber = Requirement(
    name="RQ.Google.Calculator.Constants.EulersNumber",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support entering a constant Euler's number using the `e` button, which SHALL add `e` symbol to the display that SHALL be equivalent to `2.71828182846`.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="14.2.1",
)

RQ_Google_Calculator_RandomNumber = Requirement(
    name="RQ.Google.Calculator.RandomNumber",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support generating a random number from `0` to `1` using the `Inv` `Rnd` button that SHALL add the generated number to the display.\n"
        "\n"
        "If the current expression ends with a number, then the generated number is preceded by the multiplication `x` operation.\n"
        "\n"
    ),
    link=None,
    level=2,
    num="15.1",
)

RQ_Google_Calculator_Expressions_Groups = Requirement(
    name="RQ.Google.Calculator.Expressions.Groups",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support defining expression groups using left `(` and right `)` parenthesis buttons, and the corresponding character SHALL be displayed.\n"
        "\n"
        "An expression within the group SHALL be evaluated first, and nested groups SHALL be supported.\n"
        "\n"
        "Right `)` parenthesis SHALL only be allowed if there is a matching left `)` parenthesis open and the expression is not empty.\n"
        "\n"
        "Any number of missing right `)` parenthesis to close currently open groups SHALL be auto completed automatically on evaluation and SHALL not generate an `Error`.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="16.1.1",
)

RQ_Google_Calculator_Expressions_Complex = Requirement(
    name="RQ.Google.Calculator.Expressions.Complex",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support the evaluation of complex expressions that include multiple expression groups.\n"
        "\n"
        "For example,\n"
        "```\n"
        "(2 + 2) / ((1+2) * (sin(20)))\n"
        "```\n"
        "\n"
    ),
    link=None,
    level=3,
    num="16.2.1",
)

RQ_Google_Calculator_Expressions_OrderOfOperations = Requirement(
    name="RQ.Google.Calculator.Expressions.OrderOfOperations",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL execute the expression respecting the standard order of operations:\n"
        "\n"
        "* parentheses first\n"
        "* exponents (powers, square roots, etc.)\n"
        "* multiplication and division (left-to-right)\n"
        "* addition and subtraction (left-to-right)\n"
        "\n"
    ),
    link=None,
    level=3,
    num="16.3.1",
)

RQ_Google_Calculator_AnswerPrompt = Requirement(
    name="RQ.Google.Calculator.AnswerPrompt",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL support showing in the top right corner an answer prompt that display the expression that produced the last result.\n"
        "\n"
        "The last calculation expression SHALL be visually truncated if it does not fit the allocated display's width.\n"
        "\n"
        "For example,\n"
        "```\n"
        "2 + 2\n"
        "```\n"
        "\n"
        "![Answer Prompt](answer_prompt.png)\n"
        "\n"
    ),
    link=None,
    level=2,
    num="17.1",
)

RQ_Google_Calculator_History = Requirement(
    name="RQ.Google.Calculator.History",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator SHALL provide calculation history when the user clicks on the `🕑` button on the left top corner.\n"
        "\n"
        "![Calculation History](history.png)\n"
        "\n"
    ),
    link=None,
    level=2,
    num="18.1",
)

RQ_Google_Calculator_History_Result = Requirement(
    name="RQ.Google.Calculator.History.Result",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator history SHALL support clicking on the result of the previous calculation, and that result SHALL be added to the display.\n"
        "\n"
        "The `Error` result SHALL not be clickable.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="18.2.1",
)

RQ_Google_Calculator_History_Expression = Requirement(
    name="RQ.Google.Calculator.History.Expression",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator history SHALL support clicking on the calculation expression of the previous calculation, and that expression SHALL replace any content currently present on the display.\n"
        "\n"
        "The calculator history SHALL truncate very long expressions using the `...`.\n"
        "\n"
    ),
    link=None,
    level=3,
    num="18.3.1",
)

RQ_Google_Calculator_History_Order = Requirement(
    name="RQ.Google.Calculator.History.Order",
    version="1.0",
    priority=None,
    group=None,
    type=None,
    uid=None,
    description=(
        "The calculator's history SHALL add the last calculation to the bottom of the list.\n"
        "\n"
        "The calculator history SHALL open with the list scrolled to the bottom showing the most recent calculation.\n"
    ),
    link=None,
    level=3,
    num="18.4.1",
)

SRS001_Google_com_Calculator = Specification(
    name="SRS001 Google.com Calculator",
    description=None,
    author=None,
    date=None,
    status=None,
    approved_by=None,
    approved_date=None,
    approved_version=None,
    version=None,
    group=None,
    type=None,
    link=None,
    uid=None,
    parent=None,
    children=None,
    headings=(
        Heading(name="Introduction", level=1, num="1"),
        Heading(name="Opening The Calculator", level=1, num="2"),
        Heading(name="RQ.Google.Calculator.Open", level=2, num="2.1"),
        Heading(name="User Interface", level=1, num="3"),
        Heading(name="Normal View", level=2, num="3.1"),
        Heading(name="RQ.Google.Calculator.UI.NormalView", level=3, num="3.1.1"),
        Heading(name="Inverse View", level=2, num="3.2"),
        Heading(name="RQ.Google.Calculator.UI.InverseView", level=3, num="3.2.1"),
        Heading(name="Keyboard Input", level=2, num="3.3"),
        Heading(name="RQ.Google.Calculator.UI.KeyboardInput", level=3, num="3.3.1"),
        Heading(name="Mixed Input", level=2, num="3.4"),
        Heading(name="RQ.Google.Calculator.UI.MixedInput", level=3, num="3.4.1"),
        Heading(name="Entering Numbers", level=1, num="4"),
        Heading(name="Digits", level=2, num="4.1"),
        Heading(
            name="RQ.Google.Calculator.EnteringNumbers.Digits", level=3, num="4.1.1"
        ),
        Heading(name="Negative Numbers", level=2, num="4.2"),
        Heading(
            name="RQ.Google.Calculator.EnteringNumbers.Negative", level=3, num="4.2.1"
        ),
        Heading(name="Decimals", level=2, num="4.3"),
        Heading(
            name="RQ.Google.Calculator.EnteringNumbers.Decimal", level=3, num="4.3.1"
        ),
        Heading(name="Accuracy", level=3, num="4.3.2"),
        Heading(
            name="RQ.Google.Calculator.EnteringNumbers.Decimal.Accuracy",
            level=4,
            num="4.3.2.1",
        ),
        Heading(name="Infinity", level=1, num="5"),
        Heading(
            name="RQ.Google.Calculator.EnteringNumbers.Infinity", level=2, num="5.1"
        ),
        Heading(name="Positive Infinity", level=2, num="5.2"),
        Heading(
            name="RQ.Google.Calculator.EnteringNumbers.Infinity.Positive",
            level=3,
            num="5.2.1",
        ),
        Heading(name="Negative Infinity", level=2, num="5.3"),
        Heading(
            name="RQ.Google.Calculator.EnteringNumbers.Infinity.Negative",
            level=3,
            num="5.3.1",
        ),
        Heading(name="Limits", level=1, num="6"),
        Heading(name="Maximum Positive Number", level=2, num="6.1"),
        Heading(
            name="RQ.Google.Calculator.Limits.MaximumPositiveNumber",
            level=3,
            num="6.1.1",
        ),
        Heading(name="Maximum Negative Number", level=2, num="6.2"),
        Heading(
            name="RQ.Google.Calculator.Limits.MaximumNegativeNumber",
            level=3,
            num="6.2.1",
        ),
        Heading(name="Minimum Positive Number", level=2, num="6.3"),
        Heading(
            name="RQ.Google.Calculator.Limits.MinimumPositiveNumber",
            level=3,
            num="6.3.1",
        ),
        Heading(name="Minimum Negative Number", level=2, num="6.4"),
        Heading(
            name="RQ.Google.Calculator.Limits.MinimumNegativeNumber",
            level=3,
            num="6.4.1",
        ),
        Heading(name="Scientific Notation", level=2, num="6.5"),
        Heading(
            name="RQ.Google.Calculator.EnteringNumbers.ScientificNotation",
            level=3,
            num="6.5.1",
        ),
        Heading(name="Retrieving the Last Answer", level=1, num="7"),
        Heading(name="RQ.Google.Calculator.LastAnswer", level=2, num="7.1"),
        Heading(name="Switching Between Radians and Degrees", level=1, num="8"),
        Heading(
            name="RQ.Google.Calculator.SwitchingBetweenRadiansAndDegrees",
            level=2,
            num="8.1",
        ),
        Heading(name="Clearing Display", level=1, num="9"),
        Heading(name="Clear Entry", level=2, num="9.1"),
        Heading(
            name="RQ.Google.Calculator.ClearingDisplay.ClearEntry", level=3, num="9.1.1"
        ),
        Heading(name="Clear All", level=2, num="9.2"),
        Heading(
            name="RQ.Google.Calculator.ClearingDisplay.ClearAll", level=3, num="9.2.1"
        ),
        Heading(name="Calculating the Result", level=1, num="10"),
        Heading(name="RQ.Google.Calculator.CalculatingResult", level=2, num="10.1"),
        Heading(name="Arithmetic Operations", level=1, num="11"),
        Heading(name="Addition", level=2, num="11.1"),
        Heading(name="RQ.Google.Calculator.Addition", level=3, num="11.1.1"),
        Heading(name="Subtraction", level=2, num="11.2"),
        Heading(name="RQ.Google.Calculator.Subtraction", level=3, num="11.2.1"),
        Heading(name="Multiplication", level=2, num="11.3"),
        Heading(name="RQ.Google.Calculator.Multiplication", level=3, num="11.3.1"),
        Heading(name="Division", level=2, num="11.4"),
        Heading(name="RQ.Google.Calculator.Division", level=3, num="11.4.1"),
        Heading(name="Mathematical Operations", level=1, num="12"),
        Heading(name="Factorial", level=2, num="12.1"),
        Heading(
            name="RQ.Google.Calculator.Operations.Factorial", level=3, num="12.1.1"
        ),
        Heading(name="Square Root", level=2, num="12.2"),
        Heading(
            name="RQ.Google.Calculator.Operation.SquareRoot", level=3, num="12.2.1"
        ),
        Heading(name="Logarithm", level=2, num="12.3"),
        Heading(name="RQ.Google.Calculator.Operation.Logarithm", level=3, num="12.3.1"),
        Heading(name="Natural Logarithm", level=2, num="12.4"),
        Heading(
            name="RQ.Google.Calculator.Operation.NaturalLogarithm",
            level=3,
            num="12.4.1",
        ),
        Heading(name="Percentage", level=2, num="12.5"),
        Heading(name="RQ.Google.Calculator.Percentage", level=3, num="12.5.1"),
        Heading(name="X to the power of Y", level=2, num="12.6"),
        Heading(
            name="RQ.Google.Calculator.Operation.XToThePowerOfY", level=3, num="12.6.1"
        ),
        Heading(name="Euler's Number To The Power of X", level=2, num="12.7"),
        Heading(
            name="RQ.Google.Calculator.Operations.EToThePowerOfX", level=3, num="12.7.1"
        ),
        Heading(name="10 To The Power of X", level=2, num="12.8"),
        Heading(
            name="RQ.Google.Calculator.Operations.10ToThePowerOfX",
            level=3,
            num="12.8.1",
        ),
        Heading(name="X Squared", level=2, num="12.9"),
        Heading(name="RQ.Google.Calculator.Operations.XSquared", level=3, num="12.9.1"),
        Heading(name="Nth Root", level=2, num="12.10"),
        Heading(name="RQ.Google.Calculator.Operations.NthRoot", level=3, num="12.10.1"),
        Heading(name="Trigonometric Functions", level=1, num="13"),
        Heading(name="Sine", level=2, num="13.1"),
        Heading(
            name="RQ.Google.Calculator.TrigonometricFunctions.Sine",
            level=3,
            num="13.1.1",
        ),
        Heading(name="Cosine", level=2, num="13.2"),
        Heading(
            name="RQ.Google.Calculator.TrigonometricFunctions.Cosine",
            level=3,
            num="13.2.1",
        ),
        Heading(name="Tangent", level=2, num="13.3"),
        Heading(
            name="RQ.Google.Calculator.TrigonometricFunctions.Tangent",
            level=3,
            num="13.3.1",
        ),
        Heading(name="Arcsine", level=2, num="13.4"),
        Heading(
            name="RQ.Google.Calculator.TrigonometricFunctions.Arcsine",
            level=3,
            num="13.4.1",
        ),
        Heading(name="Arccosine", level=2, num="13.5"),
        Heading(
            name="RQ.Google.Calculator.TrigonometricFunctions.Arccosine",
            level=3,
            num="13.5.1",
        ),
        Heading(name="Arctangent", level=2, num="13.6"),
        Heading(
            name="RQ.Google.Calculator.TrigonometricFunctions.Arctangent",
            level=3,
            num="13.6.1",
        ),
        Heading(name="Mathematical Constants", level=1, num="14"),
        Heading(name="The pi value - π", level=2, num="14.1"),
        Heading(name="RQ.Google.Calculator.Constants.Pi", level=3, num="14.1.1"),
        Heading(name="Euler's number - e", level=2, num="14.2"),
        Heading(
            name="RQ.Google.Calculator.Constants.EulersNumber", level=3, num="14.2.1"
        ),
        Heading(name="Random Number", level=1, num="15"),
        Heading(name="RQ.Google.Calculator.RandomNumber", level=2, num="15.1"),
        Heading(name="Expressions", level=1, num="16"),
        Heading(name="Expression Groups", level=2, num="16.1"),
        Heading(name="RQ.Google.Calculator.Expressions.Groups", level=3, num="16.1.1"),
        Heading(name="Complex Expressions", level=2, num="16.2"),
        Heading(name="RQ.Google.Calculator.Expressions.Complex", level=3, num="16.2.1"),
        Heading(name="Order of Operations", level=2, num="16.3"),
        Heading(
            name="RQ.Google.Calculator.Expressions.OrderOfOperations",
            level=3,
            num="16.3.1",
        ),
        Heading(name="Answer Prompt", level=1, num="17"),
        Heading(name="RQ.Google.Calculator.AnswerPrompt", level=2, num="17.1"),
        Heading(name="Calculation History", level=1, num="18"),
        Heading(name="RQ.Google.Calculator.History", level=2, num="18.1"),
        Heading(name="History Result", level=2, num="18.2"),
        Heading(name="RQ.Google.Calculator.History.Result", level=3, num="18.2.1"),
        Heading(name="History Expression", level=2, num="18.3"),
        Heading(name="RQ.Google.Calculator.History.Expression", level=3, num="18.3.1"),
        Heading(name="History Order", level=2, num="18.4"),
        Heading(name="RQ.Google.Calculator.History.Order", level=3, num="18.4.1"),
    ),
    requirements=(
        RQ_Google_Calculator_Open,
        RQ_Google_Calculator_UI_NormalView,
        RQ_Google_Calculator_UI_InverseView,
        RQ_Google_Calculator_UI_KeyboardInput,
        RQ_Google_Calculator_UI_MixedInput,
        RQ_Google_Calculator_EnteringNumbers_Digits,
        RQ_Google_Calculator_EnteringNumbers_Negative,
        RQ_Google_Calculator_EnteringNumbers_Decimal,
        RQ_Google_Calculator_EnteringNumbers_Decimal_Accuracy,
        RQ_Google_Calculator_EnteringNumbers_Infinity,
        RQ_Google_Calculator_EnteringNumbers_Infinity_Positive,
        RQ_Google_Calculator_EnteringNumbers_Infinity_Negative,
        RQ_Google_Calculator_Limits_MaximumPositiveNumber,
        RQ_Google_Calculator_Limits_MaximumNegativeNumber,
        RQ_Google_Calculator_Limits_MinimumPositiveNumber,
        RQ_Google_Calculator_Limits_MinimumNegativeNumber,
        RQ_Google_Calculator_EnteringNumbers_ScientificNotation,
        RQ_Google_Calculator_LastAnswer,
        RQ_Google_Calculator_SwitchingBetweenRadiansAndDegrees,
        RQ_Google_Calculator_ClearingDisplay_ClearEntry,
        RQ_Google_Calculator_ClearingDisplay_ClearAll,
        RQ_Google_Calculator_CalculatingResult,
        RQ_Google_Calculator_Addition,
        RQ_Google_Calculator_Subtraction,
        RQ_Google_Calculator_Multiplication,
        RQ_Google_Calculator_Division,
        RQ_Google_Calculator_Operations_Factorial,
        RQ_Google_Calculator_Operation_SquareRoot,
        RQ_Google_Calculator_Operation_Logarithm,
        RQ_Google_Calculator_Operation_NaturalLogarithm,
        RQ_Google_Calculator_Percentage,
        RQ_Google_Calculator_Operation_XToThePowerOfY,
        RQ_Google_Calculator_Operations_EToThePowerOfX,
        RQ_Google_Calculator_Operations_10ToThePowerOfX,
        RQ_Google_Calculator_Operations_XSquared,
        RQ_Google_Calculator_Operations_NthRoot,
        RQ_Google_Calculator_TrigonometricFunctions_Sine,
        RQ_Google_Calculator_TrigonometricFunctions_Cosine,
        RQ_Google_Calculator_TrigonometricFunctions_Tangent,
        RQ_Google_Calculator_TrigonometricFunctions_Arcsine,
        RQ_Google_Calculator_TrigonometricFunctions_Arccosine,
        RQ_Google_Calculator_TrigonometricFunctions_Arctangent,
        RQ_Google_Calculator_Constants_Pi,
        RQ_Google_Calculator_Constants_EulersNumber,
        RQ_Google_Calculator_RandomNumber,
        RQ_Google_Calculator_Expressions_Groups,
        RQ_Google_Calculator_Expressions_Complex,
        RQ_Google_Calculator_Expressions_OrderOfOperations,
        RQ_Google_Calculator_AnswerPrompt,
        RQ_Google_Calculator_History,
        RQ_Google_Calculator_History_Result,
        RQ_Google_Calculator_History_Expression,
        RQ_Google_Calculator_History_Order,
    ),
    content="""
# SRS001 Google.com Calculator
# Software Requirements Specification

## Table of Contents

* 1 [Introduction](#introduction)
* 2 [Opening The Calculator](#opening-the-calculator)
    * 2.1 [RQ.Google.Calculator.Open](#rqgooglecalculatoropen)
* 3 [User Interface](#user-interface)
    * 3.1 [Normal View](#normal-view)
        * 3.1.1 [RQ.Google.Calculator.UI.NormalView](#rqgooglecalculatoruinormalview)
    * 3.2 [Inverse View](#inverse-view)
        * 3.2.1 [RQ.Google.Calculator.UI.InverseView](#rqgooglecalculatoruiinverseview)
    * 3.3 [Keyboard Input](#keyboard-input)
        * 3.3.1 [RQ.Google.Calculator.UI.KeyboardInput](#rqgooglecalculatoruikeyboardinput)
    * 3.4 [Mixed Input](#mixed-input)
        * 3.4.1 [RQ.Google.Calculator.UI.MixedInput](#rqgooglecalculatoruimixedinput)
* 4 [Entering Numbers](#entering-numbers)
    * 4.1 [Digits](#digits)
        * 4.1.1 [RQ.Google.Calculator.EnteringNumbers.Digits](#rqgooglecalculatorenteringnumbersdigits)
    * 4.2 [Negative Numbers](#negative-numbers)
        * 4.2.1 [RQ.Google.Calculator.EnteringNumbers.Negative](#rqgooglecalculatorenteringnumbersnegative)
    * 4.3 [Decimals](#decimals)
        * 4.3.1 [RQ.Google.Calculator.EnteringNumbers.Decimal](#rqgooglecalculatorenteringnumbersdecimal)
        * 4.3.2 [Accuracy](#accuracy)
            * 4.3.2.1 [RQ.Google.Calculator.EnteringNumbers.Decimal.Accuracy](#rqgooglecalculatorenteringnumbersdecimalaccuracy)
* 5 [Infinity](#infinity)
    * 5.1 [RQ.Google.Calculator.EnteringNumbers.Infinity](#rqgooglecalculatorenteringnumbersinfinity)
    * 5.2 [Positive Infinity](#positive-infinity)
        * 5.2.1 [RQ.Google.Calculator.EnteringNumbers.Infinity.Positive](#rqgooglecalculatorenteringnumbersinfinitypositive)
    * 5.3 [Negative Infinity](#negative-infinity)
        * 5.3.1 [RQ.Google.Calculator.EnteringNumbers.Infinity.Negative](#rqgooglecalculatorenteringnumbersinfinitynegative)
* 6 [Limits](#limits)
    * 6.1 [Maximum Positive Number](#maximum-positive-number)
        * 6.1.1 [RQ.Google.Calculator.Limits.MaximumPositiveNumber](#rqgooglecalculatorlimitsmaximumpositivenumber)
    * 6.2 [Maximum Negative Number](#maximum-negative-number)
        * 6.2.1 [RQ.Google.Calculator.Limits.MaximumNegativeNumber](#rqgooglecalculatorlimitsmaximumnegativenumber)
    * 6.3 [Minimum Positive Number](#minimum-positive-number)
        * 6.3.1 [RQ.Google.Calculator.Limits.MinimumPositiveNumber](#rqgooglecalculatorlimitsminimumpositivenumber)
    * 6.4 [Minimum Negative Number](#minimum-negative-number)
        * 6.4.1 [RQ.Google.Calculator.Limits.MinimumNegativeNumber](#rqgooglecalculatorlimitsminimumnegativenumber)
    * 6.5 [Scientific Notation](#scientific-notation)
        * 6.5.1 [RQ.Google.Calculator.EnteringNumbers.ScientificNotation](#rqgooglecalculatorenteringnumbersscientificnotation)
* 7 [Retrieving the Last Answer](#retrieving-the-last-answer)
    * 7.1 [RQ.Google.Calculator.LastAnswer](#rqgooglecalculatorlastanswer)
* 8 [Switching Between Radians and Degrees](#switching-between-radians-and-degrees)
    * 8.1 [RQ.Google.Calculator.SwitchingBetweenRadiansAndDegrees](#rqgooglecalculatorswitchingbetweenradiansanddegrees)
* 9 [Clearing Display](#clearing-display)
    * 9.1 [Clear Entry](#clear-entry)
        * 9.1.1 [RQ.Google.Calculator.ClearingDisplay.ClearEntry](#rqgooglecalculatorclearingdisplayclearentry)
    * 9.2 [Clear All](#clear-all)
        * 9.2.1 [RQ.Google.Calculator.ClearingDisplay.ClearAll](#rqgooglecalculatorclearingdisplayclearall)
* 10 [Calculating the Result](#calculating-the-result)
    * 10.1 [RQ.Google.Calculator.CalculatingResult](#rqgooglecalculatorcalculatingresult)
* 11 [Arithmetic Operations](#arithmetic-operations)
    * 11.1 [Addition](#addition)
        * 11.1.1 [RQ.Google.Calculator.Addition](#rqgooglecalculatoraddition)
    * 11.2 [Subtraction](#subtraction)
        * 11.2.1 [RQ.Google.Calculator.Subtraction](#rqgooglecalculatorsubtraction)
    * 11.3 [Multiplication](#multiplication)
        * 11.3.1 [RQ.Google.Calculator.Multiplication](#rqgooglecalculatormultiplication)
    * 11.4 [Division](#division)
        * 11.4.1 [RQ.Google.Calculator.Division](#rqgooglecalculatordivision)
* 12 [Mathematical Operations](#mathematical-operations)
    * 12.1 [Factorial](#factorial)
        * 12.1.1 [RQ.Google.Calculator.Operations.Factorial](#rqgooglecalculatoroperationsfactorial)
    * 12.2 [Square Root](#square-root)
        * 12.2.1 [RQ.Google.Calculator.Operation.SquareRoot](#rqgooglecalculatoroperationsquareroot)
    * 12.3 [Logarithm](#logarithm)
        * 12.3.1 [RQ.Google.Calculator.Operation.Logarithm](#rqgooglecalculatoroperationlogarithm)
    * 12.4 [Natural Logarithm](#natural-logarithm)
        * 12.4.1 [RQ.Google.Calculator.Operation.NaturalLogarithm](#rqgooglecalculatoroperationnaturallogarithm)
    * 12.5 [Percentage](#percentage)
        * 12.5.1 [RQ.Google.Calculator.Percentage](#rqgooglecalculatorpercentage)
    * 12.6 [X to the power of Y](#x-to-the-power-of-y)
        * 12.6.1 [RQ.Google.Calculator.Operation.XToThePowerOfY](#rqgooglecalculatoroperationxtothepowerofy)
    * 12.7 [Euler's Number To The Power of X](#eulers-number-to-the-power-of-x)
        * 12.7.1 [RQ.Google.Calculator.Operations.EToThePowerOfX](#rqgooglecalculatoroperationsetothepowerofx)
    * 12.8 [10 To The Power of X](#10-to-the-power-of-x)
        * 12.8.1 [RQ.Google.Calculator.Operations.10ToThePowerOfX](#rqgooglecalculatoroperations10tothepowerofx)
    * 12.9 [X Squared](#x-squared)
        * 12.9.1 [RQ.Google.Calculator.Operations.XSquared](#rqgooglecalculatoroperationsxsquared)
    * 12.10 [Nth Root](#nth-root)
        * 12.10.1 [RQ.Google.Calculator.Operations.NthRoot](#rqgooglecalculatoroperationsnthroot)
* 13 [Trigonometric Functions](#trigonometric-functions)
    * 13.1 [Sine](#sine)
        * 13.1.1 [RQ.Google.Calculator.TrigonometricFunctions.Sine](#rqgooglecalculatortrigonometricfunctionssine)
    * 13.2 [Cosine](#cosine)
        * 13.2.1 [RQ.Google.Calculator.TrigonometricFunctions.Cosine](#rqgooglecalculatortrigonometricfunctionscosine)
    * 13.3 [Tangent](#tangent)
        * 13.3.1 [RQ.Google.Calculator.TrigonometricFunctions.Tangent](#rqgooglecalculatortrigonometricfunctionstangent)
    * 13.4 [Arcsine](#arcsine)
        * 13.4.1 [RQ.Google.Calculator.TrigonometricFunctions.Arcsine](#rqgooglecalculatortrigonometricfunctionsarcsine)
    * 13.5 [Arccosine](#arccosine)
        * 13.5.1 [RQ.Google.Calculator.TrigonometricFunctions.Arccosine](#rqgooglecalculatortrigonometricfunctionsarccosine)
    * 13.6 [Arctangent](#arctangent)
        * 13.6.1 [RQ.Google.Calculator.TrigonometricFunctions.Arctangent](#rqgooglecalculatortrigonometricfunctionsarctangent)
* 14 [Mathematical Constants](#mathematical-constants)
    * 14.1 [The pi value - π](#the-pi-value---)
        * 14.1.1 [RQ.Google.Calculator.Constants.Pi](#rqgooglecalculatorconstantspi)
    * 14.2 [Euler's number - e](#eulers-number---e)
        * 14.2.1 [RQ.Google.Calculator.Constants.EulersNumber](#rqgooglecalculatorconstantseulersnumber)
* 15 [Random Number](#random-number)
    * 15.1 [RQ.Google.Calculator.RandomNumber](#rqgooglecalculatorrandomnumber)
* 16 [Expressions](#expressions)
    * 16.1 [Expression Groups](#expression-groups)
        * 16.1.1 [RQ.Google.Calculator.Expressions.Groups](#rqgooglecalculatorexpressionsgroups)
    * 16.2 [Complex Expressions](#complex-expressions)
        * 16.2.1 [RQ.Google.Calculator.Expressions.Complex](#rqgooglecalculatorexpressionscomplex)
    * 16.3 [Order of Operations](#order-of-operations)
        * 16.3.1 [RQ.Google.Calculator.Expressions.OrderOfOperations](#rqgooglecalculatorexpressionsorderofoperations)
* 17 [Answer Prompt](#answer-prompt)
    * 17.1 [RQ.Google.Calculator.AnswerPrompt](#rqgooglecalculatoranswerprompt)
* 18 [Calculation History](#calculation-history)
    * 18.1 [RQ.Google.Calculator.History](#rqgooglecalculatorhistory)
    * 18.2 [History Result](#history-result)
        * 18.2.1 [RQ.Google.Calculator.History.Result](#rqgooglecalculatorhistoryresult)
    * 18.3 [History Expression](#history-expression)
        * 18.3.1 [RQ.Google.Calculator.History.Expression](#rqgooglecalculatorhistoryexpression)
    * 18.4 [History Order](#history-order)
        * 18.4.1 [RQ.Google.Calculator.History.Order](#rqgooglecalculatorhistoryorder)

## Introduction

This software requirements specification covers requirements related to the functionality of the Google.com Calculator.

## Opening The Calculator

### RQ.Google.Calculator.Open
version: 1.0

The calculator SHALL open when the user searches for `calculator` or similar terms in the search box.

## User Interface

### Normal View

#### RQ.Google.Calculator.UI.NormalView
version: 1.0

The calculator SHALL have the following graphical user interface.

![Calculator](calculator.png)

### Inverse View

#### RQ.Google.Calculator.UI.InverseView
version: 1.0

The calculator SHALL have the following graphical user interface when `Inv` button is clicked.

![Calculator](inverse.png)

### Keyboard Input

#### RQ.Google.Calculator.UI.KeyboardInput
version: 1.0

The calculator SHALL support entering operations and numbers using keyboard.

| Keyboard Input | Description
| --- | --- |
| `0` | digit `0` |
| `1` | digit `1` |
| `2` | digit `2` |
| `3` | digit `3` |
| `4` | digit `4` |
| `5` | digit `5` |
| `6` | digit `6` |
| `7` | digit `7` |
| `8` | digit `8` |
| `9` | digit `9` |
| `+` | addition |
| `-` | subtraction |
| `*` | multiplication |
| `÷` | division |
| `BACKSPACE` | clear (AC/CE) |
| `%` | percentage |
| `(` | left parenthesis |
| `)` | right parenthesis |
| `.` | decimal point |
| `=` | calculate result |
| `ENTER` | calculate result |
| `!` | factorial |
| `s` | sin() |
| `c` | cos() |
| `t` | tan() |
| `S` | arcsin() |
| `C` | arccos() |
| `T` | arctan() |
| `l`, `L` | ln() |
| `g`, `G` | log() |
| `p`, `P` | π constant |
| `e` | Euler's number e |
| `E` | scientific notation `10E3` |
| `q`, `Q` | `√()` square root |
| `a`, `A` | `Ans` answer |
| `^` | <code>x<sup>y</sup></code> x to the power of y |
| `R` | `Rnd` random number |
| `r` | <code><sup>y</sup>√x</code> |

### Mixed Input

#### RQ.Google.Calculator.UI.MixedInput
version: 1.0

The calculator SHALL support entering operations using keyboard and buttons mixed input for the same expression.

## Entering Numbers

### Digits

#### RQ.Google.Calculator.EnteringNumbers.Digits
version: 1.0

The calculator SHALL support entering number digits using `0`-`9` buttons, and the digits SHALL be added to the display.

### Negative Numbers

#### RQ.Google.Calculator.EnteringNumbers.Negative
version: 1.0

The `-` button SHALL allow defining negative numbers.

For example,
```
-2.0
2*-1
(-3
1-.2
```

### Decimals

#### RQ.Google.Calculator.EnteringNumbers.Decimal
version: 1.0

The calculator SHALL support entering decimal numbers using the `.` button to add the decimal point.

The calculator SHALL not allow entering numbers with multiple decimal points.

The `.` SHALL return an `Error`.

The calculator SHALL allow omitting `0` before the `.`. For example,
```
-.2 = 0.2
```

#### Accuracy

##### RQ.Google.Calculator.EnteringNumbers.Decimal.Accuracy
version: 1.0

The calculator SHALL display decimal numbers to the 11th place after the decimal point.

```
0.12345678901
```

## Infinity

### RQ.Google.Calculator.EnteringNumbers.Infinity
version: 1.0

The calculator SHALL support handling positive `Infinity` and negative `-Infinity`.

### Positive Infinity

#### RQ.Google.Calculator.EnteringNumbers.Infinity.Positive
version: 1.0

Any number larger than the maximum positive number SHALL be treated as a positive `Infinity`.

### Negative Infinity

#### RQ.Google.Calculator.EnteringNumbers.Infinity.Negative
version: 1.0

Any number smaller than the maximum negative number SHALL be treated as negative `Infinity`.

## Limits

### Maximum Positive Number

#### RQ.Google.Calculator.Limits.MaximumPositiveNumber
version: 1.0

The calculator SHALL support the maximum positive number `1.7976931348623157e+308` (<code>2<sup>1024</sup>-1</code>).

### Maximum Negative Number

#### RQ.Google.Calculator.Limits.MaximumNegativeNumber
version: 1.0

The calculator SHALL support the maximum negative number of `-1.7976931348623157e+308` (<code>-2<sup>1024</sup>-1</code>).

### Minimum Positive Number

#### RQ.Google.Calculator.Limits.MinimumPositiveNumber
version: 1.0

The calculator SHALL support the minimum positive number of `5E-324`.

Any number that is smaller SHALL be treated as `0`.

```
5E-324/2 = 0
1E-324 = 0
2E-324 = 0
```

### Minimum Negative Number

#### RQ.Google.Calculator.Limits.MinimumNegativeNumber
version: 1.0

The calculator SHALL support the minimum positive number of `-5E-324`.

Any number that is smaller SHALL be treated as `0`.

```
-5E-324/2 = 0
-1E-324 = 0
-2E-324 = 0
```

### Scientific Notation

#### RQ.Google.Calculator.EnteringNumbers.ScientificNotation
version: 1.0

The calculator SHALL support entering numbers in scientific notation using the `EXP` button that SHALL add the `E` to the display.
The `E` SHALL be equivalent to the <code>x 10<sup>x</sup></code> where `x` is the number that follows the `E`.

For example,

```
1E2 = 100
```

## Retrieving the Last Answer

### RQ.Google.Calculator.LastAnswer
version: 1.0

The calculator SHALL support retrieving the last non-`Error` answer using the `ANS` button that SHALL add the `Ans` to the display.

For example,
```
1 x Ans
```

The value of `Ans` by default SHALL be `0`.
```
Ans = 0
```

A multiplication operation SHALL be assumed if there is a current expression. For example,
```
5Ans
```

## Switching Between Radians and Degrees

### RQ.Google.Calculator.SwitchingBetweenRadiansAndDegrees
version: 1.0

The calculator SHALL support specifying angles for the trigonometric functions either in radians or degrees.

The user SHALL be able to switch between them using the `Rad | Deg` button, where the`Rad` SHALL set the radians mode and `Deg` SHALL set the degrees mode.

The default mode SHALL be `Deg`.

## Clearing Display

### Clear Entry

#### RQ.Google.Calculator.ClearingDisplay.ClearEntry
version: 1.0

The calculator SHALL support clearing the last entry using the `CE` button, which SHALL remove the current last character or operator from the display.

If there are no characters or operators left to remove, then `0` SHALL be displayed.

### Clear All

#### RQ.Google.Calculator.ClearingDisplay.ClearAll
version: 1.0

The calculator SHALL support clearing the last result using the `AC` button, which SHALL remove the result of the last expression from the display and display SHALL be set to `0`.

## Calculating the Result

### RQ.Google.Calculator.CalculatingResult
version: 1.0

The calculator SHALL calculate the result of the current expression using the `=` button, which SHALL cause the display to be cleared and show the result of the calculation if and only if the expression is complete.

The evaluation of a complete expression SHALL result in the following:

1. The answer prompt SHALL be set to the expression that was evaluated.

2. The calculation history SHALL be updated to contain the last evaluated expression.

3. The value of `Ans` SHALL be set to the result value.

## Arithmetic Operations

### Addition

#### RQ.Google.Calculator.Addition
version: 1.0

The calculator SHALL support adding integers and decimal numbers using the `+` button, which SHALL add the addition operator to the display.

For example,

```
2 + 2
-9 + 4
2.3 + 1.33
```

The `+` operator SHALL handle `Infinity` as one of its arguments as follows:

| Operation | Result |
| --- | ---|
| `Infinity` + X | `Infinity`  |
| `-Infinity` + X | `-Infinity` |
| `Infinity` + `Infinity` | `Infinity` |
| `Infinity` - `Infinity` | `Error` |

The result of the addition operation when either argument is an `Error` SHALL be `Error`.

| Operation | Result |
| --- | --- |
| 1 + . | `Error` |
| . + . | `Error` |

An incomplete expression SHALL not be evaluated.
```
1 + = 1 +
```

Clicking `+` button SHALL be ignored when the expression does not contain a left argument.
```
(+
```

Incomplete `+` operation SHALL be overwritable by the following operators:

| Operator | Description |
| --- | --- |
| `*` | multiplication |
| `-` | subtraction |
| `/` | division |
| `!` | factorial |
| <code>x<sup>2</sup></code> | X squared |
| <code>x<sup>y</sup></code> | X to the power of Y |
| `y√x` | nth root |

For example,
```
2+- = 2-
```

### Subtraction

#### RQ.Google.Calculator.Subtraction
version: 1.0

The calculator SHALL support subtracting integers and decimal numbers using the `-` button that SHALL add the `-` operation to the display.

For example,
```
2.0 - 2
-9 - 4
```

The `-` operator SHALL handle `Infinity` as one of its arguments as follows:

| Operation | Result |
| --- | ---|
| `Infinity` - X | `Infinity`  |
| X - `Infinity` | `-Infinity` |
| `-Infinity` - X | `-Infinity` |
| `Infinity` - `Infinity` | `Error` |
| `-Infinity` - `Infinity` | `-Infinity` |

The result of the subtraction operation when either argument is an `Error` SHALL be `Error`.
For example,

| Operation | Result |
| --- | --- |
| 1 - . | `Error` |
| . - . | `Error` |

An incomplete expression SHALL not be evaluated.
```
1 -
2 * -
```

An incomplete `-` operation, when `-` is not treated as being used to define a negative number, SHALL be overwritable by the following operators:

| Operator | Description |
| --- | --- |
| `+` | addition |
| `*` | multiplication |
| `/` | division |
| `!` | factorial |
| <code>x<sup>2</sup></code> | X squared |
| <code>x<sup>y</sup></code> | X to the power of Y |
| `y√x` | nth root |

For example,
```
2-+ = 2+
```

### Multiplication

#### RQ.Google.Calculator.Multiplication
version: 1.0

The calculator SHALL support multiplication of integers and decimal numbers using the `×` button, which SHALL add the multiplication operator to the display.

```
-9 × 4
2.3 × 1.33
```

The `×` operator SHALL handle `Infinity` as one of its arguments as follows:

| Operation | Result |
| --- | ---|
| `Infinity` × X | `Infinity`  |
| `-Infinity` × X | `-Infinity` |
| `Infinity` × `Infinity` | `Infinity` |
| `-Infinity` × `Infinity` | `-Infinity` |

The result of the `×` operation when either argument is an `Error` SHALL be `Error`.

| Operation | Result |
| --- | --- |
| 1 × . | `Error` |
| . × . | `Error` |

An incomplete expression SHALL not be evaluated.
```
1 ×
```

Clicking `×` button SHALL be ignored when the expression does not contain a left argument.
```
(×
```

Incomplete `×` operation SHALL be overwritable by the following operators:

| Operator | Description |
| --- | --- |
| `+` | addition |
| `÷` | division |
| `!` | factorial |
| <code>x<sup>2</sup></code> | X squared |
| <code>x<sup>y</sup></code> | X to the power of Y |
| `y√x` | nth root |

For example,
```
2×+ = 2 +
```

### Division

#### RQ.Google.Calculator.Division
version: 1.0

The calculator SHALL support division of integers and decimal numbers using the `÷` button that SHALL add the `÷` operator to the display.

```
2 ÷ 2
2.3 ÷ 1.33
```

Division of positive number by `0` SHALL return `Infinity`.

Division of negative number by `0` SHALL return `-Infinity`.

`0 ÷ 0` SHALL return an `Error`.

The `÷` operator SHALL handle `Infinity` as one of its arguments as follows:

| Operation | Result |
| --- | ---|
| `Infinity` ÷ X | `Infinity`  |
| `-Infinity` ÷ X | `-Infinity` |
| X ÷ `Infinity` | `0` |
| X ÷ `-Infinity` | `0` |
| `Infinity` ÷ `Infinity` | `Error` |
| `-Infinity` ÷ `Infinity` | `Error` |

The result of the `÷` operation when either argument is an `Error` SHALL be `Error`.

| Operation | Result |
| --- | --- |
| 1 ÷ . | `Error` |
| . ÷ . | `Error` |

An incomplete expression SHALL not be evaluated.
```
1 ÷
```

Clicking `÷` button SHALL be ignored when the expression does not contain a left argument.
```
(÷
```

Incomplete `÷` operation SHALL be overwritable by the following operators:

| Operator | Description |
| --- | --- |
| `+` | addition |
| `×` | multiplication |
| `!` | factorial |
| <code>x<sup>2</sup></code> | X squared |
| <code>x<sup>y</sup></code> | X to the power of Y |
| `y√x` | nth root |

For example,
```
2÷+ = 2 +
```

## Mathematical Operations

### Factorial

#### RQ.Google.Calculator.Operations.Factorial
version: 1.0

The calculator SHALL support factorial operation using the `x!` button that SHALL add the `!` symbol to the display.

The factorial operation SHALL be defined as
```
n! = n × (n - 1)!
```

The `0!` SHALL be 1.

The factorial of a negative integer number SHALL be an `Error`.
```
(-4)! = Error
```

The factorial SHALL support positive and negative decimal numbers.
```
3.5! = 11.6317283966
(-0.1)! = 1.06862870212
```

The negative of factorial expression SHALL be the negative of the factorial of the positive number.

```
-4! = -(4!) = -24
```

The maximum factorial that can be calculated SHALL be `170!`.
```
170! = 7.257416e+306
```

The factorial SHALL handle `Infinity` as follows:

| Operation | Result |
| --- | ---|
| `Infinity`! | `Infinity`  |
| `-Infinity`! | `-Infinity` |
| `(-Infinity)`! | `Error` |

The result of the factorial operation when argument is an `Error` SHALL be `Error`.
```
 .! =  Error
```

Clicking `!` button SHALL be ignored when the expression does not contain a left argument.
```
(!
```

The factorial operation SHALL not be overwritable.
```
2!+ = 2! +
```

### Square Root

#### RQ.Google.Calculator.Operation.SquareRoot
version: 1.0

The calculator SHALL support square root operation using the `√` button that SHALL add the `√(`  to the display.
```
√(4)
```

The `√` of a negative number SHALL return an `Error`.
```
√(-1)
```

The `√()` with no arguments SHALL return an `Error`.
```
√()
```

The `√()` SHALL handle `Infinity` as one of its arguments as follows:

| Operation | Result |
| --- | ---|
| `√`(`Infinity`) | `Infinity`  |
| `√`(`-Infinity`) | `Error` |

The result of the `√()` operation when argument is an `Error` SHALL be `Error`.
```
√(.) =  Error
```

The `√(` operation SHALL not be overwritable.
```
√(+
```

### Logarithm

#### RQ.Google.Calculator.Operation.Logarithm
version: 1.0

The calculator SHALL support Logarithm operation using the `log` button that SHALL add the `log(`  to the display.

```
log(4)
```

The `log` of a negative number SHALL return an `Error`.
```
log(-5)
```

The `log` of `0` SHALL return `-Infinity`.
```
log(0)
```

The `log()` with no arguments SHALL return an `Error`.
```
log()
```

The `log()` function SHALL handle `Infinity` as one of its arguments as follows:

| Operation | Result |
| --- | ---|
| `log`(`Infinity`) | `Infinity`  |
| `log`(`-Infinity`) | `Error` |

The result of the `log()` operation when the argument is an `Error` SHALL be `Error`.
```
log(.) =  Error
```

The `log(` operation SHALL not be overwritable.
```
log(+
```

### Natural Logarithm

#### RQ.Google.Calculator.Operation.NaturalLogarithm
version: 1.0

The calculator SHALL support natural logarithm operation using the `ln` button that SHALL add the `ln(`  to the display.

```
ln(6)
```

The `ln` of a negative number SHALL return an `Error`.
```
ln(-6)
```

The `ln` of `0` SHALL return `-Infinity`.
```
ln(0)
```

The `ln()` with no arguments SHALL return an `Error`.
```
ln()
```

The `ln()` function SHALL handle `Infinity` as one of its arguments as follows:

| Operation | Result |
| --- | ---|
| `ln`(`Infinity`) | `Infinity`  |
| `ln`(`-Infinity`) | `Error` |

The result of the `ln()` operation when argument is an `Error` SHALL be `Error`.
```
ln(.) =  Error
```

The `ln(` operation SHALL not be overwritable.
```
ln(+
```

### Percentage

#### RQ.Google.Calculator.Percentage
version: 1.0

The calculator SHALL support specifying percentage using the `%` button, which SHALL add the `%`  operator to the display right after any last number or expression and be equivalent to `/100`.

```
5% + 2
```

If the display is empty when the user enters the `%` operation, then `0%` SHALL be displayed.

The `-%` SHALL return an `Error`.

The `.%` SHALL return an `Error`.

The `Infinity%` SHALL return `Infinity`.

The `-Infinity%` SHALL return `-Infinity`.

The `%` is not valid when entering an argument to any function if it is not preceded by the number, and therefore using `%` button SHALL result in no changes to the current expression.

The `%` SHALL not be overwritable.
```
2%+
```

### X to the power of Y

#### RQ.Google.Calculator.Operation.XToThePowerOfY
version: 1.0

The calculator SHALL support `x` to the power of `y` operation using the <code>x<sup>y</sup></code> button that SHALL add the <code><sup>□</sup></code> to the display.
The next expression entered SHALL specify the exponent `y`.

<code>2<sup>3</sup></code>

If `x` is`-0` and `y` exponent is negative, then the result SHALL be `-Infinity`.

<code>-0<sup>-3</sup></code>

The <code>x<sup>y</sup></code> SHALL handle `Infinity` as the Y exponent as follows:

| Operation | Result |
| --- | ---|
| <code>x<sup>Infinity</sup></code> | `Error`  |
| <code>x<sup>-Infinity</sup></code> | `0` |

The result of the <code>x<sup>y</sup></code> operation when exponent expression is an `Error` SHALL be `Error`.

An incomplete expression SHALL not be evaluated.

<code>2<sup>□</sup></code>

Clicking <code>x<sup>y</sup></code>  button SHALL be ignored when the expression does not contain a left argument.

<code>(x<sup>□</sup></code>

Incomplete <code>x<sup>y</sup></code> operation SHALL be overwritable by the following operators:

| Operator | Description |
| --- | --- |
| `+` | addition |
| `×` | multiplication |
| `÷` | division |
| `!` | factorial |
| <code>x<sup>2</sup></code> | X squared |
| `y√x` | nth root |

<code>2<sup>□</sup>+ = 2 +</code>

### Euler's Number To The Power of X

#### RQ.Google.Calculator.Operations.EToThePowerOfX
version: 1.0

The calculator SHALL support Euler's number, `e`, to the power of `x` operation using the `Inv` <code>e<sup>x</sup></code> button that SHALL add the <code>e<sup>□</sup></code> to the display. The next expression entered SHALL specify the exponent `x`.

<code>e<sup>2</sup></code>

The <code>e<sup>x</sup></code> SHALL handle `Infinity` as the X exponent as follows:

| Operation | Result |
| --- | ---|
| <code>e<sup>Infinity</sup></code> | `Infinity`  |
| <code>e<sup>-Infinity</sup></code> | `0` |

The result of the <code>e<sup>x</sup></code> operation when exponent expression is an `Error` SHALL be `Error`.

An incomplete expression SHALL not be evaluated.

<code>e<sup>□</sup></code>

Incomplete <code>e<sup>x</sup></code> operation SHALL not be overwritable.

The <code>x<sup>2</sup></code> SHALL set the `x` exponent to `2` if `x` was not specified.

### 10 To The Power of X

#### RQ.Google.Calculator.Operations.10ToThePowerOfX
version: 1.0

The calculator SHALL support ten to the power of `x` operation using the `Inv` <code>10<sup>x</sup></code> button that SHALL add the <code>10<sup>□</sup></code> to the display.
The next expression entered SHALL specify the exponent value of `x`.
The multiplication operation SHALL be added if the current expression is non empty before the <code>10<sup>□</sup></code>.

For example,

<code>10<sup>□</sup></code>
<code>0 x 10<sup>□</sup></code>

The <code>10<sup>x</sup></code> SHALL handle `Infinity` as the X exponent as follows:

| Operation | Result |
| --- | ---|
| <code>10<sup>Infinity</sup></code> | `Infinity`  |
| <code>10<sup>-Infinity</sup></code> | `0` |

The result of the <code>10<sup>x</sup></code> operation when the exponent expression is an `Error` SHALL be `Error`.

Incomplete expression SHALL not be evaluated.

<code>10<sup>□</sup></code>

An incomplete <code>10<sup>x</sup></code> operation SHALL not be overwritable.

The <code>x<sup>2</sup></code> SHALL set the `x` exponent to `2` if `x` was not specified.

### X Squared

#### RQ.Google.Calculator.Operations.XSquared
version: 1.0

The calculator SHALL support calculating the square value using the `Inv` <code>x<sup>2</sup></code> button.
If the display is empty, then it SHALL add <code>0<sup>2</sup></code> to the display.

<code>2<sup>2</sup></code>

The <code>x<sup>2</sup></code> SHALL handle `Infinity` as the value to be squared as follows:

| Operation | Result |
| --- | ---|
| <code>Infinity<sup>2</sup></code> | `Infinity`  |
| <code>-Infinity<sup>2</sup></code> | `Infinity` |

The result of the <code>x<sup>2</sup></code> operation when the exponent expression is an `Error` SHALL be `Error`.

An incomplete expression SHALL not be evaluated.

<code>2<sup>□</sup></code>

Incomplete <code>x<sup>2</sup></code> operation SHALL not be overwritable.

Clicking <code>x<sup>2</sup></code>  button SHALL be ignored when the expression does not contain a left argument.

<code>(x<sup>□</sup></code>

### Nth Root

#### RQ.Google.Calculator.Operations.NthRoot
version: 1.0

The calculator SHALL support calculating the value of N<sup>th</sup> root using the `Inv` <code><sup>y</sup>√x</code> button.
If the display is empty then the <code><sup>□</sup>√0</code> to the display.

If `x` is`-0` and `y` is negative, then the result SHALL be `-Infinity`.

For example,
```
-1√-0
```

The <code>x<sup>2</sup></code> SHALL handle `Infinity` as the value to be squared as follows:

| Operation | Result |
| --- | ---|
| <code><sup>Infinity</sup>√x</code> | `1` |
| <code><sup>-Infinity</sup>√x</code> | `1` |
| <code><sup>y</sup>√Infinity</code> | `Infinity` |
| <code><sup>y</sup>√-Infinity</code> | `-Infinity` |
| <code><sup>Infinity</sup>√Infinity</code> | `1` |
| <code><sup>-Infinity</sup>√Infinity</code> | `1` |
| <code><sup>Infinity</sup>√-Infinity</code> | `1` |
| <code><sup>-Infinity</sup>√-Infinity</code> | `1` |

The result of the <code><sup>y</sup>√x</code> operation when either `x` or `y` is an `Error` SHALL be `Error`.

An incomplete expression SHALL not be evaluated.

<code><sup>□</sup>√2</code>

Incomplete <code><sup>y</sup>√x</code> operation SHALL not be overwritable.

Clicking <code><sup>y</sup>√x</code>  button SHALL be ignored when the expression does not contain a left argument.

<code>(<sup>□</sup>√x</code>

## Trigonometric Functions

### Sine

#### RQ.Google.Calculator.TrigonometricFunctions.Sine
version: 1.0

The calculator SHALL support calculating the value of sine the trigonometric function using the `sin` button that SHALL add `sin(` to the display.

The `sin` function SHALL treat the angle as specified in either degrees or radians based on the currently selected `Rad|Deg` mode.

The `sin` function call with an empty value SHALL return an `Error`.

The `sin()` SHALL handle `Infinity` as an argument value as follows:

| Operation | Result |
| --- | ---|
| `sin(Infinity)` | `Error` |
| `sin(-Infinity)` | `Error` |

The result of the `sin` operation when argument is an `Error` SHALL be `Error`.
```
sin(.) = Error
```

### Cosine

#### RQ.Google.Calculator.TrigonometricFunctions.Cosine
version: 1.0

The calculator SHALL support calculating the value of the cosine trigonometric function using the `cos` button that SHALL add `cos(` to the display.

The `cos` function SHALL treat the angle as specified in either degrees or radians based on the currently selected `Rad|Deg` mode.

The `cos` function call with an empty value SHALL return an `Error`.

The `cos()` function SHALL handle `Infinity` as an argument value as follows:

| Operation | Result |
| --- | ---|
| `cos(Infinity)` | `Error` |
| `cos(-Infinity)` | `Error` |

The result of the `cos` operation when argument is an `Error` SHALL be `Error`.
```
cos(.) = Error
```

### Tangent

#### RQ.Google.Calculator.TrigonometricFunctions.Tangent
version: 1.0

The calculator SHALL support calculating the value of the tangent trigonometric function using the `tan` button that SHALL add `tan(` to the display.

The `tan` function SHALL treat the angle as specified in either degrees or radians based on the currently selected `Rad|Deg` mode.

The `tan` function call with an empty value SHALL return an `Error`.

The `tan()` function SHALL handle `Infinity` as an argument value as follows:

| Operation | Result |
| --- | ---|
| `tan(Infinity)` | `Error` |
| `cos(-Infinity)` | `Error` |

The result of the `tan` operation when argument is an `Error` SHALL be `Error`.
```
tan(.) = Error
```

### Arcsine

#### RQ.Google.Calculator.TrigonometricFunctions.Arcsine
version: 1.0

The calculator SHALL support calculating the value of the arcsine trigonometric function using the `Inv` `sin^-1` button that SHALL add `arcsin(` to the display.

The `arcsin` function SHALL treat the angle as specified in either degrees or radians based on the currently selected `Rad|Deg` mode.

The `arcsin` function call SHALL return an `Error` for any argument larger than `1`
or smaller than `-1`.

The `arcsin` function call with an empty value SHALL return an `Error`.

The `arcsin()` function SHALL handle `Infinity` as an argument value as follows:

| Operation | Result |
| --- | ---|
| `arcsin(Infinity)` | `Error` |
| `arcsin(-Infinity)` | `Error` |

The result of the `arcsin` operation when argument is an `Error` SHALL be `Error`.
```
arcsin(.) = Error
```

### Arccosine

#### RQ.Google.Calculator.TrigonometricFunctions.Arccosine
version: 1.0

The calculator SHALL support calculating the value of the arccosine trigonometric function using the `Inv` `cos^-1` button that SHALL add `arccos(` to the display.

The `arccos` function SHALL treat the angle as specified in either degrees or radians based on the currently selected `Rad|Deg` mode.

The `arccos` function call SHALL return an `Error` for any argument larger than `1`
or smaller than `-1`.

The `arccos` function call with an empty value SHALL return an `Error`.

The `arcsin()` SHALL handle `Infinity` as an argument value as follows:

| Operation | Result |
| --- | ---|
| `arccos(Infinity)` | `Error` |
| `arccos(-Infinity)` | `Error` |

The result of the `arccos` operation when argument is an `Error` SHALL be `Error`.
```
arccos(.) = Error
```

### Arctangent

#### RQ.Google.Calculator.TrigonometricFunctions.Arctangent
version: 1.0

The calculator SHALL support calculating the value of the arctangent trigonometric function using the `Inv` `tan^-1` button that SHALL add `arctan(` to the display.

The `arctan` function SHALL treat the angle as specified in either degrees or radians based on the currently selected `Rad|Deg` mode.

The `arctan` function call with an empty value SHALL return an `Error`.

The `arctan()` function SHALL handle `Infinity` as an argument value as follows:

| Operation | Result |
| --- | ---|
| `arctan(Infinity)` | `90` |
| `arcsin(-Infinity)` | `-90` |

The result of the `arctan` operation when argument is an `Error` SHALL be `Error`.
```
arctan(.) = Error
```

## Mathematical Constants

### The pi value - π

#### RQ.Google.Calculator.Constants.Pi
version: 1.0

The calculator SHALL support entering the constant value of pi using the `π` button, which SHALL add `π` symbol to the display and be equivalent to `3.14159265359`.

### Euler's number - e

#### RQ.Google.Calculator.Constants.EulersNumber
version: 1.0

The calculator SHALL support entering a constant Euler's number using the `e` button, which SHALL add `e` symbol to the display that SHALL be equivalent to `2.71828182846`.

## Random Number

### RQ.Google.Calculator.RandomNumber
version: 1.0

The calculator SHALL support generating a random number from `0` to `1` using the `Inv` `Rnd` button that SHALL add the generated number to the display.

If the current expression ends with a number, then the generated number is preceded by the multiplication `x` operation.

## Expressions

### Expression Groups

#### RQ.Google.Calculator.Expressions.Groups
version: 1.0

The calculator SHALL support defining expression groups using left `(` and right `)` parenthesis buttons, and the corresponding character SHALL be displayed.

An expression within the group SHALL be evaluated first, and nested groups SHALL be supported.

Right `)` parenthesis SHALL only be allowed if there is a matching left `)` parenthesis open and the expression is not empty.

Any number of missing right `)` parenthesis to close currently open groups SHALL be auto completed automatically on evaluation and SHALL not generate an `Error`.

### Complex Expressions

#### RQ.Google.Calculator.Expressions.Complex
version: 1.0

The calculator SHALL support the evaluation of complex expressions that include multiple expression groups.

For example,
```
(2 + 2) / ((1+2) * (sin(20)))
```

### Order of Operations

#### RQ.Google.Calculator.Expressions.OrderOfOperations
version: 1.0

The calculator SHALL execute the expression respecting the standard order of operations:

* parentheses first
* exponents (powers, square roots, etc.)
* multiplication and division (left-to-right)
* addition and subtraction (left-to-right)

## Answer Prompt

### RQ.Google.Calculator.AnswerPrompt
version: 1.0

The calculator SHALL support showing in the top right corner an answer prompt that display the expression that produced the last result.

The last calculation expression SHALL be visually truncated if it does not fit the allocated display's width.

For example,
```
2 + 2
```

![Answer Prompt](answer_prompt.png)

## Calculation History

### RQ.Google.Calculator.History
version: 1.0

The calculator SHALL provide calculation history when the user clicks on the `🕑` button on the left top corner.

![Calculation History](history.png)

### History Result

#### RQ.Google.Calculator.History.Result
version: 1.0

The calculator history SHALL support clicking on the result of the previous calculation, and that result SHALL be added to the display.

The `Error` result SHALL not be clickable.

### History Expression

#### RQ.Google.Calculator.History.Expression
version: 1.0

The calculator history SHALL support clicking on the calculation expression of the previous calculation, and that expression SHALL replace any content currently present on the display.

The calculator history SHALL truncate very long expressions using the `...`.

### History Order

#### RQ.Google.Calculator.History.Order
version: 1.0

The calculator's history SHALL add the last calculation to the bottom of the list.

The calculator history SHALL open with the list scrolled to the bottom showing the most recent calculation.
""",
)
