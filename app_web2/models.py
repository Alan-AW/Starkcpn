from django.db import models


class Host(models.Model):
    """
    主机管理
    """
    host = models.CharField(verbose_name='主机名', max_length=32)
    ip = models.GenericIPAddressField(verbose_name='IP')

    def __str__(self):
        return self.host

    class Meta:
        db_table = 'host'
        verbose_name = '所有主机'


class Role(models.Model):
    """
    角色表
    """
    title = models.CharField(verbose_name='角色名称', max_length=32)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'role'
        verbose_name = '角色'
