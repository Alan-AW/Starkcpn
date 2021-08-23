class Base(object):
    def __init__(self, name):
        self.name = name

    def show_detail(self):
        msg = '我叫%s， 来自哪里？' % self.name
        print(msg)


class Foo(object):
    def __init__(self, name):
        self.name = name

    def show_detail(self):
        msg = '我叫%s， 来自火星' % self.name
        print(msg)


class Bar(Base):
    pass


obj1 = Foo('old boy')
obj2 = Bar('old girl')
obj1.show_detail()
obj2.show_detail()
