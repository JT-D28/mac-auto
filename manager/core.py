#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-08-29 08:43:52
# @Author  : Blackstone
# @to      :

#from manager import models

import  requests,re,warnings,copy,os,traceback,base64,time,json,datetime,smtplib,base64
from collections import namedtuple
from login.models import User
from django.http import HttpResponse,JsonResponse
from hashlib import md5
from . import models
from login import models as md
from .models import Function
from .builtin import *
from .db import Mysqloper as op
from pyDes import *
from django.conf import settings

#用户变量缓存 key=user.varname
# __varcache=dict()

# #sql关键字
# __sql_key=('insert','delete','update','select')

# #内置支持的比较操作，还要支持包含操作
# __compare_word=('>=','<=','!=','=','>','<')



##三方调用

def clear_task_before(taskid):
	'''
	清除任务id之前可能存在的结果
	'''
	detaillist=list(models.ResultDetail.objects.filter(taskid=taskid))
	[x.delete()  for x in detaillist]



def gen_third_invoke_url(planid):
	taskid=planid
	callername=models.Plan.objects.get(id=planid).author.name
	mwstr='callername=%s&taskid=%s'%(callername,taskid)
	return '%s/manager/third_party_call/?v=%s&planid=%s'%(settings.BASE_URL,EncryptUtils.base64_encrypt(EncryptUtils.des_encrypt(mwstr)),planid)


def decrypt_third_invoke_url_params(paramV):
	d={}
	mwstr=EncryptUtils.des_decrypt(EncryptUtils.base64_decrypt(paramV))
	for x in mwstr.split('&'):
		key=x.split('=')[0]
		v=x.split('=')[1]
		d[key]=v

	return d





"""
计划&&用例相关
"""

def genorder(kind="case",parentid=None,childid=None):

	code=0

	# print("type=%s parentid=%s childid=%s"%(kind,parentid,childid))

	try:
		if parentid is not None:
			# steps=models.Case.objects.get(id=parentid).steps
			start_group_id=1
			start_index=1

			if childid is None:
				#根据创建时间重新排序
				#sorted_steps_order= models.Order.objects.filter(main_id=parentid,kind=kind).order_by('createtime')
				

				#保持原来顺序重新排序
				sorted_steps_order=ordered(list(models.Order.objects.filter(main_id=parentid,kind=kind)))

				# print(len(sorted_steps_order))
				for order in sorted_steps_order:
					# print(order.id,order.main_id,order.follow_id)
					models.Order.objects.filter(id=order.id).update(value="%s.%s"%(start_group_id,start_index))
					#models.Order.objects.filter(id=order.id).update(value='1.4')
					start_index=start_index+1
					
			else:
				##

				##更新指定step或case后的执行序号
				sorted_steps_order=[_ for _ in models.Order.objects.filter(main_id=parentid,kind=kind).order_by('value')]
				size=len(sorted_steps_order)
				if size==1:
					order=models.Order.objects.get(main_id=parentid,kind=kind)
					order.value='1.1'
					order.save()
					
				else:
					print("更新group..")
					is_update=False
					for order in sorted_steps_order:
						step_id=order.follow_id
						print(type(childid))
						if int(step_id)==int(childid):
							is_update=True
							value=models.Order.objects.get(main_id=parentid,follow_id=childid,kind=kind).value
							old_group_id=int(value.split(".")[0])
							start_group_id=int(old_group_id)+1
							models.Order.objects.filter(id=order.id).update(value="%s.%s"%(start_group_id,start_index))
							start_index=int(start_index)+1
						else:
							if is_update==True:
								if start_group_id==1:
									raise Exception('groupid=>1')
								models.Order.objects.filter(id=order.id).update(value="%s.%s"%(start_group_id,start_index))
								start_index=int(start_index)+1
						
	except Exception as e:
		code=1
		traceback.print_exc(e)

	finally:
		return code



