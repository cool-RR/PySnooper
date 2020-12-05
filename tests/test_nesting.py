import time
import pysnooper

snoop = pysnooper.snoop()

def test():
        with snoop:
            a = 10
            with snoop:
                time.sleep(1.0)
            a = 20
            time.sleep(1.0)

test()
