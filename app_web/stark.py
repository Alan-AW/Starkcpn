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
from app_web import models


class DepartHandler(StarkHandler):
    pass


class UserHandler(StarkHandler):
    pass


site.register(models.Depart, DepartHandler)
site.register(models.User, UserHandler)