def changepostion(kind,parentid,childid,move=1):

	# print('=='*100)
	# print(kind,parentid,childid,move)
	flag,msg='success',''
	try:
		parentid=int(parentid)
		childid=int(childid)
		move=int(move)
		# print(parentid,childid,move)
		orderlist=ordered(list(models.Order.objects.filter(main_id=parentid,kind=kind).order_by('value')))
		# print("orderlist=>",orderlist)
		size=len(orderlist)
		# print('移动项所列表长度',size)
		pos=-1
		for item in orderlist:
			pos=pos+1
			if item.follow_id==childid:
				break;


		if pos+move>=size or pos+move<0:
			print("------------边界操作忽略...--------------")
			return 0

		# print("移动项所在位置=>",pos)

		tmp=orderlist[pos].value
		orderlist[pos].value=orderlist[pos+move].value
		orderlist[pos].save()
		orderlist[pos+move].value=tmp
		orderlist[pos+move].save()
	except:
		flag='error'
		msg='changepostion操作异常[%s]'%traceback.format_exc()
		print(traceback.format_exc())
	return (flag,msg)

def swap(kind,main_id,aid,bid):
	flag,msg='nosee',''
	try:

		ao=models.Order.objects.get(kind=kind,main_id=main_id,follow_id=aid)
		bo=models.Order.objects.get(kind=kind,main_id=main_id,follow_id=bid)
		tmp=ao.value
		ao.value=bo.value
		bo.value=tmp

		ao.save()
		bo.save()
		flag,msg='success','操作成功'


	except:
		print(traceback.format_exc())
		msg='swap操作异常%s'%traceback.format_exc()
		flag='error'
	

	return (flag,msg)



# def getpagedata(list_,request):
# 	"""
# 	获取分页数据
# 	"""
# 	page=int(request.GET.get("page"))
# 	limit=int(request.GET.get("limit"))

# 	print("获取分页数据 page=%s limit=%s"%(page,limit))

# 	start=(page-1)*limit+1
# 	end=page*limit+1
# 	return list_[start:end]


def testinterface(interface):

	try:
		url=interface.url
		body=interface.body
		method=interface.method

		cmdstr='requests.%s(%s,data=%s)'%(method,url,body)
		print("执行请求=>",cmdstr)
		res=eval(cmdstr)
		print("执行结果=>",res.text)
		return True
	except Exception as e:
		print(e)


def testfunc(functionstr):
	try:
		print("执行函数=>",functionstr)
		res= eval(functionstr)
		print("执行结果=>",res)
		return res
	except Exception as e:
		return False


# def runstep(step):
# 	type_=step.step_type
# 	if type_=='function':
# 		try:
# 			eval(step.body)
# 			return True
# 		except Exception as e:
# 			print(e)
# 			return False

# 	elif type_=='interface':

# 		try:
# 			url=step.interface.url
# 			body=step.body
# 			method=step.interface.method
# 			print("接口地址=>"%url)
# 			print("请求方式=>"%method)
# 			print("请求参数=>"%body)
# 			#requests.post(url,data=body)
# 			response=eval('requests.%s(url,data=body)'%method)
# 			d=eval(_responsefilter(response.text))
# 			db_check_items=step.db_check.split("||")
# 			itf_check_items=step.itf_check.split("||")

# 			##验证过程....

# 			#####

# 			return True
# 		except Exception as e:
# 			print(e)
# 			return False

# 	else:
# 		warnings.warn("不能识别的测试步骤类型=>%s"%type_)

# 	return False







# def _is_sql_call(str_):
# 	s=str_.strip()
# 	res=len(re.findall('|'.join(__sql_key),s))
# 	#print(res)
# 	if res>0:
# 		return True
# 	else:
# 		return False


# def _eval(str_):
# 	"""
# 	执行有意义的函数 or sql字符串
# 	"""

