"""
当定义了一个类的时候，如果使用实例化进行调用的话，被调用的方法称为方法
否则就称为一个函数
"""


class Func(object):
    def __init__(self, obj):
        self.obj = obj

    def func_or_meth(self):
        print(self.obj)


func = Func('绑定方法调用')
func.func_or_meth()
print(type(func))  # <class '__main__.Func'>

Func.func_or_meth(Func('作为函数调用'))


# 简单点说就是这样:
class Foo(object):
    def func(self):
        pass


obj = Foo()
obj.func()  # 方法

Foo.func(self=Foo())  # 函数
