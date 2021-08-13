"""
1. 如果不需要自定制视图类，那么直接组册一个models即可，不需要写视图类：
site.register(models.User)

2. stark插件默认生成4个URL对数据表的增删改查；如果需要自定制功能路由那么就需要重新定义视图类：
class XXXXHandler(StarkHandler):
    pass

2.1. 减少功能路由：
class XXXXHandler(StarkHandler):
    def get_urls(self):
        patterns = [
            path('list/', self.changelist_view),
            path('add/', self.add_view),
        ]
        return patterns

2.2 增加功能路由
class XXXXHandler(StarkHandler):
        def extra_urls(self):
            patterns = [
                path('detail/', self.detail_view),
                ......
            ]
        return patterns

        def detail_view(self, request):
            return ......
"""

from django.shortcuts import render, redirect, HttpResponse
from django.utils.safestring import mark_safe
from app_stark.service.v1 import site, StarkHandler
from app_web import models


class DepartHandler(StarkHandler):
    def display_edit(self, obj, is_header=None):
        """
        实现自定制操作栏(表头与内容)
        """
        if is_header:
            return '编辑'
        return mark_safe('<a href="https://www.baidu.com">编辑</a>')

    def display_del(self, obj, is_header=None):
        """
        实现自定制删除栏(表头与内容)
        """
        if is_header:
            return '删除'
        return mark_safe('<a href="https://www.baidu.com">删除</a>')
    # 定制页面显示内容，list_display 中的项要与数据表的字段对应
    list_display = ['id', 'title', display_edit, display_del]
    """
        如果根据用户的不同来定制不同的列，那么直接写上这个方法，返回值内写入自定义展示的内容
    
        def get_list_display(self):
            return ['name']
    """


class UserHandler(StarkHandler):
    def display_edit(self, obj, is_header=None):
        """
        实现自定制操作栏(表头与内容)
        """
        if is_header:
            return '编辑'
        return mark_safe('<a href="https://www.baidu.com">编辑</a>')

    def display_del(self, obj, is_header=None):
        """
        实现自定制删除栏(表头与内容)
        """
        if is_header:
            return '删除'
        return mark_safe('<a href="https://www.baidu.com">删除</a>')

    # 定制页面显示内容，list_display 中的项要与数据表的字段对应
    list_display = ['name', 'age', 'email', display_edit, display_del]
    """
        如果根据用户的不同来定制不同的列，那么直接写上这个方法，返回值内写入自定义展示的内容
    
        def get_list_display(self):
            return ['name']
    """


site.register(models.Depart, DepartHandler)
site.register(models.User, UserHandler)
