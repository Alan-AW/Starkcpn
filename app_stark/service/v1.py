import functools
from types import FunctionType  # 判断一个变量是否是函数
from django.urls import path, re_path
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from django.http import QueryDict
from django import forms
from django.db.models import ForeignKey, ManyToManyField
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
    action_list = list()  # 批量操作选项
    search_group = list()  # 组合搜索组默认配置
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

    def get_action_list(self):
        # 获取批量操作列表
        return self.action_list

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

    def get_search_group(self):
        # 组合搜索钩子函数，方便开发自定义
        return self.search_group

    def get_search_group_condition(self, request):
        condition = dict()
        # 获取URL传递的所有组合搜索的参数
        for option in self.get_search_group():  # 防止误操作，地址栏传递非常多的参数过来进行查询，只去获取配置当中的配置项进行查询
            if option.is_multi:
                values_list = request.GET.getlist(option.field)  # 支持多选如果一个选项用户进行了多选操作，那么一个键会对应多个值，都要获取到
                if not values_list:
                    continue
                condition['%s__in' % option.field] = values_list  # 多选使用 '__in' 表示 或 搜索条件，而不是 且
            else:
                values = request.GET.get(option.field)  # 单选操作，只需要获取对应的一个值即可
                if not values:
                    continue
                condition[option.field] = values  # 单选不使用 '__in' 直接赋值即可

        return condition

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

    def action_multi_delete(self, request, *args, **kwargs):
        # 自定义批量操作下拉框选项
        # 批量删除  如果执行完该函数之后需要跳转到某个地址的话，那么就返回到某个地址
        pk_list = request.POST.getlist('pk')
        self.model_class.objects.filter(id__in=pk_list).delete()  # 执行删除操作
        # return redirect('http://www.baidu.com')

    def action_multi_init(self, request):
        # 批量初始化
        return HttpResponse('批量初始化方法正在开发中!')

    def changelist_view(self, request, *args, **kwargs):
        """
        数据展示视图
        """
        ##########  1.获取批量操作action ##################
        action_list = self.get_action_list()
        action_dict = {func.__name__: func.text for func in action_list}  # {'函数名': '函数对象的text'}
        if request.method == 'POST':
            action_func_name = request.POST.get('action')
            if action_func_name:  # 选择之后才做处理
                if action_func_name in action_dict:
                    # 反射 -- # 执行自定义操作方法（删除\初始化）
                    action_response = getattr(self, action_func_name)(request, *args, **kwargs)
                    # !!!! 扩展功能，如果批量操作之后需要跳转到某个页面，那么就执行自定义的跳转函数 !!!!
                    if action_response:
                        return action_response
                else:
                    return HttpResponse('严重违规警告！！禁止操作！！')

        ##########  2.获取模糊搜索范围 ##################
        search_list = self.get_search_list()
        # 获取用户搜索关键字
        search_value = request.GET.get('q', '')
        # 构造搜索条件 -- Q 用于构造负责ORM查询条件 默认的filter查询在多条件情况下是通过and连接的，不符合逻辑需求
        conn = Q()
        conn.connector = 'OR'
        if search_value:
            for item in search_list:
                conn.children.append((item, search_value))

        ##########  3.获取排序规则 ##################
        order = self.get_order_list()  # 如果search_list没有值，默认不显示搜索框
        search_group_condition = self.get_search_group_condition(request)

        ########## 4.处理分页 ##################
        # 获取数据库中的数据(包含手动搜索和组合搜索的数据)
        queryset = self.model_class.objects.filter(conn).filter(**search_group_condition).order_by(*order)
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

        ########## 5.处理表格 ##################
        # 5.1. 处理表头 -- 使用models中的表类中字段的verbose_name
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

        # 5.2. 处理表的内容tbody
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

        ########## 6 处理添加按钮 ##################
        add_btn = self.get_add_btn()

        ########## 7 处理组合搜索 ##################
        search_group_row_list = list()
        search_group = self.get_search_group()
        for option in search_group:
            # 每一行数据
            row = option.get_queryset_or_tuple(self.model_class, request, *args, **kwargs)
            search_group_row_list.append(row)  # 封装的对象

        return render(request, 'stark/changelist.html', locals())

    def save(self, form, is_update=False):
        """
        预留钩子函数，当开发过程中自定制了页面编辑的字段之后，如果减少了某些字段的编辑，
        有可能导致modelform  save 的时候报错，缺少字段，那么就可以在APP下的XXXHandler类中
        重写此方法进行自定制，将没有进行展示编辑的字段在保存之前设置一个默认值。
        """
        form.save()

    def add_view(self, request, *args, **kwargs):
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

    def edit_view(self, request, pk, *args, **kwargs):
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

    def delete_view(self, request, pk, *args, **kwargs):
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


