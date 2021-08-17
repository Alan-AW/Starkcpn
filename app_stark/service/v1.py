from types import FunctionType  # 判断一个变量是否是函数
from django.urls import path, re_path
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from app_stark.utils.pageination import Pagination


class StarkHandler(object):
    def __init__(self, site, model_class, prev):
        self.site = site
        self.model_class = model_class
        self.prev = prev

    def display_edit(self, obj, is_header=None):
        """
        实现自定制操作栏(表头与内容)
        """
        if is_header:
            return '编辑'
        else:
            name = '%s:%s' % (self.site.namespace, self.get_edit_url_name)  # 获取别名
        return mark_safe('<a href="%s">编辑</a>' % reverse(name, args=(obj.pk,)))

    def display_del(self, obj, is_header=None):
        """
        实现自定制删除栏(表头与内容)
        """
        if is_header:
            return '删除'
        else:
            name = '%s:%s' % (self.site.namespace, self.get_delete_url_name)  # 获取别名
        return mark_safe('<a href="%s">删除</a>' % reverse(name, args=(obj.pk,)))

    list_display = list()

    def get_list_display(self):
        """
        获取页面上应该显示的列；如果一张表要显示的字段非常的多，那么在handler对象中配置
        list_display列表中的项需要配置很多字段，不方便，此功能做一个拓展
        """
        value = []
        value.extend(self.list_display)
        return value

    def changelist_view(self, request):
        """
        数据展示视图
        """
        ########## 1 处理分页 ##################
        # 获取数据库中的数据
        # 根据URL中的page参数计算出数据的索引位置
        # 生成HTML的页码
        query_paramas = request.GET.copy()  # 拷贝URL地址get参数
        query_paramas._mutable = True  # 默认禁止修改get参数变为可修改
        pager = Pagination(
            current_page=request.GET.get('page'),  # 获取到分页
            all_count=self.model_class.objects.all().count(),  # 统计数据库数量
            base_url=request.path_info,  # 当前访问的URL
            query_params=query_paramas,  # 原搜索条件
            per_page=10,  # 每页显示的条数(默认显示10条)
        )
        data_list = self.model_class.objects.all()[pager.start:pager.end]  # 计算出对应的页的数据

        ########## 2 处理表格 ##################
        # 2.1. 处理表头 -- 使用models中的表类中字段的verbose_name
        # 页面要显示的列
        list_display = self.get_list_display()
        header_list = list()
        if list_display:
            for key_or_func in list_display:
                if isinstance(key_or_func, FunctionType):  # 判断这里面的变量是否是一个函数，如果是一个函数那么就去执行这个函数
                    verbose_name = key_or_func(self, obj=None,
                                               is_header=True)  # 调用执行函数self参数需要手动进行传递。（未实例化类执行类中的方法其实就是函数的调用）
                else:
                    # 获取数据表中指定xxxx字段的verbos_name属性
                    verbose_name = self.model_class._meta.get_field(key_or_func).verbose_name
                header_list.append(verbose_name)
        else:
            header_list.append(self.model_class._meta.model_name)  # 默认显示数据表类对象
        # 2.2. 处理表的内容tbody
        body_list = list()
        for row in data_list:
            tr_list = list()
            if list_display:
                for key_or_func in list_display:
                    if isinstance(key_or_func, FunctionType):  # 判断这里面的变量是否是一个函数，如果是一个函数那么就去执行这个函数
                        tr_list.append(key_or_func(self, obj=row, is_header=False))  # 调用执行函数self参数需要手动进行传递。
                        # （未实例化类执行类中的方法其实就是函数的调用）
                    else:
                        tr_list.append(getattr(row, key_or_func))
                        # getattr() 方法默认需要传入两个参数，一个是obj对象，一个是字段名称；
                        # 相当于用row对象点上key参数(User.objects.name/User.objects.age)
            else:
                tr_list.append(row)
            body_list.append(tr_list)
        return render(request, 'stark/changelist.html', locals())

    def add_view(self, request):
        return HttpResponse('添加页面')

    def edit_view(self, request, pk):
        return HttpResponse('编辑页面')

    def delete_view(self, request, pk):
        return HttpResponse('删除页面')

    def get_url_name(self, param):
        """
        判断url是否自定制了前缀，用于生成反向解析url别名
        """
        app_label, model_name = self.model_class._meta.app_label, self.model_class._meta.model_name
        if self.prev:
            return '%s_%s_%s_%s' % (app_label, model_name, self.prev, param)
        return '%s_%s_%s' % (app_label, model_name, param)

    @property
    def get_list_url_name(self):
        """
        获取list页面的url别名
        """
        return self.get_url_name('list')

    @property
    def get_add_url_name(self):
        """
        获取添加页面的url别名
        """
        return self.get_url_name('add')

    @property
    def get_edit_url_name(self):
        """
        获取编辑页面的url别名
        """
        return self.get_url_name('edit')

    @property
    def get_delete_url_name(self):
        """
        获取删除页面的url别名
        """
        return self.get_url_name('delete')

    def get_urls(self):
        """
        默认生成4组增删改查功能路由。如需自定制功能路由可在APP下的stark中重写该方法实现自动定制
        """
        app_label, model_name = self.model_class._meta.app_label, self.model_class._meta.model_name
        patterns = [
            path('list/', self.changelist_view, name=self.get_list_url_name),
            path('add/', self.add_view, name=self.get_add_url_name),
            re_path('edit/(\d+)/$', self.edit_view, name=self.get_edit_url_name),
            re_path('delete/(\d+)/$', self.delete_view, name=self.get_delete_url_name),
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
        """
       * _registry*: django启动时注册的列表
        app_name: APP名称
        namespace: namespace 值改变全局生效
        """
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
        self._registry.append({
            'model_class': model_class,
            'handler': handler_class(self, model_class, prev),
            'prev': prev}
        )
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
            """
            # 默认生成业务逻辑的增删改查4个url(写死)
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


def get_choices_text(title, field):
    """
    对stark组件中定义列的显示时，choice显示的中文信息，直接调用此方法
    当数据库多字段为choices时使用；
    title： 表格显示的表头
    field： 数据库的字段名称
    """

    def inner(self, obj=None, is_header=None):
        if is_header:
            return title
        method = 'get_%s_display' % field  # choices内容： get_字段名_display() 直接获取到字段的中文释义
        return getattr(obj, method)()

    return inner