# 	if _is_sql_call(str_):
# 		return op().db_execute(str_)
# 	else:
# 		return eval(str_)



# def _responsefilter(msg):
# 	msg=msg.replace('true','True').replace('false','False').replace('null','None')
# 	return msg

# def _responsecheck(response,wait_check_list=None):
# 	'''
# 	可能的情况
# 	{{x}}=1 
# 	code=3
# 	list[0].text=1111
# 	'''
# 	if wait_check_list is None:
# 		warnings.warn("校验列表为空，默认通过..")
# 		return True

# 	#存储所有校验项的执行结果
# 	res=[]
# 	operator='='
# 	for item in wait_check_list:
# 		operator=_getoperator(item)
# 		if operator is None:
# 			warnings.warn('校验表达式无法解析=>%s'%item)
# 			return True

# 		left=item.split(operator)[0]
# 		right=item.split(operator)[1]

		



# def _getoperator(str_):
# 	"""
# 	获取操作符
# 	"""

# 	for x in __compare_word:
# 		if x in str_:
# 			return x

# 	return None

def packagemenu(list_):
	root=None
	for menu in list_:
		#print(menu.parentid)
		if menu.parentid=='0':
			root=menu
			break

	#print(root)

	_packagenodechildren(root,list_)



	return root



def _packagenodechildren(menu,list_):
	if getattr(menu, 'child',None) is None:
		menu.child=[]

	for cmenu in list_:
		cmenu.child=[]
		if cmenu.parentid==str(menu.id):
			print("uuuuuuuuuuuuuuuuuuuuuuuuuuuuu")
			menu.child.append(cmenu)
			alist=copy.deepcopy(list_)
			alist.remove(cmenu)
			_packagenodechildren(cmenu, alist)


# class MenuJsonEncoder(json.JSONEncoder):
# 	def default(self,obj):
# 		url=obj.url
# 		text=obj.text
# 		icon=obj.icon
# 		child=obj.child

# 		return {
# 		'urr':url,
# 		'text':text,
# 		'icon':icon,
# 		'child':child

# 		}



"""
实例json解析
"""

class XJsonEncoder(json.JSONEncoder):

	def __init__(self,attrs=None,**args):

		self._total=args.get('total', None)
		#print('self.total=>',self._total)
		if self._total is not None:
			del args['total']

		super(XJsonEncoder,self).__init__(**args)
		self._attrs=attrs
		#print('attrs=>',self._attrs)
		#print('args=>',args)

	def default(self,obj):
		_map={}

		#print(len(self._attrs))
		for x in self._attrs:
			#print("name=>",x)
			v=''

			try:
				v=getattr(obj, x)
				# if isinstance(v,datetime.datetime):
				# 	v=v[:18]

				v=str(v)

			except:
				#print(type(obj))
				# print('error',obj,x)
				v=str(obj)
			finally:
				_map[x]=v

		#print(_map)

		return _map


	def encode(self,obj):
		L=eval(super(XJsonEncoder,self).encode(obj))

		return {
		"code":0,
		"msg":'操作成功',
		#"count":len(L),
		"count":self._total,
		 #"data":[{'key':'host','value':'2.2.34.3'}],
		"data":L
		}


class ProductEncoder(XJsonEncoder):
	def __init__(self,**args):
		super(ProductEncoder,self).__init__(['id','description','createtime','updatetime','author'],**args)



class VarEncoder(XJsonEncoder):
	def __init__(self,**args):
		super(VarEncoder,self).__init__(['id','description','key','gain','value','createtime','updatetime','is_cache','tag','author'],**args)


class UserEncoder(XJsonEncoder):
	def __init__(self,**args):
		super(UserEncoder,self).__init__(['id','createtime','updatetime','name','password'],**args)



class ItfEncoder(XJsonEncoder):
	def __init__(self,**args):
		super(ItfEncoder,self).__init__(['id','name','headers','url','content_type','method','version','createtime','updatetime'],**args)


