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
from django.urls import reverse
from django.utils.safestring import mark_safe
from app_stark.service.v1 import site, StarkHandler, get_choices_text
from app_web import models


class DepartHandler(StarkHandler):
    # 定制页面显示内容，list_display 中的项要与数据表的字段对应
    list_display = ['id', 'title']
    has_add_btn = True  # 定制是否显示添加按钮

    """
        如果根据用户的不同来定制不同的列，那么直接写上这个方法，返回值内写入自定义展示的内容
        def get_list_display(self):
            return ['name']
    """


class UserHandler(StarkHandler):
    # 定制页面显示内容，list_display 中的项要与数据表的字段对应
    list_display = ['name', get_choices_text('性别', 'sex'), 'age', 'email', StarkHandler.display_edit, StarkHandler.display_del]
    """
        * 如果根据用户的不同来定制不同的列，那么直接写上这个方法，返回值内写入自定义展示的内容
            def get_list_display(self):
                return ['name']
        
        * 对于表中的choice字段，直接调用 get_choices_text('表头', '字段名') 即可生效。
    """
    has_add_btn = True  # 定制是否显示添加按钮


site.register(models.Depart, DepartHandler)
site.register(models.User, UserHandler)
