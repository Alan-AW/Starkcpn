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
from app_stark.service.v1 import site, StarkHandler
from app_web2 import models


class HostHandler(StarkHandler):
    # 定制页面显示内容，list_display 中的项要与数据表的字段对应
    list_display = ['id', 'host', 'ip']
    """
        如果根据用户的不同来定制不同的列，那么直接写上这个方法，返回值内写入自定义展示的内容

        def get_list_display(self):
            return ['name']
    """


class RoleHandler(StarkHandler):
    # 定制页面显示内容，list_display 中的项要与数据表的字段对应
    list_display = ['id', 'title']
    """
        如果根据用户的不同来定制不同的列，那么直接写上这个方法，返回值内写入自定义展示的内容

        def get_list_display(self):
            return ['name']
    """


site.register(models.Host, HostHandler)
site.register(models.Role, RoleHandler)