class CaseEncoder(XJsonEncoder):
	def __init__(self,**args):
		super(CaseEncoder,self).__init__(['id','author','priority','description','steps','createtime','updatetime','db_id'],**args)

	def encode(self,obj):
		L=eval(super(XJsonEncoder,self).encode(obj))
		if not isinstance(L, (list)):
			L=[L]

		for x in L:
			try:
				o1=list(models.Order.objects.filter(kind='plan_case',follow_id=int(x.get('id'))))
				o2=list(models.Order.objects.filter(kind='case_case',follow_id=int(x.get('id'))))

				if len(o1)>0:
					x['weight']=o1[0].value
				else:
					if len(o2)>0:
						x['weight']=o2[0].value
					else:
						x['weight']='未知'

			except:
				print(traceback.format_exc())
				x['weight']='未知'

		return {
		"code":0,
		"msg":'操作成功',
		#"count":len(L),
		"count":self._total,
		 #"data":[{'key':'host','value':'2.2.34.3'}],
		"data":L
		}




class PlanEncoder(XJsonEncoder):
	def __init__(self,**args):
		super(PlanEncoder,self).__init__(['id','author','last','description','cases','createtime','updatetime','run_type','run_value','mail_config_id','db_id'],**args)
	def encode(self,obj):
		#print('hhhh'*100)
		L=eval(super(XJsonEncoder,self).encode(obj))
		code=0
		if not isinstance(L, (list)):
			L=[L]

		# print('UU'*100)
		# print(L)
	
		for x in L:
		
			try:
				invoke_url=gen_third_invoke_url(x['id'])
				x['invoke_url']=invoke_url
				
				config_id=x.get('mail_config_id')
				is_send_mail=models.MailConfig.objects.get(id=config_id).is_send_mail

				x['is_send_mail']=is_send_mail

				# print("uuuuuuuuuu=>",x)

			except:
				
				msg='计划未关联邮件'
				x['is_send_mail']='disabled'
				pass

		print(L)

		return {
		"code":0,
		"msg":'操作成功',
		#"count":len(L),
		"count":self._total,
		 #"data":[{'key':'host','value':'2.2.34.3'}],
		"data":L
		}

class ResultEncoder(XJsonEncoder):
	def __init__(self,**args):
		super(ResultEncoder,self).__init__(['id','author','case','success','skip','fail','updatetime','createtime'],**args)

class ResultDetailEncoder(XJsonEncoder):
	def __init__(self,**args):
		
		super(ResultDetailEncoder,self).__init__(['id','case','step','result','createtime','updatetime'],**args)



class FunctionEncoder(XJsonEncoder):
	def __init__(self,**args):
		
		super(FunctionEncoder,self).__init__(['id','kind','author','name','description','flag','body','createtime','updatetime'],**args)


class StepEncoder(XJsonEncoder):
	def __init__(self,**args):
		super(StepEncoder,self).__init__(['id','businesstitle','author','priority','interface','description','headers','body','db_check','itf_check','step_type','createtime','updatetime','tag_id','temp','url','content_type','method','db_id'],**args)
	
	def encode(self,obj):
		L=eval(super(XJsonEncoder,self).encode(obj))
		if not isinstance(L, (list)):
			L=[L]
	
		for x in L:
			#print("x=>",x)
			tag_id=x.get('tag_id')
			uid=x.get('id')
			try:

				# print('weight=>',uid)
				x['weight']=models.Order.objects.get(kind='case_step',follow_id=int(uid)).value

			except:
				print(traceback.format_exc())
				x['weight']='未知'



			try:
				tagname=models.Tag.objects.get(id=tag_id.strip()).name
				x['tagname']=tagname
			except:
				x['tagname']=''

		return {
		"code":0,
		"msg":'操作成功',
		#"count":len(L),
		"count":self._total,
		 #"data":[{'key':'host','value':'2.2.34.3'}],
		"data":L
		}


