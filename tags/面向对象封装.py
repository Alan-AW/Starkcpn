class Foo(object):
    def __init__(self, name):
        self.name = name

    def show_detail(self):
        msg = '我叫%s， 来自火星' % self.name
        print(msg)


obj1 = Foo('alex')
obj2 = Foo('luffy')
obj3 = Foo('sansan')

obj1.show_detail()
obj2.show_detail()
obj3.show_detail()
