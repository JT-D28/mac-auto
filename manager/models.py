from django.db.models import *
from login.models import *


# Create your models here.

class Function(Model):
	kind = CharField(max_length=12, default='用户定义')
	author = ForeignKey(User, on_delete=CASCADE)
	name = CharField(max_length=64)
	description = CharField(max_length=128)
	flag = CharField(max_length=32)
	body = TextField(null=True)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)
	
	def __str__(self):
		return self.name

class Tag(Model):
	planids = CharField(max_length=128, null=True)
	customize = TextField(null=True)
	var = ForeignKey('Variable', on_delete=CASCADE)
	isglobal = IntegerField(default=0)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)

class TemplateField(Model):
	'''报文字段定义
	'''
	fieldcode=CharField(max_length=16)
	description=TextField()
	start=IntegerField()##从1算起
	end=IntegerField()
	index=IntegerField()


class Template(Model):
	'''报文校验
	'''
	kind=CharField(max_length=2)#length/separator
	name=CharField(max_length=16)
	description=TextField()
	author=ForeignKey(User, on_delete=CASCADE)
	createtime=DateTimeField(auto_now_add=True)
	updatetime=DateTimeField(auto_now=True)
	fieldinfo=ManyToManyField(TemplateField,blank=True,db_column='field_id')


	def __str__(self):
		return '[%s]%s' % (self.id, self.name)

'''
业务数据定义
'''


class Param(Model):
	key = CharField(max_length=32)
	value = TextField(blank=True)


class BusinessData(Model):
	count=IntegerField(default=1,null=True)
	businessname=CharField(max_length=128,null=True)
	itf_check=TextField(null=True)
	db_check=TextField(null=True)
	#params=ManyToManyField(Param,blank=True)
	params=TextField(blank=True,null=True)
	preposition=TextField(blank=True,null=True)
	postposition=TextField(blank=True,null=True)

	parser_id=CharField(max_length=32,null=True)#解析器id
	parser_check=TextField()#解析器校验


	def __str__(self):
		return '[%s]%s' % (self.id, self.businessname)


# class BusinessTitle(Model):
# 	value=CharField(max_length=1000)

class Step(Model):
	choice = (('interface', '接口'), ('function', '函数'))
	count = IntegerField(default=1, null=True)
	
	author = ForeignKey(User, on_delete=CASCADE)
	step_type = CharField(choices=choice, max_length=12, null=True)
	
	##如果是接口类型 这个字段暂时无用
	related_id = CharField(max_length=32, blank=True, null=True)
	
	description = CharField(max_length=500, null=True)
	headers = CharField(max_length=500, blank=True, null=True)
	body = TextField(blank=True, null=True)
	url = TextField(blank=True, null=True)
	method = CharField(max_length=128, blank=True, null=True)
	content_type = CharField(max_length=128, blank=True, null=True)
	
	# db_check=CharField(max_length=128,blank=True)
	# itf_check=CharField(max_length=128,blank=True)
	##临时变量等 |分隔  可以是token
	temp = CharField(max_length=128, blank=True, null=True)
	# tag_id=CharField(max_length=32,blank=True)
	
	businessdatainfo = ManyToManyField(BusinessData, blank=True)
	# businesstitle=CharField(max_length=1000,blank=True)
	db_id = CharField(max_length=20, blank=True, null=True)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)
	
	def __str__(self):
		return "[%s]%s" % (self.id, self.description)


class Case(Model):
	count = IntegerField(default=1)
	author = ForeignKey(User, on_delete=CASCADE)
	# priority=CharField(max_length=32)
	description = CharField(max_length=128)
	businessdatainfo = ManyToManyField(BusinessData, blank=True)
	# steps=ManyToManyField(Step,blank=True)
	db_id = CharField(max_length=20, blank=True, null=True)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)
	
	def __str__(self):
		# return '[%s]%s'%(self.id,self.description)
		return '%s' % self.id


class Plan(Model):
	author = ForeignKey(User, on_delete=CASCADE)
	description = CharField(max_length=128)
	cases = ManyToManyField(Case, blank=True)
	db_id = CharField(max_length=20, blank=True, null=True)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)
	
	# 运行方式:手动运行|定时运行
	run_type = CharField(max_length=32)
	# run_value=CharField(max_length=64)
	# 3状态 succes fail 未运行
	last = CharField(max_length=32, blank=True)
	is_running = CharField(max_length=4, default=0, null=True)
	# is_send_mail=CharField(max_length=6,default='close')
	mail_config_id = CharField(max_length=125, blank=True, null=True)
	
	def __str__(self):
		return '[%s]%s' % (self.id, self.description)


