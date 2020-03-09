from django.db.models import *

# Create your models here.

class User(Model):

    gender = (
        ('male', "男"),
        ('female', "女"),
    )

    name = CharField(max_length=128, unique=True)
    password = CharField(max_length=256)
    email = EmailField(blank=True)
    sex = CharField(max_length=32, choices=gender, default="男")
    createtime=DateTimeField(auto_now_add=True,null=True)
    updatetime=DateTimeField(auto_now=True,null=True)


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

#
# class Role(Model):
#     '''角色表
#     '''
#     name=CharField(max_length=16)
#     description=TextField()
#
# class Auth(Model):
#     '''
#     权限表
#     '''
#     kind=CharField(max_length=16,default='menu')#OPERATIOH|WEB



# class Operation(Model):
#     '''
#     功能操作
#     '''
#     code=CharField(max_length=16)
#     url=TextField()
#     description=CharField(max_length=64)
#     is_allow=BooleanField(default=True)


# class WebElement(Model):
#     '''
#     web元素
#     '''
#     element_id=CharField(max_length=16)
#     kind=CharField(max_length=16)#BUTTON|MENU
#     text=CharField(max_length=16)
#     url=TextField()
#     description=CharField(max_length=64)
#     is_hide=BooleanField(default=True)
#     is_disable=BooleanField(default=True)


# class AuthOperation(Model):
#     '''
#     权限&功能关联表
#     '''
#     auth=ForeignKey(Auth, on_delete=CASCADE)
#     Op=ForeignKey(Operation,on_delete=CASCADE)

# class AuthWebElement(Model):
#     '''
#     权限&页面元素关联表
#     '''
#     auth=ForeignKey(Auth, on_delete=CASCADE)
#     el=ForeignKey(WebElement,on_delete=CASCADE)

