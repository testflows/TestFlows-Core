from testflows.core import *

## Press keys
@TestStep
def pressing_0():
    note("pressing: 0")

@TestStep
def pressing_1():
    note("pressing: 1")

@TestStep
def pressing_2():
    note("pressing: 2")

@TestStep
def pressing_3():
    note("pressing: 3")

@TestStep
def pressing_4():
    note("pressing: 4")

@TestStep
def pressing_5():
    note("pressing: 5")

@TestStep
def pressing_6():
    note("pressing: 6")

@TestStep
def pressing_7():
    note("pressing: 7")

@TestStep
def pressing_8():
    note("pressing: 8")

@TestStep
def pressing_9():
    note("pressing: 9")

@TestStep
def pressing_negative():
    note("pressing: negative")

@TestStep
def pressing_addition():
    note("pressing: +")

@TestStep
def pressing_substract():
    note("pressing: -")

@TestStep
def pressing_divide():
    note("pressing: /")

@TestStep
def pressing_multiply():
    note("pressing: *")

@TestStep
def pressing_equal():
    note("pressing: =")

@TestStep
def entering_number(num=None):
    if num is not None:
        if num < 0:
            And(pressing_negative)
            num = abs(num)
        for digit in str(num):
            And(globals().get(f"pressing_{digit}"))
    else:
        raise NotImplementedError

@TestStep
def entering_operation(op=None):
    if op is not None:
        if op == "+":
            By(pressing_addition)
        elif op == "-":
            By(pressing_substract)
        elif op == "*":
            By(pressing_multiply)
        elif op == "/":
            By(pressing_devide)
        else:
            raise ValueError(f"invalid operation {op}")
    else:
        raise NotImplementedError

@TestStep
def entering_equal():
    By(pressing_equal)

@TestStep
def checking_result(expected=None):
    if expected is not None:
        assert expected == expected, error()
    else:
        raise NotImplementedError

## build a map
pressing_number_keys = [
    pressing_0,
    pressing_1,
    pressing_2,
    pressing_3,
    pressing_4,
    pressing_5,
    pressing_6,
    pressing_7,
    pressing_8,
    pressing_9,
]

pressing_operation_keys = [
    pressing_addition,
    pressing_substract,
    pressing_multiply,
    pressing_divide
]

for key in list(pressing_number_keys):
    maps(key)

maps(entering_number,
    nexts=[entering_equal, entering_operation, checking_result],
    ins=pressing_number_keys, 
    outs=pressing_number_keys)

maps(entering_operation,
     nexts=[entering_operation, entering_number, entering_equal, checking_result],
     ins=pressing_operation_keys,
     outs=pressing_operation_keys)

maps(entering_equal,
     nexts=[entering_equal, entering_operation, entering_number, checking_result],
     ins=[pressing_equal],
     outs=[pressing_equal])
