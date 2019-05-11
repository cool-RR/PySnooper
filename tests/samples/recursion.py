import pysnooper


@pysnooper.snoop(depth=2)
def factorial(x):
    if x <= 1:
        return 1
    return mul(x, factorial(x - 1))


def mul(a, b):
    return a * b


def main():
    factorial(4)
    
expected_output = '''
Starting var:.. x = 4
20:28:17.875295 call         5 def factorial(x):
20:28:17.875509 line         6     if x <= 1:
20:28:17.875550 line         8     return mul(x, factorial(x - 1))
    Starting var:.. x = 3
    20:28:17.875624 call         5 def factorial(x):
    20:28:17.875668 line         6     if x <= 1:
    20:28:17.875703 line         8     return mul(x, factorial(x - 1))
        Starting var:.. x = 2
        20:28:17.875771 call         5 def factorial(x):
        20:28:17.875813 line         6     if x <= 1:
        20:28:17.875849 line         8     return mul(x, factorial(x - 1))
            Starting var:.. x = 1
            20:28:17.875913 call         5 def factorial(x):
            20:28:17.875953 line         6     if x <= 1:
            20:28:17.875987 line         7         return 1
            20:28:17.876021 return       7         return 1
            Return value:.. 1
            Starting var:.. a = 2
            Starting var:.. b = 1
            20:28:17.876111 call        11 def mul(a, b):
            20:28:17.876151 line        12     return a * b
            20:28:17.876190 return      12     return a * b
            Return value:.. 2
        20:28:17.876235 return       8     return mul(x, factorial(x - 1))
        Return value:.. 2
        Starting var:.. a = 3
        Starting var:.. b = 2
        20:28:17.876320 call        11 def mul(a, b):
        20:28:17.876359 line        12     return a * b
        20:28:17.876397 return      12     return a * b
        Return value:.. 6
    20:28:17.876442 return       8     return mul(x, factorial(x - 1))
    Return value:.. 6
    Starting var:.. a = 4
    Starting var:.. b = 6
    20:28:17.876525 call        11 def mul(a, b):
    20:28:17.876563 line        12     return a * b
    20:28:17.876601 return      12     return a * b
    Return value:.. 24
20:28:17.876646 return       8     return mul(x, factorial(x - 1))
Return value:.. 24
'''
