from django.db import models
from  login.models import *

# Create your models here.

class Function(models.Model):

	kind=models.CharField(max_length=12,default='用户定义')
	author=models.ForeignKey(User, on_delete=models.CASCADE)
	name=models.CharField(max_length=64)
	description=models.CharField(max_length=128)
	flag=models.CharField(max_length=32)
	body=models.TextField(null=True)
	createtime=models.DateTimeField(auto_now_add=True)
	updatetime=models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name


# class Interface(models.Model):
# 	author=models.ForeignKey(User, on_delete=models.CASCADE)
# 	name=models.CharField(max_length=64)
# 	headers=models.CharField(max_length=128)
# 	url=models.CharField(max_length=128)
# 	method=models.CharField(max_length=128)
# 	content_type=models.CharField(max_length=128)
# 	version=models.CharField(max_length=10)
# 	body=models.CharField(max_length=500)
#
# 	createtime=models.DateTimeField(auto_now_add=True)
# 	updatetime=models.DateTimeField(auto_now=True)
#
# 	class Meta:
# 		unique_together=('url','version')
#
# 	def __str__(self):
# 		return '%s[%s]'%(self.url,self.version)

# class InterfaceGen(models.Model):
# 	interface=models.ForeignKey(Interface,on_delete=models.CASCADE)
# 	kind=models.CharField(choices=(('step','测试步骤'),('record','录制'),('direct','直接新增接口')),max_length=16)
# 	by=models.IntegerField()##
# 	createtime=models.DateTimeField(auto_now_add=True)
# 	updatetime=models.DateTimeField(auto_now=True)


class Tag(models.Model):
	name=models.CharField(max_length=16)

	author=models.ForeignKey(User, on_delete=models.CASCADE)
	createtime=models.DateTimeField(auto_now_add=True)
	updatetime=models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name

#
# class Scheme(models.Model):
# 	name=models.CharField(max_length=18)
# 	description=models.CharField(max_length=64)
# 	t1=models.IntegerField()
# 	t2=models.IntegerField()





'''
业务数据定义
'''
class Param(models.Model):
	key=models.CharField(max_length=32)
	value=models.TextField(blank=True)

class BusinessData(models.Model):
	count=models.IntegerField(default=1,null=True)
	businessname=models.CharField(max_length=128,null=True)
	itf_check=models.TextField(null=True)
	db_check=models.TextField(null=True)
	#params=models.ManyToManyField(Param,blank=True)
	params=models.TextField(blank=True,null=True)
	preposition=models.TextField(blank=True,null=True)
	postposition=models.TextField(blank=True,null=True)
	def __str__(self):
		return '[%s]%s'%(self.id,self.businessname)


# class BusinessTitle(models.Model):
# 	value=models.CharField(max_length=1000)

class Step(models.Model):

	choice=(('interface','接口'),('function','函数'))
	count=models.IntegerField(default=1)


	author=models.ForeignKey(User, on_delete=models.CASCADE)
	step_type=models.CharField(choices=choice,max_length=12,null=True)

	##如果是接口类型 这个字段暂时无用
	related_id=models.CharField(max_length=32,blank=True,null=True)

	description=models.CharField(max_length=500,null=True)
	headers=models.CharField(max_length=500,blank=True,null=True)
	body=models.TextField(blank=True,null=True)
	url=models.TextField(blank=True,null=True)
	method=models.CharField(max_length=128,blank=True,null=True)
	content_type=models.CharField(max_length=128,blank=True,null=True)

	# db_check=models.CharField(max_length=128,blank=True)
	# itf_check=models.CharField(max_length=128,blank=True)
	##临时变量等 |分隔  可以是token
	temp=models.CharField(max_length=128,blank=True,null=True)
	# tag_id=models.CharField(max_length=32,blank=True)

	businessdatainfo=models.ManyToManyField(BusinessData,blank=True)
	# businesstitle=models.CharField(max_length=1000,blank=True)
	db_id=models.CharField(max_length=20,blank=True,null=True)
	createtime=models.DateTimeField(auto_now_add=True)
	updatetime=models.DateTimeField(auto_now=True)



	def __str__(self):
		return "[%s]%s"%(self.id,self.description)


class Case(models.Model):

	count=models.IntegerField(default=1)
	author=models.ForeignKey(User, on_delete=models.CASCADE)
	# priority=models.CharField(max_length=32)
	description=models.CharField(max_length=128)
	businessdatainfo=models.ManyToManyField(BusinessData,blank=True)
	# steps=models.ManyToManyField(Step,blank=True)
	db_id=models.CharField(max_length=20,blank=True,null=True)
	createtime=models.DateTimeField(auto_now_add=True)
	updatetime=models.DateTimeField(auto_now=True)


	def __str__(self):
		#return '[%s]%s'%(self.id,self.description)
		return '%s'%self.id


