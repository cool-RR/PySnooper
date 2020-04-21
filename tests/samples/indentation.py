import pysnooper


@pysnooper.snoop(depth=2)
def main():
    f2()


def f2():
    f3()


def f3():
    f4()


@pysnooper.snoop(depth=2)
def f4():
    f5()


def f5():
    pass


expected_output = '''
Source path:... Whatever
21:10:42.298924 call         5 def main():
21:10:42.299158 line         6     f2()
    21:10:42.299205 call         9 def f2():
    21:10:42.299246 line        10     f3()
        Source path:... Whatever
        21:10:42.299305 call        18 def f4():
        21:10:42.299348 line        19     f5()
            21:10:42.299386 call        22 def f5():
            21:10:42.299424 line        23     pass
            21:10:42.299460 return      23     pass
            Return value:.. None
        21:10:42.299509 return      19     f5()
        Return value:.. None
        Elapsed time: 00:00:00.000134
    21:10:42.299577 return      10     f3()
    Return value:.. None
21:10:42.299627 return       6     f2()
Return value:.. None
Elapsed time: 00:00:00.000885
'''