class BusinessDataEncoder(XJsonEncoder):
	def __init__(self,**args):
		super(BusinessDataEncoder,self).__init__(['id','businessname','db_check','itf_check','params','postposition','preposition','count'],**args)
	
	def encode(self,obj):
		from .cm import getchild
		L=eval(super(XJsonEncoder,self).encode(obj))
		if not isinstance(L, (list)):
			L=[L]

		steps=models.Step.objects.all()
		
		for x in L:
			try:

				x['weight']=models.Order.objects.get(kind='step_business',follow_id=int(x.get('id'))).value

			except:
				print('weight=>',traceback.format_exc())
				x['weight']='未知'

			# print('x[weight]=>',x['weight'])


			if x.get('count')=='None':
				# print('yes')
				x['count']= 1
			# print('count=>',x['count'])

			try:
				##找关联step
				stepinst=None
				for step in list(models.Step.objects.all()):
					businessids=[sb.id for sb in getchild('step_business',step.id)]
					#print(businessids)
					idd=x.get('id')
					try:
						idd=int(idd)
					except:
						pass

					if idd in businessids:
						stepinst=step
						break;

				if stepinst is None:
					warnings.warn('获取业务数据[id=%s]关联步骤操作失败'%x.get('id'))
				else:
					print('[获取业务数据关联步骤]step_id=%s'%stepinst.id)
					# stepinst=step_matchs[0]
					# tag_id=stepinst.tag_id
					x['stepname']=stepinst.description
				x['businessname']=x.get('businessname')
	

				# if tag_id.strip():
				# 	x['tagname']=models.Tag.objects.get(id=tag_id.strip()).name

			except:
				print(traceback.format_exc())
				#x['tagname']=''

		return {
		"code":0,
		"msg":'操作成功',
		#"count":len(L),
		"count":self._total,
		 #"data":[{'key':'host','value':'2.2.34.3'}],
		"data":L
		}



class TagEncoder(XJsonEncoder):
	def __init__(self,**args):
		super(TagEncoder,self).__init__(['id','author','name','createtime','updatetime'],**args)
class MailConfigEncoder(XJsonEncoder):
	def __init__(self,**args):
		super(MailConfigEncoder,self).__init__(['id','author','smtp_host','smtp_port','sender_name','sender_nick','sender_pass','is_send_mail','createtime','updatetime','description','to_receive','cc_receive','color_scheme','rich_text'],**args)



class  OrderEncoder(XJsonEncoder):
	def __init__(self,**args):
		super(OrderEncoder,self).__init__(['id','main_id','follow_id','value','kind','updatetime','createtime','author'],**args)
		

class DBEncoder(XJsonEncoder):
	def __init__(self,**args):
		super(DBEncoder,self).__init__(['id','kind','dbname','host','port','username','password','description','author','createtime','updatetime'],**args)

def simplejson(code=0,msg='',**kw):
	_dict={}

	_dict['code']=code
	_dict['msg']=msg

	for key,value in kw.items():
		_dict[key]=value

	return json.dumps(_dict)

def pkg(code=0,msg='',**kw):
	_dict={}

	_dict['code']=code
	_dict['msg']=msg

	for key,value in kw.items():
		_dict[key]=value

	return _dict

def getpagedata(data,page,limit):
	'''
	返回分页数据与元数据大小
	'''
	print('page=>%s limit=>%s'%(page,limit))
	if page is None or limit is None:
		return data,len(data)
		
	if data is None:
		data=[]
		
	old=copy.copy(data)
	start=(int(page)-1)*int(limit)
	end=int(page)*int(limit)
	data=data[start:end+1]

	print("分页信息[分页数据大小=%s 返回%s-%s数据]"%(len(old),start+1,end))
	#print(start,end)
	return data,len(old)

