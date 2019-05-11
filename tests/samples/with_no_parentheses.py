import pysnooper


def main():
    x = 1
    with pysnooper.snoop:
        y = x + 1
        z = y + 2
    str(z)


expected_output = '''
New var:....... x = 1
20:38:44.712343 line         7         y = x + 1
New var:....... y = 2
20:38:44.712700 line         8         z = y + 2
'''
