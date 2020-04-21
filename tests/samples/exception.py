import pysnooper


def foo():
    raise TypeError('bad')


def bar():
    try:
        foo()
    except Exception:
        str(1)
        raise


@pysnooper.snoop(depth=3)
def main():
    try:
        bar()
    except:
        pass


expected_output = '''
Source path:... Whatever
12:18:08.017782 call        17 def main():
12:18:08.018142 line        18     try:
12:18:08.018181 line        19         bar()
    12:18:08.018223 call         8 def bar():
    12:18:08.018260 line         9     try:
    12:18:08.018293 line        10         foo()
        12:18:08.018329 call         4 def foo():
        12:18:08.018364 line         5     raise TypeError('bad')
        12:18:08.018396 exception    5     raise TypeError('bad')
        TypeError: bad
        Call ended by exception
    12:18:08.018494 exception   10         foo()
    TypeError: bad
    12:26:33.942623 line        11     except Exception:
    12:26:33.942674 line        12         str(1)
    12:18:08.018655 line        13         raise
    Call ended by exception
12:18:08.018718 exception   19         bar()
TypeError: bad
12:18:08.018761 line        20     except:
12:18:08.018787 line        21         pass
12:18:08.018813 return      21         pass
Return value:.. None
Elapsed time: 00:00:00.000885
'''
