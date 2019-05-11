from pysnooper import log, snoop


@snoop()
def main():
    x = 4
    y = 2 + log(x * 3)
    log(pow(*log(x + 1, y + 1)))


expected_output = '''
21:11:41.664281 call         5 def main():
21:11:41.664487 line         6     x = 4
New var:....... x = 4
21:11:41.664548 line         7     y = 2 + log(x * 3)
Log from log.py - main - 7: 12
New var:....... y = 14
21:11:41.664639 line         8     log(pow(*log(x + 1, y + 1)))
Log from log.py - main - 8: 5
Log from log.py - main - 8: 15
Log from log.py - main - 8: 30517578125
21:11:41.664746 return       8     log(pow(*log(x + 1, y + 1)))
Return value:.. None
'''
