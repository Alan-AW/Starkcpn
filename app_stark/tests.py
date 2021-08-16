from django.test import TestCase
from types import FunctionType


class Foo(object):
    # 定义一个类方法
    def test(self, obj):
        count = obj
        return print(count)


_list = ['nothing', Foo.test(Foo, 'haha')]  # 将该方法作为参数传递自动被调用（但未传入参数）程序已经报错！

for row in _list:
    if isinstance(row, FunctionType):
        row('success!')  # 检测到列表中的参数为函数，默认执行函数（此时传入了参数）
    else:
        print(row)
