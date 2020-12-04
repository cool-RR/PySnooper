import pysnooper

@pysnooper.snoop()
def bubble(number):
    a = [5, 0, 2, 3, 6, 9, 1, 7, 4]
    if number == 1:
        for i in  range(0,11):
            for j in range(i, 9):
                if(a[j] < a[i]):
                    temp = a[i]
                    a[i] = a[j]
                    a[j] = temp
        return a

    else:
        return [0]

print(bubble(0))