class SearchGroupRow(object):
    """
    将搜索按钮作为属性封装成统一的对象
    组合搜索关联获取到的数据，queryset对象 或 元祖
    """

    def __init__(self, title, queryset_or_tuple, option, query_dict):
        """
        title: 组合搜索的列名称（分类）使用的是数据库中的 verbose_name 字段
        queryset_or_tuple: 组合搜索关联获取的数据
        option: 配置项APP的Stark.py相关的类中自定义的内容
        query_dict: request.GET 用于获取到url中的组合筛选值
        """
        self.title = title
        self.queryset_or_tuple = queryset_or_tuple
        self.option = option
        self.query_dict = query_dict

    def __iter__(self):
        # ! 定义一个__iter__方法可以将类变为可迭代对象 ! #
        """
        # 默认的展示
        if isinstance(self.queryset_or_tuple, tuple):
            # 如果是元祖对象的话，直接获取到元祖内的 choice 选项
            # ((1, '男'), (2, '女'))
            for item in self.queryset_or_tuple:
                yield '<a href="#">%s</a>' % item[1]
        else:
            # 如果是一个Queryset对象，那么直接迭代返回该对象即可
            # < QuerySet[ < Depart: 董事 >] >
            for item in self.queryset_or_tuple:
                yield '<a href="#">%s</a>' % str(item)
        """
        """
        # 优化后的可自定义的展示
        """
        total_dict = self.query_dict.copy()
        total_dict._mutable = True
        yield '<div class="whole">'
        yield str(self.title) + '(*^▽^*)'
        yield '</div>'
        yield '<div class="othoers">'
        if not self.query_dict.getlist(self.option.field):
            yield '<a href="?%s" class="active">全部</a>' % total_dict.urlencode()
        else:
            total_dict.pop(self.option.field)
            yield '<a href="?%s">全部</a>' % total_dict.urlencode()
        for item in self.queryset_or_tuple:
            show_test = self.option.get_show_test(item)
            value = str(self.option.get_value(item))
            # 生成筛选按钮
            # 1. 需要request.GET（self.query_dict）
            # 返回的搜索条件： request.GET: depart=1&sex=1  ==> <QueryDict: {'depart': ['1'], 'sex': ['1']}>
            # 2. 获取组合搜索文本背后对应的值
            query_dict = self.query_dict.copy()  # 需要修改一份request.GET的值，但是不能直接修改，需要深拷贝一份
            query_dict._mutable = True  # 设置成可以被修改（默认不可修改）
            origin_value_list = query_dict.getlist(self.option.field)
            if not self.option.is_multi:  # 不支持多选
                query_dict[self.option.field] = value  # 设置值（option字段）
                if value in origin_value_list:
                    # 再次点击则 取消 当前搜索条件
                    query_dict.pop(self.option.field)
                    # 被选中样式设计
                    yield '<a href="?%s" class="active">%s</a>' % (query_dict.urlencode(), show_test)
                else:
                    yield '<a href="?%s">%s</a>' % (query_dict.urlencode(), show_test)
            else:
                # 支持多选
                multi_value_list = query_dict.getlist(self.option.field)
                if value in multi_value_list:
                    multi_value_list.remove(value)
                    query_dict.setlist(self.option.field, multi_value_list)
                    yield '<a href="?%s" class="active">%s</a>' % (query_dict.urlencode(), show_test)
                else:
                    multi_value_list.append(value)
                    query_dict.setlist(self.option.field, multi_value_list)
                    yield '<a href="?%s">%s</a>' % (query_dict.urlencode(), show_test)

        yield '</div>'


class SearchOption(object):
    """
    默认的组合搜索条件封装类，在app中可以通过继承该类并且重写方法：
    get_db_condition(self, request, *args, **kwargs)
    实现自定义的搜索条件
    """

    # 组合搜索条件尽量封装到一个类中进行属性的调用即可
    def __init__(self, field, db_condition=None, show_func=None, value_func=None, is_multi=True):
        """
        field: 组合搜索关联的字段
        db_condition: 数据库关联查询的条件
        show_func: 用户自定义组合搜索显示的按钮扩展（用于显示页面文本--显示成图标或者加上前后缀）
        value_func: 组合搜索自定制的
        is_multi: 是否支持多选
        """
        self.field = field
        if not db_condition:
            db_condition = {}
        self.db_condition = db_condition
        self.show_func = show_func
        self.is_choice = False
        self.value_func = value_func
        self.is_multi = is_multi

    def get_db_condition(self, request, *args, **kwargs):
        # 默认的搜索条件，可以通过改写此方法进行定制不同的搜索方式
        return self.db_condition

    def get_queryset_or_tuple(self, model_class, request, *args, **kwargs):
        # 根据字段去获取关联的数据库的数据
        # 根据字符串去对应的models类中找到字段对象
        field_obj = model_class._meta.get_field(self.field)
        title = field_obj.verbose_name
        # 根据对象获取到关联数据
        if isinstance(field_obj, ForeignKey) or isinstance(field_obj, ManyToManyField):
            # 对于ForeignKey, ManyToManyField 应该去获取关联的表的数据: Queryset  -- 然后封装成属性
            db_condition = self.get_db_condition(request, *args, **kwargs)
            return SearchGroupRow(title, field_obj.related_model.objects.filter(**db_condition), self, request.GET)
        else:
            # choice 字段应该去获取对应的choice元组 -- 然后封装成属性
            self.is_choice = True
            return SearchGroupRow(title, field_obj.choices, self, request.GET)

    def get_show_test(self, field_obj):
        """
        获取文本函数也就是配置项中自定义页面显示的内容
        自动计算要显示的文本
        """
        if self.show_func:
            return self.show_func(field_obj)
        if self.is_choice:
            return field_obj[1]
        return str(field_obj)

    def get_value(self, field_obj):
        if self.value_func:
            return self.value_func(field_obj)
        if self.is_choice:
            return field_obj[0]
        return field_obj.pk