class Plan(models.Model):
	author=models.ForeignKey(User, on_delete=models.CASCADE)
	description=models.CharField(max_length=128)
	cases=models.ManyToManyField(Case,blank=True)
	db_id=models.CharField(max_length=20,blank=True,null=True)
	createtime=models.DateTimeField(auto_now_add=True)
	updatetime=models.DateTimeField(auto_now=True)

	#运行方式:手动运行|定时运行
	run_type=models.CharField(max_length=32)
	# run_value=models.CharField(max_length=64)
	#3状态 succes fail 未运行
	last=models.CharField(max_length=32,blank=True)
	is_running=models.CharField(max_length=4,default=0,null=True)
	# is_send_mail=models.CharField(max_length=6,default='close')
	mail_config_id=models.CharField(max_length=125,blank=True,null=True)

	def __str__(self):
		return '[%s]%s'%(self.id,self.description)

# class Result(models.Model):

# 	author=models.ForeignKey(User, on_delete=models.CASCADE)
# 	case=models.ForeignKey(Case, on_delete=models.CASCADE)
# 	success=models.CharField(max_length=16)
# 	fail=models.CharField(max_length=16)
# 	skip=models.CharField(max_length=16)
# 	createtime=models.DateTimeField(auto_now_add=True)
# 	updatetime=models.DateTimeField(auto_now=True)


class ResultDetail(models.Model):
	choice=(('success','success'),('fail','fail'))
	taskid=models.CharField(max_length=64)
	plan=models.ForeignKey(Plan, on_delete=models.CASCADE)
	case=models.ForeignKey(Case, on_delete=models.CASCADE)
	step=models.ForeignKey(Step, on_delete=models.CASCADE)

	businessdata=models.ForeignKey(BusinessData, on_delete=models.CASCADE)
	result=models.TextField(choices=choice,max_length=12)
	spend=models.CharField(max_length=64,null=True)
	error=models.TextField(blank=True)

	createtime=models.DateTimeField(auto_now_add=True)
	updatetime=models.DateTimeField(auto_now=True)

	loop_id=models.IntegerField(null=True)
	is_verify=models.CharField(max_length=4,default=0)

	def __str__(self):
		return "%s,%s"%(self.case,self.step)


class Variable(models.Model):
	author=models.ForeignKey(User, on_delete=models.CASCADE)
	description=models.CharField(max_length=128)
	tag_id=models.CharField(max_length=24,null=True)
	key=models.CharField(max_length=255,unique=True)
	value=models.TextField(blank=True,null=True)
	gain=models.TextField(blank=True,null=True)
	is_cache=models.BooleanField(default=True)
	# is_default=models.BooleanField(default=True)
	createtime=models.DateTimeField(auto_now_add=True)
	updatetime=models.DateTimeField(auto_now=True)


	def __str__(self):

		return "%s_%s"%(self.author,self.key)



# class priority(models.Model):
# 	"""
# 	测试步骤优先级或测试用例优先级
# 	"""
# 	main_id=models.IntegerField()
# 	follow_id=models.IntegerField()
# 	kind=models.CharField(choices=(('plan','计划'),('case','用例')),max_length=16)
# 	value=models.IntegerField()

# 	author=models.ForeignKey(User, on_delete=models.CASCADE)
# 	createtime=models.DateTimeField(auto_now_add=True)
# 	updatetime=models.DateTimeField(auto_now=True)


class Order(models.Model):
	"""
	某用例测试步骤或者某计划测试用例的执行顺序

	"""
	main_id=models.IntegerField()
	follow_id=models.IntegerField()
	kind=models.CharField(choices=(('plan','计划'),('case','用例')),max_length=16)
	value=models.CharField(max_length=64,blank=True)

	author=models.ForeignKey(User, on_delete=models.CASCADE)
	createtime=models.DateTimeField(auto_now_add=True)
	updatetime=models.DateTimeField(auto_now=True)

	def __str__(self):
		return 'kind=%s,main=%s,follow=%s,value=%s'%(self.kind,self.main_id,self.follow_id,self.value)




# class RelatedTag(models.Model):
# 	"""
# 	用例或者计划打标签
# 	"""
# 	kind=models.CharField(default='case',max_length=16)#暂时用不上
# 	related_id=models.IntegerField()
# 	tag_id=models.IntegerField()
#
# 	author=models.ForeignKey(User, on_delete=models.CASCADE)
# 	createtime=models.DateTimeField(auto_now_add=True)
# 	updatetime=models.DateTimeField(auto_now=True)



#
# class Rule(models.Model):
# 	"""
# 	通用或者约定俗成的一些配置 如token
# 	"""
# 	kind=models.CharField(max_length=64,choices=(('token','token'),))
# 	name=models.CharField(max_length=64)
# 	description=models.CharField(max_length=500)
# 	pick_pattern=models.CharField(max_length=64)#特征提取
# 	final_pattern=models.CharField(max_length=64)##最终样式
# 	src=models.CharField(max_length=64)
# 	dest=models.CharField(max_length=64)
# 	ext=models.CharField(max_length=64)##扩展字段
# 	ext1=models.CharField(max_length=64)


