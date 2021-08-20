import functools
from types import FunctionType  # 判断一个变量是否是函数
from django.urls import path, re_path
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from django.http import QueryDict
from django import forms
from app_stark.utils.pageination import Pagination
from django.db.models import Q


class StarkHandler(object):
    def __init__(self, site, model_class, prev):
        self.site = site
        self.model_class = model_class
        self.prev = prev
        self.request = None

    list_display = list()  # 自定义列的展示内容
    has_add_btn = True  # 是否显示 添加 按钮
    order_list = list()  # 排序规则
    search_list = list()  # 默认查询方式
    # 配置文件，自定义页面展示的字段，
    # 如果没有自定义字段信息，那么就使用默认的展示数据表中的所有字段
    # 如果需要自定义，那么在APP下的XXXHandler类中进行自定义
    model_form_class = None

    def display_checkbox(self, obj, is_header=None):
        """
        批量操作的checkbox展示
        """
        if is_header:
            return '选择'
        else:
            edit_url = self.reverse_edit_url(pk=obj.pk)
        return mark_safe('<input type="checkbox" name="pk" value="%s" />' % obj.pk)

    def display_edit(self, obj, is_header=None):
        """
        实现自定制操作栏(表头与内容)
        """
        if is_header:
            return '编辑'
        else:
            edit_url = self.reverse_edit_url(pk=obj.pk)
        return mark_safe('<a href="%s">编辑</a>' % edit_url)

    def display_del(self, obj, is_header=None):
        """
        实现自定制删除栏(表头与内容)
        """
        if is_header:
            return '删除'
        else:
            delete_url = self.reverse_delete_url(pk=obj.pk)
            return mark_safe('<a href="%s">删除</a>' % delete_url)

    def get_add_btn(self):
        """
        预留权限判断的钩子函数：是否显示添加按钮
        """

        if self.has_add_btn:
            # 根据别名反向生成URL
            add_url = self.reverse_add_url()
            return '<a href="%s" class="btn btn-primary">添加</a>' % add_url
        return None

    def get_order_list(self):
        """
        默认数据展示的排序为 -id
        """
        return self.order_list or ['-id']

    def get_search_list(self):
        """
        默认的模糊搜索范围为空，不展示搜索框，
        APP中进行配置之后便按照设置的列进行搜索（也就是字段）
        """
        return self.search_list

    def get_model_form_class(self):
        """
        为所有视图函数提供modelform的编辑，
        """
        if self.model_form_class:
            # 　优先读取用户自定义的类，
            # 如果没有自定义，那么就使用默认的展示所有字段，进行编辑
            return self.model_form_class
        else:
            class DynamicModelForm(StarkModelForm):
                class Meta:
                    model = self.model_class  # 动态获取当前需要操作的视图类
                    fields = '__all__'

            return DynamicModelForm

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
        ##########  获取模糊搜索范围 ##################
        search_list = self.get_search_list()
        # 获取用户搜索关键字
        search_value = request.GET.get('q', '')
        # 构造搜索条件 -- Q 用于构造负责ORM查询条件 默认的filter查询在多条件情况下是通过and连接的，不符合逻辑需求
        conn = Q()
        conn.connector = 'OR'
        if search_value:
            for item in search_list:
                conn.children.append((item, search_value))
        ##########  获取排序规则 ##################
        order = self.get_order_list()  # 如果search_list没有值，默认不显示搜索框
        ########## 1 处理分页 ##################
        # 获取数据库中的数据
        queryset = self.model_class.objects.filter(conn).order_by(*order)
        # 根据URL中的page参数计算出数据的索引位置
        # 生成HTML的页码
        query_paramas = request.GET.copy()  # 拷贝URL地址get参数
        query_paramas._mutable = True  # 默认禁止修改get参数变为可修改
        all_count = queryset.count()
        pager = Pagination(
            current_page=request.GET.get('page'),  # 获取到分页
            all_count=all_count,  # 统计数据库数量
            base_url=request.path_info,  # 当前访问的URL
            query_params=query_paramas,  # 原搜索条件
            per_page=10,  # 每页显示的条数(默认显示10条)
        )
        data_list = queryset[pager.start:pager.end]  # 计算出对应的页的数据

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

        ########## 3 处理添加按钮 ##################
        add_btn = self.get_add_btn()

        return render(request, 'stark/changelist.html', locals())

    def save(self, form, is_update=False):
        """
        预留钩子函数，当开发过程中自定制了页面编辑的字段之后，如果减少了某些字段的编辑，
        有可能导致modelform  save 的时候报错，缺少字段，那么就可以在APP下的XXXHandler类中
        重写此方法进行自定制，将没有进行展示编辑的字段在保存之前设置一个默认值。
        """
        form.save()

    def add_view(self, request):
        model_form_class = self.get_model_form_class()
        if request.method == 'GET':
            form = model_form_class()
            return render(request, 'stark/change.html', locals())
        form = model_form_class(data=request.POST)
        if form.is_valid():
            self.save(form, is_update=False)
            # 保存成功后跳转回list页面
            return redirect(self.reverse_list_url())
        return render(request, 'stark/change.html', locals())

    def edit_view(self, request, pk):
        current_obj = self.model_class.objects.filter(pk=pk).first()
        if not current_obj:
            return HttpResponse('修改的数据不存在！')
        model_form_class = self.get_model_form_class()
        if request.method == 'GET':
            form = model_form_class(instance=current_obj)
            return render(request, 'stark/change.html', locals())
        form = model_form_class(data=request.POST, instance=current_obj)
        if form.is_valid():
            self.save(form, is_update=False)
            # 保存成功后跳转回list页面
            return redirect(self.reverse_list_url())
        return render(request, 'stark/change.html', locals())

    def delete_view(self, request, pk):
        return_url = self.reverse_list_url()
        if request.method == 'GET':
            cancelUrl = return_url
            return render(request, 'stark/delete.html', locals())
        self.model_class.objects.filter(pk=pk).delete()
        return redirect(return_url)

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

    def reverse_add_url(self):
        # 保留原搜索条件进行跳转到添加页面
        name = '%s:%s' % (self.site.namespace, self.get_add_url_name)
        base_url = reverse(name)
        if not self.request.GET:
            add_url = base_url
        else:
            # 原搜索条件携带返回
            param = self.request.GET.urlencode()
            new_query_dict = QueryDict(mutable=True)
            new_query_dict['_filter'] = param
            add_url = '%s?%s' % (base_url, new_query_dict.urlencode())
        return add_url

    def reverse_edit_url(self, *args, **kwargs):
        # 保留原搜索条件进行跳转到编辑页面
        name = '%s:%s' % (self.site.namespace, self.get_edit_url_name)
        base_url = reverse(name, args=args, kwargs=kwargs)
        if not self.request.GET:
            edit_url = base_url
        else:
            # 原搜索条件携带返回
            param = self.request.GET.urlencode()
            new_query_dict = QueryDict(mutable=True)
            new_query_dict['_filter'] = param
            edit_url = '%s?%s' % (base_url, new_query_dict.urlencode())
        return edit_url

    def reverse_delete_url(self, *args, **kwargs):
        # 保留原搜索条件进行跳转到删除页面
        name = '%s:%s' % (self.site.namespace, self.get_delete_url_name)
        base_url = reverse(name, args=args, kwargs=kwargs)
        if not self.request.GET:
            delete_url = base_url
        else:
            # 原搜索条件携带返回
            param = self.request.GET.urlencode()
            new_query_dict = QueryDict(mutable=True)
            new_query_dict['_filter'] = param
            delete_url = '%s?%s' % (base_url, new_query_dict.urlencode())
        return delete_url

    def reverse_list_url(self):
        # 取消删除操作或者编辑完毕之后跳转回list页面携带参数返回的URL
        name = '%s:%s' % (self.site.namespace, self.get_list_url_name)
        base_url = reverse(name)
        params = self.request.GET.get('_filter')
        if not params:
            list_url = base_url
        else:
            list_url = '%s?%s' % (base_url, params)
        return list_url

    def wrapper(self, func):  # request 参数装饰器
        """
        在get_urls中路由请求进来，会首先执行wrapper装饰器，由于每个视图都需要
        用到self.request参数，所以在此统一赋值，这样就不用每个视图函数内都写上
        self.request = request了，并且在后续的开发过程中如果需要在进入视图函数
        之前做其他的操作都可以写到inner内部进行处理，APP中也可以自定义本装饰器
        """

        @functools.wraps(func)  # 装饰器尽量写上这个方法-保留原函数的携带原参数信息
        def inner(request, *args, **kwargs):
            self.request = request
            return func(request, *args, **kwargs)

        return inner

    def get_urls(self):
        """
        默认生成4组增删改查功能路由。如需自定制功能路由可在APP下的stark中重写该方法实现自动定制
        """
        app_label, model_name = self.model_class._meta.app_label, self.model_class._meta.model_name
        patterns = [
            path('list/', self.wrapper(self.changelist_view), name=self.get_list_url_name),
            path('add/', self.wrapper(self.add_view), name=self.get_add_url_name),
            re_path('edit/(?P<pk>\d+)/$', self.wrapper(self.edit_view), name=self.get_edit_url_name),
            re_path('delete/(?P<pk>\d+)/$', self.wrapper(self.delete_view), name=self.get_delete_url_name),
        ]
        # 将用户自定制的URL路由(extend)扩展到全局路由中，而不是将用户自定制的路由列表(append)追加进来
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
    当数据库多字段为choices时使用；
    对stark组件中定义列的显示时，choice显示的中文信息，直接调用此方法
    添加到display_list中传入参数即可：
    title： 表格显示的表头
    field： 数据库的字段名称
    """

    def inner(self, obj=None, is_header=None):
        if is_header:
            return title
        method = 'get_%s_display' % field  # choices内容： get_字段名_display() 直接获取到字段的中文释义
        return getattr(obj, method)()

    return inner


class StarkModelForm(forms.ModelForm):
    """
    为每个编辑视图添加统一的样式
    """

    def __init__(self, *args, **kwargs):
        super(StarkModelForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
