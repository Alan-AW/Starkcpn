from django.urls import path, re_path
from django.shortcuts import render, redirect, HttpResponse


class StarkHandler(object):
    def __init__(self, model_class):
        self.model_class = model_class

    def changelist_view(self, request):
        data_list = self.model_class.objects.all()
        return render(request, 'stark/changelist.html', locals())

    def add_view(self, request):
        return HttpResponse('添加页面')

    def edit_view(self, request, pk):
        return HttpResponse('编辑页面')

    def delete_view(self, request, pk):
        return HttpResponse('删除页面')

    def get_urls(self):
        """
        默认生成4组增删改查功能路由。如需自定制功能路由可在APP下的stark中重写该方法实现自动定制
        """
        patterns = [
            path('list/', self.changelist_view),
            path('add/', self.add_view),
            path('edit/(\d+)/', self.edit_view),
            path('delete/(\d+)/', self.delete_view),
        ]
        patterns.extend(self.extra_urls())  # 此处不会直接调用本方法中的extra_urls，self代指的是APP中自定制的视图类，
        return patterns

    def extra_urls(self):
        """
        方便自定制增加功能路由预留位置
        """
        return list()


class StarkSite(object):
    def __init__(self):
        self._registry = list()
        self.app_name = 'app_stark'
        self.namespace = 'stark'

    def register(self, model_class, handler_class=None, prev=None):
        """
        model_class: 是models中的数据表相关类
        handler_class: 处理请求的视图函数所在的类
        prev: 生成URL的前缀
        """
        # 对于无须自定制视图操作，那么直接使用 StarkHandler 的视图操作
        if not handler_class:
            handler_class = StarkHandler
        self._registry.append({'model_class': model_class, 'handler': handler_class(model_class), 'prev': prev})
        """
        这个操作的结果：
        _registry = [
            {'model_class': models.Depart, 'handler': handler_class(models.Depart)}
            {'model_class': models.User, 'handler': handler_class(models.User)}
            {'model_class': models.Host, 'handler': handler_class(models.Host)}
        ]
        键：model_class       handler_class       
        值：对应的是一个数据表  实例化handler方法，并且将对应的数据表作为参数传入其中做对应的增删改查操作
        这个操作可谓是环环相扣
        """

    def get_url(self):
        patterns = []
        for item in self._registry:
            model_class = item['model_class']
            handler = item['handler']
            prev = item['prev']
            applabel, modelname = model_class._meta.app_label, model_class._meta.model_name
            # 默认生成业务逻辑的增删改查4个url(写死)
            """
            patterns.append(path('%s/%s/list/' % (applabel, modelname), handler.changelist_view))
                patterns.append(path('%s/%s/add/' % (applabel, modelname), handler.add_view))
                patterns.append(path('%s/%s/edit/(\d+)/' % (applabel, modelname), handler.edit_view))
                patterns.append(path('%s/%s/del/(\d+)/' % (applabel, modelname), handler.delete_view))
            """
            # 再次进行路由分发，支持自定制生成不同的URL
            if prev:
                # 自定制前缀
                patterns.append(path('%s/%s/%s/' % (applabel, modelname, prev), (handler.get_urls(), None, None)))
            else:
                # 无须自定制前缀
                patterns.append(path('%s/%s/' % (applabel, modelname), (handler.get_urls(), None, None)))
        # patterns.append(path('index/', lambda request: HttpResponse('index')))
        # patterns.append(path('home/', lambda request: HttpResponse('home')),)
        return patterns

    @property
    def urls(self):
        return (self.get_url(), self.app_name, self.namespace)


site = StarkSite()
