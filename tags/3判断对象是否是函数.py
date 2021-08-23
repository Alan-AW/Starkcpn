"""
判断一个对象是否是方法有三种方法
"""

dataList = [i for i in range(1, 5)]


def test(obj):
    print('%s是一个函数' % obj)


dataList.append(test)

for row in dataList:
    # 一、 '__call__' 属性
    if hasattr(row, '__call__'):
        row('方式一判断结果-->')

    # 二、callable判断
    if callable(row):
        row('方式二判断结果-->')

    # 三、 isfunction
    from inspect import isfunction

    if isfunction(row):
        row('方式三判断结果-->')

    # 四、 FunctionType
    from types import FunctionType

    if isinstance(row, FunctionType):
        row('方式四判断结果-->')
    print(row)

"""
1
2
3
4
方式一判断结果-->是一个函数
方式二判断结果-->是一个函数
方式三判断结果-->是一个函数
方式四判断结果-->是一个函数
<function test at 0x00000000025570D0>
"""
