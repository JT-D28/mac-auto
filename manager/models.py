import time, traceback, re, json
from django.db.models import *
from login.models import *
from manager.ar import RoleData
from manager.context import Me2Log as logger

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
	fieldcode = CharField(max_length=16)
	description = TextField()
	start = IntegerField(default=-1)  ##从1算起
	end = IntegerField(default=-1)
	index = IntegerField(default=-1)


class Template(Model):
	'''报文校验
	'''
	kind = CharField(max_length=32)  # length/separator
	name = CharField(max_length=16)
	description = TextField()
	author = ForeignKey(User, on_delete=CASCADE)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)
	fieldinfo = ManyToManyField(TemplateField, blank=True, db_column='field_id')
	
	def __str__(self):
		return '[%s]%s' % (self.id, self.name)


'''
业务数据定义
'''


class Param(Model):
	key = CharField(max_length=32)
	value = TextField(blank=True)


class BusinessData(Model):
	count = IntegerField(default=1, null=True)
	businessname = CharField(max_length=128, null=True)
	description=TextField(blank=True,null=True)
	itf_check = TextField(null=True)
	db_check = TextField(null=True)
	# params=ManyToManyField(Param,blank=True)
	params = TextField(blank=True, null=True)
	preposition = TextField(blank=True, null=True)
	postposition = TextField(blank=True, null=True)
	
	parser_id = CharField(max_length=32, null=True)  # 解析器id
	parser_check = TextField(null=True)  # 解析器校验
	timeout=IntegerField(default=60)
	isdelete = IntegerField(default=0)
	
	def __str__(self):
		return '[%s]%s' % (self.id, self.businessname)
	
	@classmethod
	def gettestdataparams(cls, businessdata_id):
		try:
			businessdatainst = BusinessData.objects.get(id=businessdata_id)
			msg, step = cls.gettestdatastep(businessdata_id)
			if msg is not 'success':
				return (msg, step)
			
			data = businessdatainst.params
			
			if step.step_type == 'interface':
				if step.content_type in['json','formdata']:
					# data = data.replace('null', 'None').replace('true', 'True').replace('false', 'False')
					if len(re.findall('\$\[(.*?)\((.*?)\)\]', data)) > 0:
						##是函数调用
						pass
					else:
						try:
							print(json.loads(data))
							return ('success', data)
						except:
							data = data.replace('null', 'None').replace('true', 'True').replace('false', 'False')
							return ('success', json.dumps(eval(data)))
						# data=eval(data)
						# data = json.dumps(eval(data))
					
					return ('success', data)
				else:
					return ('success', data)
			
			elif step.step_type == 'function':
				return ('success', businessdatainst.params.split(','))
		except:
			error = '获取测试数据传参信息异常[%s]' % traceback.format_exc()
			print(error)
			return ('error', error)
	
	@classmethod
	def gettestdatastep(cls, businessdata_id):
		# print('aa=>',businessdata_id)
		try:
			businessdatainst = BusinessData.objects.get(id=businessdata_id)
			# steps=models.Step.objects.all()
			# step=[step for step in steps if businessdatainst in list(step.businessdatainfo.all())][0]
			# return ('success',step)
			stepid = Order.objects.get(follow_id=businessdata_id, kind='step_business',isdelete=0).main_id
			step = Step.objects.get(id=stepid)
			return ('success', step)
		
		except:
			print(traceback.format_exc())
			return ('error', '获取业务数据所属步骤异常 业务ID=%s' % businessdata_id)


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
	headers = TextField(blank=True, null=True)
	body = TextField(blank=True, null=True)
	url = TextField(blank=True, null=True)
	method = CharField(max_length=128, blank=True, null=True)
	content_type = CharField(max_length=128, blank=True, null=True)
	##临时变量等 |分隔  可以是token
	temp = CharField(max_length=128, blank=True, null=True)
	# tag_id=CharField(max_length=32,blank=True)
	businessdatainfo = ManyToManyField(BusinessData, blank=True)
	# businesstitle=CharField(max_length=1000,blank=True)
	db_id = CharField(max_length=64, blank=True, null=True)
	isdelete = IntegerField(default=0)


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
	db_id = CharField(max_length=64, blank=True, null=True)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)
	isdelete = IntegerField(default=0)

	def __str__(self):
		# return '[%s]%s'%(self.id,self.description)
		return '[%s]%s' % (self.id,self.description)


