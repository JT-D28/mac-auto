from django.db.models import *


class User(Model):
	name = CharField(max_length=128, unique=True)
	password = CharField(max_length=256)
	createtime = DateTimeField(auto_now_add=True, null=True)
	updatetime = DateTimeField(auto_now=True, null=True)
	roles = ManyToManyField("Role")
	
	def __str__(self):
		return self.name
	
	@classmethod
	def create_superuser(cls, password):
		if not User.objects.filter(name='定时任务').exists():
			print('创建一个跑定时任务的账户')
			user = User()
			user.name = '定时任务'
			user.password = '9d3bb895f22bf0afa958d68c2a58ded7'
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


class Menu(Model):
	"""
	菜单
	"""
	title = CharField(max_length=32, unique=True)
	parent = ForeignKey("Menu", null=True, blank=True, on_delete=True)
	
	# 定义菜单间的自引用关系
	# 权限url 在 菜单下；菜单可以有父级菜单；还要支持用户创建菜单，因此需要定义parent字段（parent_id）
	# blank=True 意味着在后台管理中填写可以为空，根菜单没有父级菜单
	
	def __str__(self):
		# 显示层级菜单
		title_list = [self.title]
		p = self.parent
		while p:
			title_list.insert(0, p.title)
			p = p.parent
		# print(title_list)
		return '-'.join(title_list)
	
	def getId(self):
		# 显示层级菜单
		title_id = [self.id]
		p = self.parent
		while p:
			title_id.insert(0, p.id)
			p = p.parent
		# print("aaaaaa", title_id)
		return title_id


class Permission(Model):
	"""
	权限
	"""
	title = CharField(max_length=32, unique=True)
	url = CharField(max_length=128)
	type = CharField(max_length=64, null=False)
	menu = ForeignKey("Menu", null=True, blank=True, on_delete=True)
	
	def __str__(self):
		# 显示带菜单前缀的权限
		return '{menu}---{permission}'.format(menu=self.menu, permission=self.title)


class Role(Model):
	"""
	角色：绑定权限
	"""
	title = CharField(max_length=32, unique=True)
	
	permissions = ManyToManyField("Permission")