def ordered(iterator,key='value'):
	"""
	执行列表根据value从小到大排序
	"""
	try:
		for i  in range(len(iterator)-1):
			for j in range(i+1,len(iterator)):
				#print(key,getattr(iterator[i],key).split(".")[0],int(str(getattr(iterator[i],key)).split(".")[0]))
				# print('attr value=>',iterator[i].value)
				
				groupa=int(str(getattr(iterator[i],key)).split(".")[0])
				groupb=int(str(getattr(iterator[j],key)).split(".")[0])

				if groupa>groupb:
					tmp=iterator[i]
					iterator[i]=iterator[j]
					iterator[j]=tmp

				elif groupa==groupb:
					indexa=int(getattr(iterator[i],key).split(".")[1])
					indexb=int(getattr(iterator[j],key).split(".")[1])
					if indexa>indexb:
						tmp=iterator[i]
						iterator[i]=iterator[j]
						iterator[j]=tmp

	except:
		print(traceback.format_exc())
	finally:
		return iterator



"""
任务调度
"""
def gettaskid():
	"""
	任务id
	"""
	# s=str(time.time())
	# new_md5 = md5()
	# new_md5.update(s.encode(encoding='utf-8'))
	# return new_md5.hexdigest()

	return base64.b64encode(str(time.time()).encode()).decode()



def getbuiltin(filename='builtin.py'):
	"""获取内置函数列表 model.Function形式组装
	"""

	path=os.path.join(os.path.dirname(__file__),filename)

	list_=[]
	with open(path,encoding='utf-8') as f:
		content=f.read()
		#print(content)
		methodnames=re.findall("def\s+(.*?)\(", content)

		for methodname in methodnames:
			f=Function() 
			f.name=methodname
			f.description=eval(methodname).__doc__.strip()
			f.kind='内置函数'
			f.createtime=f.updatetime='*'
			list_.append(f)

	return list_
