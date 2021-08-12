from django.urls import path, re_path, include

from django.views.static import serve
from django.conf import settings as sys

urlpatterns = [

    # 生产环境下静态文件代理
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': sys.STATIC_ROOT}),
]
handler404 = 'app_web.views.page_not_found'  # handler404为固定写法，first.views.page_not_found为404处理函数的位置
