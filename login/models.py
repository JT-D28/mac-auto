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
	createtime = DateTimeField(auto_now_add=True, null=True)
	updatetime = DateTimeField(auto_now=True, null=True)
	
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


class Role(Model):
    '''角色表
    '''
    name=CharField(max_length=16)
    description=TextField()
    user=ManyToManyField(User,blank=True)


class UIControl(Model):
	'''
	ui控制
	'''
	code=CharField(max_length=24)
	description=TextField(blank=True)
	is_config=CharField(max_length=5)#YES|NO
	author=ForeignKey(User,on_delete=CASCADE)
	createtime = DateTimeField(auto_now_add=True, null=True)
	updatetime = DateTimeField(auto_now=True, null=True)


class User_UI_Relation(Model):
	'''用户UI关联表
	'''
	kind=CharField(max_length=12) #USER|ROLE
	user_id=IntegerField()
	uc_id=IntegerField()
	

class URLControl(Model):
	pass

class BuiltinControl(Model):
	pass


