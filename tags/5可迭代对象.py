"""
如果一个类中定义了一个__iter__(self) 方法且该方法返回一个迭代器（生成器），
那么就称该对象为可迭代对象，也就是可以被循环

迭代器 和 生成器 ———— “生成器是一个特殊的迭代器”
"""


class Search(object):
    def __init__(self, queryset):
        self.queryset = queryset

    def __iter__(self):
        # return iter(self.queryset)  # 迭代器
        yield 1  # 生成器


row = Search([11, 22, 33])
for item in row:
    # 在未定义 __iter__(self) 的时候
    # TypeError: 'Search' object is not iterable  不可迭代
    print(item)

for data in row:
    # 在定义了 __iter__(self) 的时候
    print(data)  # 11， 22， 33  迭代了
