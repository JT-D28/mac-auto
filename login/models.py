from django.db import models

# Create your models here.

class User(models.Model):

    gender = (
        ('male', "男"),
        ('female', "女"),
    )

    name = models.CharField(max_length=128, unique=True)
    password = models.CharField(max_length=256)
    email = models.EmailField(blank=True)
    sex = models.CharField(max_length=32, choices=gender, default="男")
    createtime=models.DateTimeField(auto_now_add=True)
    updatetime=models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name

    @classmethod
    def create_superuser(cls, password):
        if not User.objects.filter(name='admin').exists():
            user = User()
            user.name = 'admin'
            user.password = password
            user.save()

    class Meta:
        ordering = ["-createtime"]
        verbose_name = "用户"
        verbose_name_plural = "用户"


class Role(models.Model):
    '''角色表
    '''
    name=models.CharField(max_length=16)
    description=models.TextField()

class Auth(models.Model):
    '''
    权限表
    '''
    kind=models.CharField(max_length=16,default='menu')#OPERATIOH|WEB



class Operation(models.Model):
    '''
    功能操作
    '''
    code=models.CharField(max_length=16)
    url=models.TextField()
    description=models.CharField(max_length=64)
    is_allow=models.BooleanField(default=True)


class WebElement(models.Model):
    '''
    web元素
    '''
    element_id=models.CharField(max_length=16)
    kind=models.CharField(max_length=16)#BUTTON|MENU
    text=models.CharField(max_length=16)
    url=models.TextField()
    description=models.CharField(max_length=64)
    is_hide=models.BooleanField(default=True)
    is_disable=models.BooleanField(default=True)


class AuthOperation(models.Model):
    '''
    权限&功能关联表
    '''
    auth=models.ForeignKey(Auth, on_delete=models.CASCADE)
    Op=models.ForeignKey(Operation,on_delete=models.CASCADE)

class AuthWebElement(models.Model):
    '''
    权限&页面元素关联表
    '''
    auth=models.ForeignKey(Auth, on_delete=models.CASCADE)
    el=models.ForeignKey(WebElement,on_delete=models.CASCADE)

