#!/usr/bin/python3
import pysnooper
# test recursion
@pysnooper.snoop(depth=float("inf"), color = False)
def factorial(x):
    """This is a recursive function
    to find the factorial of an integer"""

    if x == 1:
        return 1
    else:
        return (x * factorial(x-1))

