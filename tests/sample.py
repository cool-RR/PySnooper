from pysnooper import Indices

from .utils import NoTimeTracer


@NoTimeTracer(
    depth=2,
    watch=(Indices('z')[-3:]),
    prefix='ZZZ ',
)
def foo(x):
    y = x + 1
    y += bar(y)
    z = list(range(1000))
    return z


def bar(z):
    return z * 2


expected_output = '''
ZZZ Starting var:....... x = 5
ZZZ insert_the_time_here call        11 def foo(x):
ZZZ insert_the_time_here line        12     y = x + 1
ZZZ New var:............ y = 6
ZZZ insert_the_time_here line        13     y += bar(y)
ZZZ     Starting var:....... z = 6
ZZZ     insert_the_time_here call        18 def bar(z):
ZZZ     insert_the_time_here line        19     return z * 2
ZZZ     insert_the_time_here return      19     return z * 2
ZZZ     Return value:....... 12
ZZZ Modified var:....... y = 18
ZZZ insert_the_time_here line        14     z = list(range(1000))
ZZZ New var:............ z = [0, 1, 2, 3, 4, 5, ...]
ZZZ New var:............ z[997] = 997
ZZZ New var:............ z[998] = 998
ZZZ New var:............ z[999] = 999
ZZZ insert_the_time_here line        15     return z
ZZZ insert_the_time_here return      15     return z
ZZZ Return value:....... [0, 1, 2, 3, 4, 5, ...]
'''
