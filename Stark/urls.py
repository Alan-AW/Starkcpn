from django.contrib import admin
from django.urls import path, re_path, include
from app_stark import views as starkViews
from app_web import views as webViews

urlpatterns = [
    # path('stark/', include('app_stark.urls', 'app_stark'), namespace='stark'),
    # path('web/', include('app_web.urls', 'app_web'), namespace='web'),
    # 以上两行代码实现了路由分发到app，可以替换成下面的方法，不需要再在app下创建urls.py文件了
    path('stark/', ([
        path('index/', starkViews.Index.as_view(), name='index')
    ], 'app_stark', 'stark')),

    path('web/', ([
                      path('login/', webViews.Login.as_view(), name='login')
                  ], 'app_web', 'web')),
]
