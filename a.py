import pysnooper

@pysnooper.snoop(depth = float('inf'))
def func(x):
    if x == 0:
        return
    func(x - 1)

func(3)