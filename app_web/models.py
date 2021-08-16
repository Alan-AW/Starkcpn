from django.db import models


class Depart(models.Model):
    """
    部门表
    """
    title = models.CharField(verbose_name='部门名称', max_length=32)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'depart'
        verbose_name = '部门'


class User(models.Model):
    """
    用户表
    """
    name = models.CharField(verbose_name='姓名', max_length=32)
    sex_choices = (
        (1, '男'),
        (2, '女'),
    )
    sex = models.IntegerField(verbose_name='性别', choices=sex_choices, default=1)

    age = models.CharField(verbose_name='年龄', max_length=32)
    email = models.CharField(verbose_name='邮箱', max_length=64)
    depart = models.ForeignKey(verbose_name='所属部门', to='Depart', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'user'
        verbose_name = '用户'
