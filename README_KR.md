# PySnooper - 디버깅에 print를 쓰지 말자 #

[English](./README.md) | [Korean](./README_KR.md)

**PySnooper** 는 소형판 디버거입니다.

파이썬 코드가 생각대로 작동하지 않는 것을 해결하고 싶습니다. Breakpoint와 watches 기능이 있는 본격적인 디버거를 사용하고 싶지만, 지금 당장 설치하기에는 귀찮습니다.

실행 중인 줄과 실행 되지 않은 줄을 알고 싶고, 지역변수에 무슨 값이 들어있는지 알고 싶습니다.

대부분 사람들은 원하는 위치에 `print` 라인을 사용하고, 그 중 일부는 변수의 값을 표시합니다.

**PySnooper** 는 동일한 작업을 수행할 수 있지만, `print` 줄을 신중하게 추가하는 대신, 관심있는 함수에 데코레이터 한 줄만 넣으면 됩니다. 어떤 줄이 언제 실행되었는지, 정확히 언제 지역 변수가 변경되었는지를 포함한 함수의 실황 로그값을 확인할 수 있습니다.

**PySnooper**를 다른 모든 인텔리전스 도구와 차별화되게 만드는 것은 무엇일까요? 다른 설정 필요 없이 이것을 엉망진창이고 제멋대로인 대규모의 코드베이스에 사용할 수 있습니다. 아래서 보여지는 것 같이 데코레이터를 켜고, 경로를 첫 번째 인수로 지정하여 출력을 전용 로그 파일로 리디렉션하십시오.

# 예시 #

우리는 비트 목록을 반환하여 숫자를 이진수로 변환하는 함수를 작성하고 있습니다. `@ pysnooper.snoop ()` 데코레이터를 추가하여 살펴 보겠습니다.

```python
import pysnooper

@pysnooper.snoop()
def number_to_bits(number):
    if number:
        bits = []
        while number:
            number, remainder = divmod(number, 2)
            bits.insert(0, remainder)
        return bits
    else:
        return [0]

number_to_bits(6)
```
strderr의 출력은:

```
Source path:... /my_code/foo.py
Starting var:.. number = 6
15:29:11.327032 call         4 def number_to_bits(number):
15:29:11.327032 line         5     if number:
15:29:11.327032 line         6         bits = []
New var:....... bits = []
15:29:11.327032 line         7         while number:
15:29:11.327032 line         8             number, remainder = divmod(number, 2)
New var:....... remainder = 0
Modified var:.. number = 3
15:29:11.327032 line         9             bits.insert(0, remainder)
Modified var:.. bits = [0]
15:29:11.327032 line         7         while number:
15:29:11.327032 line         8             number, remainder = divmod(number, 2)
Modified var:.. number = 1
Modified var:.. remainder = 1
15:29:11.327032 line         9             bits.insert(0, remainder)
Modified var:.. bits = [1, 0]
15:29:11.327032 line         7         while number:
15:29:11.327032 line         8             number, remainder = divmod(number, 2)
Modified var:.. number = 0
15:29:11.327032 line         9             bits.insert(0, remainder)
Modified var:.. bits = [1, 1, 0]
15:29:11.327032 line         7         while number:
15:29:11.327032 line        10         return bits
15:29:11.327032 return      10         return bits
Return value:.. [1, 1, 0]
Elapsed time: 00:00:00.000001
```

또는 전체 함수를 추적하지 않으려면 관련 부분을 `with` 블록으로 감쌀 수 있습니다.

```python
import pysnooper
import random

def foo():
    lst = []
    for i in range(10):
        lst.append(random.randrange(1, 1000))

    with pysnooper.snoop():
        lower = min(lst)
        upper = max(lst)
        mid = (lower + upper) / 2
        print(lower, mid, upper)

foo()
```

다음과 같이 출력됩니다:

```
New var:....... i = 9
New var:....... lst = [681, 267, 74, 832, 284, 678, ...]
09:37:35.881721 line        10         lower = min(lst)
New var:....... lower = 74
09:37:35.882137 line        11         upper = max(lst)
New var:....... upper = 832
09:37:35.882304 line        12         mid = (lower + upper) / 2
74 453.0 832
New var:....... mid = 453.0
09:37:35.882486 line        13         print(lower, mid, upper)
Elapsed time: 00:00:00.000344
```

# 특징 #

stderr에 쉽게 접근 할 수 없는 경우, 출력을 파일로 리디렉션 할 수 있습니다:

```python
@pysnooper.snoop('/my/log/file.log')
```

또한 stream이나 callable을 전달해 사용할 수 있습니다.

지역 변수가 아닌 일부 표현식의 값을 확인하세요:

```python
@pysnooper.snoop(watch=('foo.bar', 'self.x["whatever"]'))
```

함수가 호출하는 함수에 대한 snoop 줄을 보여줍니다.

```python
@pysnooper.snoop(depth=2)
```

**더 많은 옵션을 보려면 [Advanced Usage](https://github.com/cool-RR/PySnooper/blob/master/ADVANCED_USAGE.md) 를 참고하세요.** <------

# Pip으로 설치 #

**PySnooper**를 설치하는 가장 좋은 방법은 Pip을 이용하는 것입니다:

```console
$ pip install pysnooper
```

# 다른 설치 방법 #

Conda - conda-forge channel 이용:

```console
$ conda install -c conda-forge pysnooper
```

아치 리눅스:

```console
$ yay -S python-pysnooper
```


# 라이센스 #

Copyright (c) 2019 Ram Rachum and collaborators, released under the MIT license.

저는 [Development services in Python and Django](https://chipmunkdev.com
)를 제공하고 사람들에게 Python 및 관련 주제를 가르치는 [Python workshops](http://pythonworkshops.co/)
을 제공합니다.

# 미디어 보도 #

[Hacker News thread](https://news.ycombinator.com/item?id=19717786)
와 [/r/Python Reddit thread](https://www.reddit.com/r/Python/comments/bg0ida/pysnooper_never_use_print_for_debugging_again/) (2019년 4월 22일)

