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
Source path:... Whatever
Starting var:.. x = 4
09:31:32.691599 call         5 def factorial(x):
09:31:32.691722 line         6     if x <= 1:
09:31:32.691746 line         8     return mul(x, factorial(x - 1))
    Starting var:.. x = 3
    09:31:32.691781 call         5 def factorial(x):
    09:31:32.691806 line         6     if x <= 1:
    09:31:32.691823 line         8     return mul(x, factorial(x - 1))
        Starting var:.. x = 2
        09:31:32.691852 call         5 def factorial(x):
        09:31:32.691875 line         6     if x <= 1:
        09:31:32.691892 line         8     return mul(x, factorial(x - 1))
            Starting var:.. x = 1
            09:31:32.691918 call         5 def factorial(x):
            09:31:32.691941 line         6     if x <= 1:
            09:31:32.691961 line         7         return 1
            09:31:32.691978 return       7         return 1
            Return value:.. 1
            Elapsed time: 00:00:00.000092
            Starting var:.. a = 2
            Starting var:.. b = 1
            09:31:32.692025 call        11 def mul(a, b):
            09:31:32.692055 line        12     return a * b
            09:31:32.692075 return      12     return a * b
            Return value:.. 2
        09:31:32.692102 return       8     return mul(x, factorial(x - 1))
        Return value:.. 2
        Elapsed time: 00:00:00.000283
        Starting var:.. a = 3
        Starting var:.. b = 2
        09:31:32.692147 call        11 def mul(a, b):
        09:31:32.692174 line        12     return a * b
        09:31:32.692193 return      12     return a * b
        Return value:.. 6
    09:31:32.692216 return       8     return mul(x, factorial(x - 1))
    Return value:.. 6
    Elapsed time: 00:00:00.000468
    Starting var:.. a = 4
    Starting var:.. b = 6
    09:31:32.692259 call        11 def mul(a, b):
    09:31:32.692285 line        12     return a * b
    09:31:32.692304 return      12     return a * b
    Return value:.. 24
09:31:32.692326 return       8     return mul(x, factorial(x - 1))
Return value:.. 24
Elapsed time: 00:00:00.000760
'''