class Menu(models.Model):
	text=models.CharField(max_length=32)
	url=models.CharField(max_length=64)
	icon=models.CharField(max_length=64)
	parentid=models.CharField(max_length=128)



class DBCon(models.Model):
	kind=models.CharField(choices=(('oracle','Oracle'),('mysql',"Mysql"),('db2','DB2')),max_length=10)
	dbname=models.CharField(max_length=15)
	host=models.CharField(max_length=15,blank=True)
	port=models.CharField(max_length=5,blank=True)
	username=models.CharField(max_length=15)
	password=models.CharField(max_length=15)
	description=models.CharField(max_length=32)

	author=models.ForeignKey(User, on_delete=models.CASCADE)
	createtime=models.DateTimeField(auto_now_add=True)
	updatetime=models.DateTimeField(auto_now=True)



class Crontab(models.Model):
	taskid=models.CharField(max_length=32)
	plan=models.ForeignKey(Plan, on_delete=models.CASCADE)
	###2019 12 23 12 23 45#######
	value=models.CharField(max_length=32)
	ext=models.CharField(max_length=32,blank=True,null=True)
	status=models.CharField(choices=(('close','关闭'),('open','开启')),max_length=12,default='close')
	
	author=models.ForeignKey(User, on_delete=models.CASCADE)
	createtime=models.DateTimeField(auto_now_add=True)
	updatetime=models.DateTimeField(auto_now=True)


class MailConfig(models.Model):
	description=models.CharField(max_length=64,blank=True,null=True)
	to_receive=models.CharField(max_length=125,blank=True,null=True)
	cc_receive=models.CharField(max_length=125,blank=True,null=True)
	rich_text=models.CharField(max_length=500,blank=True,null=True)
	color_scheme=models.CharField(max_length=32,default='blue',null=True)

	sender_name=models.CharField(max_length=32,blank=True,null=True)
	sender_nick=models.CharField(max_length=32,blank=True,null=True)
	sender_pass=models.CharField(max_length=32,blank=True,null=True)
	smtp_host=models.CharField(max_length=32,blank=True,null=True)
	smtp_port=models.CharField(max_length=32,blank=True,null=True)
	is_send_mail=models.CharField(max_length=125,default='close')
	is_send_dingding=models.CharField(max_length=125,default='close')

	dingdingtoken=models.CharField(max_length=64,blank=True,null=True)
	author=models.ForeignKey(User, on_delete=models.CASCADE,null=True)
	createtime=models.DateTimeField(auto_now_add=True,null=True)
	updatetime=models.DateTimeField(auto_now=True,null=True)


# class RemoteLog(models.Model):
#
# 	description=models.CharField(max_length=64)
# 	host=models.CharField(max_length=32)
# 	port=models.CharField(max_length=6)
# 	username=models.CharField(max_length=32,blank=True)
# 	password=models.CharField(max_length=32,blank=True)
#
# 	author=models.ForeignKey(User, on_delete=models.CASCADE)
# 	createtime=models.DateTimeField(auto_now_add=True)
# 	updatetime=models.DateTimeField(auto_now=True)



class Product(models.Model):
	'''
	产品表
	'''
	# plans=models.ManyToManyField(Plan,blank=True)
	description=models.CharField(max_length=64)
	author=models.ForeignKey(User, on_delete=models.CASCADE)
	createtime=models.DateTimeField(auto_now_add=True)
	updatetime=models.DateTimeField(auto_now=True)

	def __str__(self):
		return '[%s]%s'%(self.id,self.description)


# class CommonConfig(models.Model):
# 	'''
# 	'''
# 	key=models.CharField(max_length=64)
# 	value=models.TextField(blank=True)
# 	ex_1=models.CharField(max_length=64,blank=True)
# 	ex_2=models.CharField(max_length=64,blank=True)
# 	ex_3=models.CharField(max_length=64,blank=True)
# 	ex_4=models.CharField(max_length=64,blank=True)
# 	ex_5=models.CharField(max_length=64,blank=True)

	
# class DataMove(models.Model):
# 	'''
# 	数据迁移记录
# 	'''
# 	description=models.CharField(max_length=64)
# 	operator=models.ForeignKey(User, on_delete=models.CASCADE)
# 	kind=models.CharField(max_length=64)
# 	createtime=models.DateTimeField(auto_now_add=True)
# 	updatetime=models.DateTimeField(auto_now=True)


# class HumanResource(models.Model):
# 	kind=models.CharField(max_length=64,default='user')
# 	product_id=models.IntegerField()
# 	user_id=models.IntegerField()
# 	group_id=models.IntegerField()
#
# 	createtime=models.DateTimeField(auto_now_add=True)
# 	updatetime=models.DateTimeField(auto_now=True)




