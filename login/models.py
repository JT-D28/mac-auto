from django.db.models import *
from ME2.settings import logme

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
		if not User.objects.filter(name='定时任务').exists():
			print('创建一个跑定时任务的账户')
			user = User()
			user.name = '定时任务'
			user.password = 'cron'
			user.save()
		if not User.objects.filter(name='admin').exists():
			print('创建管理员账户')
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
	name = CharField(max_length=16)
	description = TextField()
	users = ManyToManyField(User, blank=True,related_name='users')
	author = ForeignKey(User, on_delete=CASCADE)
	createtime = DateTimeField(auto_now_add=True, null=True)
	updatetime = DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return '%s'%(self.name)



class UIControl(Model):
	'''
	ui控制
	'''
	code = CharField(max_length=24)
	description = TextField(blank=True)
	is_open=IntegerField(default=0)
	# is_valid=IntegerField(default=0)
	author = ForeignKey(User, on_delete=CASCADE)
	createtime = DateTimeField(auto_now_add=True, null=True)
	updatetime = DateTimeField(auto_now=True, null=True)


class User_UIControl(Model):
	'''用户UI关联表
	'''
	kind = CharField(max_length=12,default='USER')  # USER|ROLE
	user_id = IntegerField()
	uc_id = IntegerField()
	createtime = DateTimeField(auto_now_add=True, null=True)
	updatetime = DateTimeField(auto_now=True, null=True)
	author = ForeignKey(User, on_delete=CASCADE)


class URLControl(Model):
	pass


class BuiltinControl(Model):
	pass