class Plan(Model):
	author = ForeignKey(User, on_delete=CASCADE)
	description = CharField(max_length=128)
	db_id = CharField(max_length=64, blank=True, null=True)
	schemename = CharField(max_length=64, blank=True, null=True)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)
	before_plan = CharField(max_length=128, blank=True, null=True)
	# 运行方式:手动运行|定时运行
	run_type = CharField(max_length=32)
	# run_value=CharField(max_length=64)
	# 3状态 succes fail 未运行
	last = CharField(max_length=32, blank=True)
	is_running = CharField(max_length=4, default=0, null=True)
	# is_send_mail=CharField(max_length=6,default='close')
	mail_config_id = CharField(max_length=125, blank=True, null=True)
	isdelete = IntegerField(default=0)

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


class Order(Model):
	"""
	某用例测试步骤或者某计划测试用例的执行顺序

	"""
	main_id = IntegerField()
	follow_id = IntegerField()
	kind = CharField(choices=(('plan', '计划'), ('case', '用例')), max_length=32)
	value = CharField(max_length=64, blank=True)
	isdelete = IntegerField(default=0)
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
	scheme = CharField(max_length=32, blank=True)
	username = CharField(max_length=15)
	password = CharField(max_length=15)
	description = TextField()
	author = ForeignKey(User, on_delete=CASCADE)
	createtime = DateTimeField(auto_now_add=True)
	updatetime = DateTimeField(auto_now=True)


class Crontab(Model):
	plan = ForeignKey(Plan, on_delete=CASCADE)
	###2019 12 23 12 23 45#######
	value = CharField(max_length=32)
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
	isdelete = IntegerField(default=0)

	def __str__(self):
		return '[%s]%s' % (self.id, self.description)


class OperateLog(Model):
	'''操作日志
	'''
	opcode = CharField(max_length=32)
	opname = CharField(max_length=32)
	description = TextField(blank=True, null=True)
	author = ForeignKey(User, on_delete=CASCADE)
	createtime = DateTimeField(auto_now_add=True)
	
	def __str__(self):
		return '[%s]%s' % (self.opcode, self.opname)

class News(Model):
	'''
	消息
	'''
	title=TextField()
	description=TextField()
	sender=ForeignKey(User, on_delete=CASCADE)
	createtime=DateTimeField(auto_now_add=True)
	recv=IntegerField()
	recv_kind=CharField(default='USER',max_length=5) #ROLE|USER
	is_read=IntegerField(default=0) #0|1

	@classmethod
	def get_user_news(cls,userid):
		data=[]
		nws=list(News.objects.filter(recv=userid,recv_kind='USER').order_by('-createtime'))
		sender=User.objects.get(name='admin') or User.objects.get(name='system')
		for x in nws:
			data.append({
				'id':x.id,
				'title':x.title,
				'description':x.description,
				'sendername':sender.name,
				'is_read':x.is_read,
				'createtime':str(x.createtime)[:-7],
				})

		roleid=RoleData.queryuserrole(userid)
		nwsr=list(News.objects.filter(recv=roleid,recv_kind='ROLE').order_by('-createtime'))
		for x in nwsr:
			data.append({
				'id':x.id,
				'title':x.title,
				'description':x.description,
				'sendername':sender.name,
				'is_read':x.is_read,
				'createtime':str(x.createtime)[:-7],
				})


		logger.info('用户[userid=]获得消息数据：',data)

		return data
	@classmethod
	def has_no_read_msg(cls,userid):
		nws=News.objects.filter(recv=userid,recv_kind='USER',is_read=0).order_by('-createtime')
		sender=User.objects.get(name='admin') or User.objects.get(name='system')
		return True if nws.exists() else False

class Recover(Model):
	'''
	树节点文本替换凭据
	'''
	batchid=TextField()#操作批次
	nodeid=CharField(max_length=50)
	field=CharField(max_length=6)
	old=CharField(max_length=60)
	exp=CharField(max_length=60)
	createtime=DateTimeField(auto_now_add=True)
	creater = ForeignKey(User, on_delete=CASCADE)











		