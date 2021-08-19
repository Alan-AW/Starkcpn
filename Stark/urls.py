from django.contrib import admin
from django.urls import path, re_path, include
from django.views import static
from django.views.static import serve
from django.conf import settings
from app_stark.service.v1 import site

urlpatterns = [
    path('admin/', admin.site.urls),
    path('stark/', site.urls),
    # 生产环境下静态文件代理
    re_path(r'^static/(?P<path>.*)$', static.serve,
            {'document_root': settings.STATIC_ROOT}, name='static'),
]

# handler404为固定写法，first.views.page_not_found为404处理函数的位置
handler404 = 'app_web.views.page_not_found'