"""
自定义函数管理
"""
class Fu:
	@classmethod
	def load_data(cls,id_=None):
		"""
		更新本地函数文件
		"""
				
		print("*"*20)
		print("开始更新本地函数信息..")

		try:
			list_=list(models.Function.objects.all())
			for x in list_:

				author=str(x.author)
				filename="func_%s"%x.flag
				body=x.body
				path=os.path.join(os.path.dirname(__file__),'Function',author)

				if not os.path.exists(path):
					os.makedirs(path)
				# print("path=>",path)
				#add __init__.py
				initpath=os.path.join(path,"__init__.py")
				if not os.path.exists(initpath):
					with open(initpath,'w'):
						pass

				path=os.path.join(path,filename+'.py')
				with open(path,'w',encoding='utf-8') as f:
					#print("body=>",body)
					print(type(body))
					a=base64.b64decode(body).decode(encoding='utf-8')
					#print(a)
					f.write(a)


				if id_ is not None and id_==x.id:
					print("*"*20)
					print("更新函数:%s 完毕."%x.name)
					print("*"*20)
					return 0

			print("*"*20)
			print("更新所有函数完毕.")
			print("*"*20)
			return 0

		except Exception as e:
			print(e)
			#traceback.print_exc(e)
			print("*"*20)
			print("更新函数失败.")
			print("*"*20)
			return 1

	@classmethod
	def _md5(cls,s):
		"""
		函数文件名标识
		"""
		new_md5 = md5()
		new_md5.update(s.encode(encoding='utf-8'))
		return new_md5.hexdigest()

	@classmethod
	def tzm_compute(cls,src,pattern):
		"""
		计算方法特征码
		通过pattern从src字符串获取方法名和参数串计算特征码
		"""
		pool=[chr(x) for x in range(97,123)]
		m=re.findall(pattern, src)
		funcname=m[0][0]
		paramlist=m[0][1].split(",")
		size=len(paramlist)
		paramstr=",".join(pool[0:size])
		final="%s(%s)"%(funcname,paramstr)
		print('final=>',final)

		return cls._md5(final)

	@classmethod
	def call(cls,funcobj,call_str,builtin=False):

		# print("内置=>",builtin)
		# print('调用=》',call_str)
		try:
			res=None

			if builtin is True:
				#print('callstr=>',call_str)
				try:
					call_str=call_str.replace('\n','')
					print('调用原表达式=>',call_str)
					res=eval(call_str)

					# if res[0] is not 'success':
					# 	return res
					
				except:
					try:
						methodname=call_str.split('(')[0]
						print('methodname=>',methodname)
			
						s1=re.findall('\((.*?),taskid=', call_str)[0]#sql
						s2=re.findall('taskid=(.*?),', call_str)[0]#taskid
						s3=re.findall('callername=(.*?)\)', call_str)[0]#callername

						print('s1=%s\ns2=%s\ns3=%s'%(s1,s2,s3))

						argstr=re.findall('\((.*)\)',call_str)[0]
						# arglist=argstr.split(',')
						# print('arglist=>',arglist)
						# print('size=>',len(arglist))
						#print('methodname=>',methodname)
						#print('argstr=>',argstr)
						call_str=''
						if argstr.strip():
							call_str='%s(\"%s\",taskid=%s,callername=%s)'%(methodname,s1,s2,s3)
							print('参数加双引号后表达式=>',call_str)
						else:
							call_str='%s()'%(methodname,)
							#call_str1='createPhone()'
							#print(eval(call_str1))

						print('最终计算=>',call_str)
						res=eval(call_str)
						if res[0] is not 'success':
							return res
							
					except:
						print(traceback.format_exc())
						return('error',"非法表达式[%s]"%call_str)
				
				print("调用表达式:%s 结果为:%s"%(call_str,res))
			else:
				user=funcobj.author
				flag=funcobj.flag
				f=__import__('manager.Function.%s.func_%s'%(user,flag),fromlist=True)
				callstr="f.%s"%(call_str)
				#print(callstr)
				res=eval(callstr)
				print("调用表达式:%s 结果为:%s"%(callstr,res))


			return ('success',res)
			
			# if res[0] is 'success':
			# 	return (res)
			# else:
			# 	return('fail',res)
		except Exception as e:
			print(traceback.format_exc())
			return ('error','调用表达式[%s]异常[%s]'%(call_str,traceback.format_exc()))

	@classmethod
	def getfuncname(cls,body):
		return re.findall("def[\s+]{1,}(.*?)\(.*?\):", body)



class EncryptUtils:
	'''
	加密工具
	'''
	# Des CBC
	# 自定IV向量
	Des_IV ='itfdesiv'
	key='blackstone20191111'

	@staticmethod
	def des_encrypt(str_):
		# str 明文password
		# key uid
		Des_Key = (EncryptUtils.key+"0000")[0:8]
		k = des(Des_Key, CBC,EncryptUtils.Des_IV, pad=None, padmode=PAD_PKCS5)
		EncryptStr = k.encrypt(str_)
		return base64.b64encode(EncryptStr).decode() #转base64编码返回

	@staticmethod
	def des_decrypt(str_):
		# str 密文password
		# key uid
		Des_Key = (EncryptUtils.key+"0000")[0:8]
		EncryptStr = base64.b64decode(str_)
		#print(EncryptStr)
		k = des(Des_Key, CBC,EncryptUtils.Des_IV, pad=None, padmode=PAD_PKCS5)
		DecryptStr = k.decrypt(EncryptStr)
		return DecryptStr.decode()

	@staticmethod
	def base64_encrypt(str_):
		return base64.b64encode(str_.encode('utf-8')).decode()

	@staticmethod
	def base64_decrypt(str_):
		return base64.b64decode(str_).decode(encoding='utf-8')

	@staticmethod
	def md5_encrypt(str_):
		return md5(str_.encode('utf-8')).hexdigest()