class ResultDetail(Model):
	choice = (('success', 'success'), ('fail', 'fail'))
	taskid = CharField(max_length=64)
	plan = ForeignKey(Plan, on_delete=CASCADE)
	case = ForeignKey(Case, on_delete=CASCADE)
	step = ForeignKey(Step, on_delete=CASCADE, null=True)
	
	businessdata = ForeignKey(BusinessData, on_delete=CASCADE)
	result = TextField(choices=choice, max_length=12)
	spend = CharField(max_length=64, null=True)
	error = TextField(blank=True)
	
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)
	
	loop_id = IntegerField(null=True)
	is_verify = CharField(max_length=4, default=0, null=True)
	
	def __str__(self):
		return "%s,%s" % (self.case, self.step)


class Variable(Model):
	author = ForeignKey(User, on_delete=CASCADE)
	description = CharField(max_length=128)
	key = CharField(max_length=255)
	value = TextField(blank=True, null=True)
	gain = TextField(blank=True, null=True)
	is_cache = BooleanField(default=True)
	# is_default=BooleanField(default=True)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)
	
	def __str__(self):

		return "%s_%s" % (self.author, self.key)
	
	@classmethod
	def oldVarBindTag(cls):
		vars = Variable.objects.all()
		for var in vars:
			if not Tag.objects.filter(var=var).exists():
				tag=Tag()
				tag.var=var
				tag.customize=''
				tag.planids='{}'
				tag.isglobal=1
				tag.save()
				print(str(var.id)+'更新成功')
		print('变量tag更新完成')


class Order(Model):
	"""
	某用例测试步骤或者某计划测试用例的执行顺序

	"""
	main_id = IntegerField()
	follow_id = IntegerField()
	kind = CharField(choices=(('plan', '计划'), ('case', '用例')), max_length=32)
	value = CharField(max_length=64, blank=True)
	
	author = ForeignKey(User, on_delete=CASCADE)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)
	
	def __str__(self):
		return 'kind=%s,main=%s,follow=%s,value=%s' % (self.kind, self.main_id, self.follow_id, self.value)

class Menu(Model):
	text = CharField(max_length=32)
	url = CharField(max_length=64)
	icon = CharField(max_length=64)
	parentid = CharField(max_length=128)


class DBCon(Model):
	kind = CharField(choices=(('oracle', 'Oracle'), ('mysql', "Mysql"), ('db2', 'DB2')), max_length=32)
	dbname = CharField(max_length=64)
	host = CharField(max_length=15, blank=True)
	port = CharField(max_length=5, blank=True)
	
	username = CharField(max_length=15)
	password = CharField(max_length=15)
	description = TextField()
	author = ForeignKey(User, on_delete=CASCADE)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)


class Crontab(Model):
	taskid = CharField(max_length=32)
	plan = ForeignKey(Plan, on_delete=CASCADE)
	###2019 12 23 12 23 45#######
	value = CharField(max_length=32)
	ext = CharField(max_length=32, blank=True, null=True)
	status = CharField(choices=(('close', '关闭'), ('open', '开启')), max_length=12, default='close')
	
	author = ForeignKey(User, on_delete=CASCADE)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)


class MailConfig(Model):
	description = CharField(max_length=64, blank=True, null=True)
	to_receive = CharField(max_length=125, blank=True, null=True)
	cc_receive = CharField(max_length=125, blank=True, null=True)
	rich_text = CharField(max_length=500, blank=True, null=True)
	color_scheme = CharField(max_length=32, default='blue', null=True)
	
	sender_name = CharField(max_length=32, blank=True, null=True)
	sender_nick = CharField(max_length=32, blank=True, null=True)
	sender_pass = CharField(max_length=32, blank=True, null=True)
	smtp_host = CharField(max_length=32, blank=True, null=True)
	smtp_port = CharField(max_length=32, blank=True, null=True)
	is_send_mail = CharField(max_length=125, default='close')
	is_send_dingding = CharField(max_length=125, default='close')
	
	dingdingtoken = CharField(max_length=64, blank=True, null=True)
	author = ForeignKey(User, on_delete=CASCADE, null=True)
	createtime = DateTimeField(auto_now_add=True, null=True)
	updatetime = DateTimeField(auto_now=True, null=True)

class Product(Model):
	'''
	产品表
	'''
	# plans=ManyToManyField(Plan,blank=True)
	description = CharField(max_length=64)
	author = ForeignKey(User, on_delete=CASCADE)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)
	
	def __str__(self):
		return '[%s]%s' % (self.id, self.description)

class OperateLog(Model):
	'''操作日志
	'''
	opcode=CharField(max_length=32)
	opname=CharField(max_length=32)
	description=TextField(blank=True,null=True)
	author=ForeignKey(User, on_delete=CASCADE)
	createtime=DateTimeField(auto_now_add=True)

	def __str__(self):
		return '[%s]%s'%(self.opcode,self.opname)







