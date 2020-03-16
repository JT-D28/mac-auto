#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-09-27 14:45:12
# @Author  : Blackstone
# @to      :
from . import models
from django.conf import settings
from login  import models as md
from .core import ordered,Fu,getbuiltin,EncryptUtils
from .db import Mysqloper
from .context import set_top_common_config,viewcache,gettestdatastep,gettestdataparams,get_task_session,clear_task_session
import re,traceback,redis,time,threading,smtplib, requests,json,warnings,datetime,socket
import copy,base64,datetime,xlrd
from email.mime.text import MIMEText
from email.utils import formataddr,parseaddr
from email.header import Header

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET



##支持的运算
_op=('==','>=','<=','!=')
#用户变量缓存 key=user.varname
__varcache=dict()

#记录变量名的替换过程 方便追溯
#单个表达式替换时记录 计算完成后释放
# __replace_route=dict()

#计划运行时 用户临时变量存放 结束清除
_tempinfo=dict()

##任务集
#{{'username1':{'taskid1':['planid1','planid2']}}}
_taskmap=dict()


def db_connect(config):
    '''
    测试数据库连接
    '''
    print('==测试数据库连接===')

    conn=None

    try:

        # print(len(conname),len(conname.strip()))
        description=config['description']
        dbtype=config['dbtype']
        dbname=config['dbname']
        #oracle不需要这两项
        host=config['host']
        port=config['port']
        #
        user=config['username']
        pwd=config['password']

        # print("=>没查到可用配置,准备新配一个")
        print("数据库类型=>",dbtype)
        print("数据库名(服务名|SID)=>",dbname)
        print("数据库地址=>",host,port)
        print("数据库账号=>",user,pwd)


        if dbtype.lower()=='oracle_servicename':
            import cx_Oracle

            dsn=cx_Oracle.makedsn(host,int(port),service_name=dbname)
            conn=cx_Oracle.connect(user,pwd,dsn)

        elif dbtype.lower()=='oracle_sid':
            import cx_Oracle
            dsn=cx_Oracle.makedsn(host,int(port),sid=dbname)
            conn=cx_Oracle.connect(user,pwd,dsn)

        elif dbtype.lower()=='mysql':
        	import pymysql
	        conn = pymysql.connect(db=dbname, host=host,
	                                    port=int(port),
	                                    user=user,
	                                    password=pwd,
	                                    charset='utf8mb4')

        else:
            return ('fail','连接类型不支持')

        return ('success','数据库[%s]连接成功!.'%description)


    except Exception as e:
        error=traceback.format_exc()
        return ('error','连接异常->%s'%error)



def gettaskresult(taskid):
	detail={}
	spend_total=0

	res=models.ResultDetail.objects.filter(taskid=taskid)
	# print("size=>",list(res))
	plan=list(res)[0].plan
	planname=plan.description
	planid=plan.id
	##这里order表会变
	#caseids=[x.follow_id for x in models.Order.objects.filter(main_id=planid,kind='case').order_by('value')]
	caseids=list(set([ r.case.id for r in list(res)]))
	cases=[models.Case.objects.get(id=caseid) for caseid in caseids]
	#cases=set(x.case for x in list(res))

	#print(cases)
	detail['planname']=planname
	detail['planid']=planid
	detail['taskid']=taskid
	detail['cases']=[]
	detail['success']=0
	detail['fail']=0
	detail['skip']=0

	detail['min']=99999
	detail['max']=0
	detail['average']=0


	for d in cases:
		caseobj={}
		case=d
		casename=case.description
		caseid=case.id
		#caseorder=models.Order.objects.get(main_id=planid,follow_id=caseid,kind='case').value

		# caseobj['caseorder']=caseorder
		caseobj['casename']=casename
		if caseobj.get("steps",None) is None:
			caseobj['steps']=[]
		caseid=case.id
		step_query=list(models.ResultDetail.objects.filter(taskid=taskid,case=case))
		for x in step_query:
			stepobj={}
			step=x.businessdata
			stepobj['num']=models.Order.objects.get(main_id=case.id,follow_id=step.id,kind='step').value
			stepname=step.businessname
			print('step=>',stepname)
			result=x.result
			if 'success'==result:
				detail['success']=detail['success']+1

			elif 'fail'==result:
				detail['fail']=detail['fail']+1	

			elif 'skip'==result:	
				detail['skip']=detail['skip']+1	


			error=x.error
			stepobj['businessname']=x.businessdata.businessname
			stepobj['result']=result
			stepobj['error']=error
			#stepobj['api']=re.findall('\/(.*?)[?]',step.url)[0] or step.body
			stepinst=None
			try:
				error,stepinst=gettestdatastep(step.id)
				stepobj['stepname']=stepinst.description

				stepobj['api']=re.findall('\/(.*?)[?]',stepinst.url)[0]
			except:
				stepobj['api']=stepinst.body

			stepobj['itf_check']=step.itf_check
			stepobj['db_check']=step.db_check
			stepobj['spend']=models.ResultDetail.objects.get(taskid=taskid,plan=plan,case=case,businessdata=step).spend
			spend_total+=int(stepobj['spend'])
			if int(stepobj['spend'])<=int(detail['min']):
				detail['min']=stepobj['spend']

			if int(stepobj['spend'])>int(detail['max']):
				detail['max']=stepobj['spend']

			caseobj.get('steps').append(stepobj)

		detail.get("cases").append(caseobj)

	detail['total']=detail['success']+detail['fail']+detail['skip']
	if detail['success']==detail['total']:
		detail['result']='pass'
	else:
		detail['result']='fail'


	try:
		detail['average']=int(spend_total/detail['total'])
	except:
		detail['average']='-1'

	try:
		detail['success_rate']=str("%.2f"%(detail['success']/detail['total']))
	except:
		detail['success_rate']='-1'

	return detail


def check_user_task():
	def run():
		# while True:
		# 	time.sleep(2)
		#print("do task.")
		for username,tasks in _taskmap.items():
			for taskid,plans in tasks.items():
				for planid in plans:
					runplan(planid)


def runplans(username,taskid,planids,kind=None):
	"""
	任务运行
	kind 运行方式 手动其他
	"""
	kindmsg=''
	if kind is not None:
		kindmsg=kind
		#print("kindmsg=>",kindmsg,username,taskid)


	viewcache(taskid,username,kind,"=======开始%s任务【<span style='color:#FF3399'>%s</span>】===="%(kindmsg,taskid))
	for planid in planids:
		threading.Thread(target=runplan,args=(username,taskid,planid,kind,)).start()

	
def runplan(callername,taskid,planid,kind=None):
	'''


	'''
	groupskip=[]

	try:
		plan=models.Plan.objects.get(id=planid)

		dbid=plan.db_id
		if dbid:
			desp=models.DBCon.objects.get(id=int(dbid)).description
			set_top_common_config(taskid, desp,src='plan')


		#username=plan.author.name
		username=callername
		# viewcache("username=>",username)
		viewcache(taskid,username,kind,"开始执行计划[<span style='color:#FF3399'>%s</span>]"%plan.description)
		#cases=list(plan.cases.all())
		cases=[models.Case.objects.get(id=x.follow_id)  for x in ordered(list(models.Order.objects.filter(main_id=planid,kind='case')))]
		
		#print(cases)
		result,error="",""
		caseresult=[]
		planresult=[]

		for case in cases:
			dbid=case.db_id
			if dbid:
				desp=models.DBCon.objects.get(id=int(dbid)).description
				set_top_common_config(taskid, desp,src='case')

			groupskip=[]
			viewcache(taskid,username,kind,"开始执行用例[<span style='color:#FF3399'>%s</span>]"%case.description)
			orderlist=ordered(list(models.Order.objects.filter(kind='step',main_id=case.id)))
			for order in orderlist:
				groupid=order.value.split(".")[0]
				# step=models.Step.objects.get(id=order.follow_id)
				start=time.time()
				spend=0
				if groupid not in groupskip:
					result,error=_step_process_check(callername,taskid,order,kind)
					spend=int((time.time()-start)*1000)

					if result is not 'success':
						groupskip.append(groupid)
				else:
					result,error='skip','skip'


				##保存结果
				print("准备保存结果===")
				detail=models.ResultDetail()
				detail.taskid=taskid
				detail.plan=plan
				detail.case=case
				#detail.step=models.Step.objects.get(id=order.follow_id)
				detail.businessdata=models.BusinessData.objects.get(id=order.follow_id)
				detail.result=result
				detail.error=error
				detail.spend=spend
				detail.save()


				##
				caseresult.append(result)
				##
				if "success" in result:
					result="<span class='layui-bg-green'>%s</span>"%result

				elif "fail" in result:
					result="<span class='layui-bg-red'>%s</span>"%result
				elif "skip" in result:
					result="<span class='layui-bg-orange'>%s</span>"%result

				##
				#print(len(result),len('success'),result=='success')
				if 'success' in result:
					viewcache(taskid,username,kind,"执行结果%s"%(result))
				else:
					if error is False:
						error='表达式不成立'
					viewcache(taskid,username,kind,"执行结果%s 原因=>%s"%(result,error))
					# viewcache(taskid, username,kind,"%s,%s"%('success' in result,result))
				# viewcache(taskid,username,kind,"--"*40)

			casere=(len([x for x in caseresult if x=='success'])==len([x for x in caseresult]))
			planresult.append(casere)
			if casere:
				viewcache(taskid, username,kind,"结束用例[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-green'>success</span>"%case.description)
			else:
				viewcache(taskid, username,kind,"结束用例[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-red'>fail</span>"%case.description)

		#plan
		planre=(len([x for x in planresult])==len([x for x in planresult if x==True]))

		if planre:
			plan.last='success'
			plan.save()
			viewcache(taskid, username,kind,"结束计划[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-green'>success</span>"%plan.description)
		else:
			plan.last='fail'
			plan.save()
			viewcache(taskid, username,kind,"结束计划[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-red'>fail</span>"%plan.description)

		##清除请求session
		clear_task_session('%s_%s'%(taskid,callername))
		##

		_save_builtin_property(taskid,username)
		##发送报告
		config_id=plan.mail_config_id
		if config_id:
			mail_config=models.MailConfig.objects.get(id=config_id)
			user=md.User.objects.get(name=username)
			mail_res=MainSender.send(taskid,user,mail_config)
			print("发送邮件 结果[%s]"%mail_res)
			viewcache(taskid,username,kind,mail_res)

	except Exception as e:
		#traceback.print_exc()
		print(traceback.format_exc())
		viewcache(taskid,username,kind,'执行计划未知异常[%s]'%traceback.format_exc())

	finally:
		clear_data(username, _tempinfo)


			
def _step_process_check(callername,taskid,order,kind):
	"""
	return (resultflag,msg)
	order.follw_id:业务数据id
	"""
	result="not start"
	try:
		#viewcache("f=>",str(order.follow_id))
		businessdata=models.BusinessData.objects.get(id=order.follow_id)
		status,step=gettestdatastep(businessdata.id)

		dbid=step.db_id
		if dbid:
			desp=models.DBCon.objects.get(id=int(dbid)).description
			set_top_common_config(taskid, desp,src='step')

		if status is not 'success':
			return (status,step)

		# step=models.Step.objects.get(id=order.follow_id)
		#username=order.author.name
		username=callername
		viewcache(taskid,username,kind,"--"*100)
		viewcache(taskid,username,kind,"开始执行步骤[<span style='color:#FF3399'>%s-%s</span>] 测试点[<span style='color:#FF3399'>%s</span>]"%(order.value,step.description,businessdata.businessname))
		#print("user=>",step.author)
		user=md.User.objects.get(name=username)
		# db_check=step.db_check
		# itf_check=step.itf_check
		db_check=businessdata.db_check
		itf_check=businessdata.itf_check
		status,paraminfo=gettestdataparams(order.follow_id)
		if status is not 'success':
			return (status,paraminfo)

			print('获取参数信息=>',str(paraminfo))

		if step.step_type=="interface":
			viewcache(taskid,username,kind,"数据校验配置=>%s"%db_check)
			viewcache(taskid,username,kind,"接口校验配置=>%s"%itf_check)

			# text,statuscode,itf_msg=_callinterface(taskid,user,step.url,step.body,step.method,step.headers,step.content_type,step.temp,kind)

			text,statuscode,itf_msg='',-1,''
	
			if step.content_type=='xml':
				text,statuscode,itf_msg=_callsocket(taskid, user, step.url,body=str(paraminfo))
				
			else:
				text,statuscode,itf_msg=_callinterface(taskid,user,step.url,str(paraminfo),step.method,step.headers,step.content_type,step.temp,kind)			
			
			if len(str(statuscode))==0:
				return ('fail',itf_msg)
			elif statuscode==200:
				if db_check:
					res,error=_compute(taskid,user,db_check,type="db_check",kind=kind)
					if res is not 'success':
						print('################db_check###############'*20)
						return ('fail',error)
				# else:
				# 	viewcache(taskid,username,kind,'数据校验没配置 跳过校验')

				if itf_check:
					if step.content_type in('json','urlencode'):
						res,error=_compute(taskid,user,itf_check,type='itf_check',target=text,kind=kind,parse_type='json')
					else:
						res,error=_compute(taskid,user,itf_check,type='itf_check',target=text,kind=kind,parse_type='xml')

					if res is not 'success':
						return ('fail',error)	
				# else:
				# 	viewcache(taskid,username,kind,'接口校验没配置 跳过校验')	

				return ('success','')
			else:
				return ('fail','statuscode=%s'%statuscode)


			if itf_msg:
				print('################itf-msg###############'*20)
				return ('fail',itf_msg)
			
		elif step.step_type=="function":
			viewcache(taskid,username,kind,"数据校验配置=>%s"%db_check)
			# viewcache("接口返回校验=>%s"%itf_check)

			# methodname=re.findall("(.*?)\(.*?\)", step.body.strip())[0]
			# builtinmethods=[x.name for x in getbuiltin() ]
			# builtin=(methodname in builtinmethods)

			
			res,msg=_callfunction(user,step.related_id,step.body,paraminfo,taskid=taskid)

			# print('fjdajfd=>',res,msg)
			if res is not 'success':
				return res,msg

			if db_check:
				res,error=_compute(taskid,user,db_check,type='db_check',kind=kind)
				if res is not 'success':
					return ('fail',error)
				else:
					return ('success','')
			else:
				# viewcache(taskid,username,kind,'数据校验没配置 跳过校验')
				return ('success','')

	except Exception as e:
		#traceback.print_exc()
		print(traceback.format_exc())
		return ("error","执行任务[%s] 未处理的异常[%s]"%(taskid,traceback.format_exc()))


# def getstepparaminfo(businessdatainst,kind='db'):
# 	'''
# 	函数->数组
# 	接口->字典
# 	'''
		
# 	if businessdatainst is None:
# 		return ('success',[])


# 	if kind=='db':
# 		status,stepinst=gettestdatastep(businessdatainst)

# 		if status is not 'success':
# 			return (status,stepinst)

# 		if stepinst.step_type=='interface':
# 			res={}
# 			paraminfo=list(businessdatainst.params.all())
# 			for p in paraminfo:
# 				#print(p.key,p.value)
# 				if p.key=='LAY_TABLE_INDEX':
# 					continue;
# 				res[p.key]=p.value
# 			return ('success',res)
# 		elif stepinst.step_type=='function':
# 			print('bussinessid=>',businessdatainst.id)
# 			paraminfo=list(businessdatainst.params.all())
# 			return ('success',[ str(p.value) for p in paraminfo])

# 		else:
# 			return('error','步骤类型异常=>%s'%stepinst.step_type)

# 	else:

# 		#需要剔除无用key
# 		_filter=list(_businessdatatmp.keys())
# 		res=[]

# 		sb=eval(str(businessdatainst))[0]

# 		for k,v in sb.items():
# 			if k not in _filter and k is not 'LAY_TABLE_INDEX':
# 				res.append(v)

# 		return ('success',res)



# def gettestdatastep(businessdatainst):
# 	try:
# 		steps=models.Step.objects.all()
# 		step=[step for step in steps if businessdatainst in list(step.businessdatainfo.all())][0]
# 		return ('success',step)
# 	except:
# 		print(traceback.format_exc())
# 		return ('error','获取业务数据所属步骤异常 业务ID=%s'%businessdatainst.id)



def _callsocket(taskid,user,url,body=None,kind=None,timeout=1024):
	"""
	xml报文请求
	"""

	def _getback(sock):
		recvdata = ''
		# sock.setblocking(0)
		sock.settimeout(timeout)
		try:
			lenstr = sock.recv(25)
			recvdata += lenstr.decode('GBK')
			data = sock.recv(int(lenstr[15:23]))
			data = data.decode('GBK')
			recvdata += data
		except:
			print(traceback.format_exc())
	
		finally:
			sock.close()
			return recvdata
	
	try:

		##
		body_rv=_replace_variable(user, body);
		if body_rv[0] is not 'success':
			return ('','',body_rv[1])
		body_rp=_replace_variable(user, body_rv[1])
		if body_rp[0] is not 'success':
			return ('','',body_rp[1])

		body=body_rp[1]


		cs=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		# cs.setblocking(False)
		socket.setdefaulttimeout(30)
		cs.settimeout(timeout)
		host=url.split(':')[0].strip()
		port=url.split(':')[1].strip()
		time.sleep(2)
		cs.connect((str(host),int(port)))		
		# ms=re.findall('\<\/.*?\>', body)
		# for m in ms:
		# 	body=body.replace(m, m+'\n')

		
		length=str(len(body.encode('GBK'))).rjust(8)
		print('Content-Length=>',length)
		sendmsg = 'Content-Length:' + str(length) + '\r\n' + body

		viewcache(taskid, user.name,None,'执行socket请求')
		viewcache(taskid, user.name,None,"<span style='color:#009999;'>请求IP=>%s</span>"%host)
		viewcache(taskid, user.name,None,"<span style='color:#009999;'>请求端口=>%s</span>"%port)
		viewcache(taskid, user.name,None,"<span style='color:#009999;'>发送报文=><xmp style='color:#009999;'>%s</xmp></span>"%sendmsg)
		# viewcache(taskid, user.name,None,"<span style='color:#009999;'>body=>%s</span>"%sendmsg)
		
		cs.sendall(bytes(sendmsg,encoding='GBK'))

		# recv_bytes=cs.recv(1024)
		# responsexml=b''

		# while True:
		# 	recv_bytes =cs.recv(1024)
		# 	print(2222)
		# 	responsexml+=recv_bytes
		# 	if not len(recv_bytes):
		# 		break;

		return _getback(cs),200,''


	except:
		cs.close()
		err=traceback.format_exc()
		print(err)
		return ('','',err)


def _callinterface(taskid,user,url,body=None,method=None,headers=None,content_type=None,props=None,kind=None):
	"""
	返回(rps.text,rps.status_code,msg)
	"""
	##url data headers过滤
	url_rp=_replace_property(user,url)
	if url_rp[0] is not 'success':
		return ('','',url_rp[1])
	url_rv=_replace_variable(user,url_rp[1],taskid=taskid)
	if url_rv[0] is not 'success':
		return('','',url_rv[1])
	url=url_rv[1]

	data_rp=_replace_property(user,body)
	if data_rp[0] is not 'success':
		return('','',data_rp[1])
	data_rv=_replace_variable(user,data_rp[1],taskid=taskid)
	if data_rv[0] is not 'success':
		return ('','',data_rv[1])
	body=data_rv[1]

	#body=json.loads(body)

	#print(type(headers))

	if headers is None or len(headers.strip())==0:
		headers={}

	headers_rp=_replace_property(user,str(headers))
	if headers_rp[0] is not 'success':
		return('','',headers_rp[1])
	headers_rv=_replace_variable(user,headers_rp[1],taskid=taskid)
	if headers_rv[0] is not 'success':
		return ('','',headers_rv[1])

	try:
		headers=eval(headers_rv[1])
	except:
		return ('','','接口请求头格式不对 请检查')

	##
	
	default={'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36"}
	
	if content_type=='json':
		#body=body.encode('utf-8')
		default["Content-Type"]='application/json;charset=UTF-8'
		body=json.dumps(eval(body))
	elif content_type=='xml':
		default["Content-Type"]='application/xml'
	elif content_type=='urlencode':
		#body=body.encode('utf-8')
		#body=json.loads(body)
		try:
			body=eval(body)

		except :
			print('参数转化异常：',traceback.format_exc())
			return ('','','接口参数格式不对 请检查..')
		default["Content-Type"]='application/x-www-form-urlencoded;charset=UTF-8'
	elif content_type=='xml':
		isxml=0

	else:
		raise NotImplementedError("content_type=%s没实现"%content_type)
	viewcache(taskid,user.name,kind,"执行接口请求=>")
	viewcache(taskid,user.name,kind,"<span style='color:#009999;'>url=>%s</span>"%url)
	viewcache(taskid,user.name,kind,"<span style='color:#009999;'>method=>%s</span>"%method)
	viewcache(taskid,user.name,kind,"<span style='color:#009999;'>content_type=>%s</span>"%content_type)
	viewcache(taskid,user.name,kind,"<span style='color:#009999;'>headers=>%s</span>"%{**default,**headers})
	# viewcache(taskid,user.name,kind,"body[old]=%s"%body)
	viewcache(taskid,user.name,kind,"<span style='color:#009999;'>params=>%s</span>"%body)

	#print("method=>",method)
	rps=None

	if method=="get":
		session=get_task_session('%s_%s'%(taskid,user.name))
		rps=session.get(url,params=body,headers={**default,**headers})
	elif method=='post':
		#print(body.decode())
		#print({**default,**headers})
		#print(body)
		session=get_task_session('%s_%s'%(taskid,user.name))
		rps=session.post(url,data=body,headers={**default,**headers})

		#print("textfdafda=>",rps.text)
	else:
		raise NotImplementedError("请求方法%s没实现。"%method)

	###响应报文中props处理
	_find_and_save_property(user,props, rps.text)
	#print("text=>",rps.text)
	return (rps.text,rps.status_code,"")

def _callfunction(user,functionid,call_method_name,call_method_params,taskid=None):
	"""
	内置方法 functionid=None
	call_method_params ->tuple
	返回(调用结果,msg)
	"""
	f=None
	builtin=None
	# methodname=re.findall("(.*?)\(.*?\)", call_str.strip())[0]
	methodname=call_method_name

	builtinmethods=[x.name for x in getbuiltin() ]
	builtin=(methodname in builtinmethods)

	try:
		f=models.Function.objects.get(id=functionid)
	except:
		pass

	#flag
	if call_method_name in('dbexecute2','dbexecute'):
		call_method_params.append("taskid='%s'"%taskid)
		call_method_params.append("callername='%s'"%user.name)

	call_str='%s(%s)'%(call_method_name,','.join(call_method_params))
	# print('$'*100)
	print('测试函数调用=>',call_str)
	ok=_replace_variable(user, call_str,src=1,taskid=taskid)
	
	res,call_str=ok[0],ok[1]
	if res is not 'success':
		return (res,call_str)

	return Fu.call(f,call_str,builtin=builtin)


def _compute(taskid,user,checkexpression,type=None,target=None,kind=None,parse_type='json'):
	"""
	计算各种校验表达式 
	多个时 分隔符 |
	返回(success/fail,执行结果/消息)
	"""
	try:
		# expectedexpression=_legal(checkexpression)
		expectedexpression=checkexpression
		checklist=[x for x in expectedexpression.strip().split("|") if len(x)>0]
		resultlist=[]
		if type=='db_check':
			for item in checklist:
				old=item
				item=_legal(item)
				ress=_eval_expression(user,item,taskid=taskid)
				print('ress1=>',ress)

				if ress[0] is 'success':
					viewcache(taskid,user.name,None,"判断表达式[%s] 结果[%s]"%(old,ress[0]))
				else:
					viewcache(taskid,user.name,None,"判断表达式[%s] 结果[%s] 原因[%s]"%(old,ress[0],ress[1]))

				resultlist.append(ress)

		elif type=="itf_check":
			viewcache(taskid,user.name,kind,"<span style='color:#009999;'>请求响应=><xmp style='color:#009999;'>%s</xmp></span>"%target)

			for item in checklist:
				old=item
				item=_legal(item)
				ress=_eval_expression(user,item,need_chain_handle=True,data=target,taskid=taskid,parse_type=parse_type)
				print('ress2=>',ress)
				if ress[0] is 'success':
					viewcache(taskid,user.name,None,"判断表达式[%s] 结果[%s]"%(old,ress[0]))
				else:
					msg=ress[1]
					if msg is False:
						msg='表达式不成立'
					viewcache(taskid,user.name,None,"判断表达式[%s] 结果[%s] 原因[%s]"%(old,ress[0],msg))


				resultlist.append(ress)


		else:
			return ('error','计算表达式[%s]异常[_compute type传参错误]'%checkexpression)
		#print("结果列表=>",resultlist)
		# errmsgs=[flag for flag,msg in resultlist if isinstance(x,(str))]
		failmsg='请检查_compute函数,_eval_expression函数返回fail时没传失败消息'

		print('resultlist=>',resultlist)
		notsuccessmsg=[msg for flag,msg in resultlist if flag is not 'success']
		if len(notsuccessmsg)>0:
			failmsg=notsuccessmsg[0]

		res=len([flag for flag,msg in resultlist if flag is 'success' ])==len(resultlist)
		if res is True:
			return('success','')
		else:
			return('fail',failmsg)

	except Exception as e:
		return('error','计算表达式[%s]异常[%s]'%(checkexpression,traceback.format_exc()))
		
def _separate_expression(expectedexpression):
	# _op=('==','>=','<=','!=')
	for op in _op:
		if op in expectedexpression:
			k=expectedexpression.split(op)[0]
			v=expectedexpression.split(op)[1]
			return k,v,op

	raise RuntimeError("不能分割的表达式=>%s"%expectedexpression)
	
def _legal(ourexpression):

	res=None

	if "|" in ourexpression:
		res=[]
		seplist=ourexpression.split("|")
		for sep in seplist:
			res.append(_replace(sep))

		return "|".join(res)

			
	else:
		res=_replace(ourexpression)
	
	return res


def _replace(expressionsep):
	try:
		eval(expressionsep)
	except Exception as e:
		list_=re.findall("=", expressionsep)
		if len(list_)==1:
			expressionsep=expressionsep.replace("=","==")
		elif 'true' in expressionsep:
			expressionsep=expressionsep.replace('true','True')
		elif 'false' in expressionsep:
			expressionsep=expressionsep.replace('false','False')
		else:
			msg="不能合法化的表达式!=>%s"%expressionsep
			#viewcache(msg)
			raise RuntimeError(msg)
	finally:
		return expressionsep

def _eval_expression(user,ourexpression,need_chain_handle=False,data=None,direction='left',taskid=None,parse_type='json'):
	"""返回情况
	返回(success,'')
	返回(fail,failmsg)
	返回(error,errmsg)
	1.表达式校验通过放回True
	2.校验失败 返回表达式校验失败信息
	3.发生异常 返回异常简述

	执行时 先属性替换=>变量替换=>链式校验

	接口校验需要开启need_chain_handle=True
	接口验证时 direction=left ,临时变量设置时 为right
	"""

	#res=None
	exp=None
	try:

		#print("ourexpression=>",ourexpression)
		exp_rp=_replace_property(user, ourexpression)
		# print('exp-pr=>',exp_rp)
		if exp_rp[0] is not 'success':
			return exp_rp

		exp_rv=_replace_variable(user,exp_rp[1],taskid=taskid)
		if exp_rv[0] is not 'success':
			return exp_rv
		# print('exp_rv=<',exp_rv)

		exp=exp_rv[1]

		res=None

		if need_chain_handle is True:
			
			k,v,op=_separate_expression(exp)
			# print(k,v,op)
			data=data.replace('null',"'None'").replace('true',"'True'").replace("false","'False'")
			# print('data=>',data)
			
			p=None

			if parse_type=='json':
				p=JSONParser(data)
			elif parse_type=='xml':
				# print('类型=>',type(parse_type))
				# print('data=>')
				# print(data)
				#消除content-type首行
				data='\n'.join(data.split('\n')[1:])
				p=XMLParser(data)

			k=p.getValue(k)
			# try:
			# 	if eval(str(k)) in(None,True,False):
			# 		k=str(k)
			# 		v=str(v)
			# except:
			# 	pass

			if v == 'true':
				v='True'
			elif v == 'false':
				v='False'
			elif v == 'null':
				v='None'

			print('表达式合成{%s(%s),%s(%s),%s(%s)}'%(k,type(k),op,type(op),v,type(v)))

			if type(k) == type(v):
				exp="".join([str(k),op,str(v)])
			else:
				return ('fail','表达式[%s]校验不通过 期望[%s]和实际类型[%s]不一致'%(ourexpression,type(v),type(k)))

			#res=eval(exp)

			print("实际计算表达式[%s] 结果[%s]"%(exp,eval(exp)))
		return ('success','') if eval(exp) is True else ('fail','表达式%s校验失败'%ourexpression)
	except:
		print(traceback.format_exc())
		print('表达式等号两边加单引号后尝试判断..')

		#return ('error','表达式[%s]计算异常[%s]'%(ourexpression,traceback.format_exc()))
		try:
			print('_op=>',_op)
			print('_exp=>',exp)
			for op in _op:
				if op in exp:
					key=exp.split(op)[0]
					value=exp.split(op)[1]
					print('key=>',key)
					print('value=>',value)
					print('fdjalfd=>')

					res= eval("'%s'%s'%s'"%(str(key),op,str(value)))
					print('判断结果=>',res)
					if res is True:
						return ('success',res)
					else:
						return('fail',res)

		except:
			print('表达式计算异常.')
			return ('error','表达式[%s]计算异常[%s]'%(ourexpression,traceback.format_exc()))



def _replace_variable(user,str_,src=1,taskid=None):
	"""
	返回(success,替换后的新字符串)
	返回(fail,错误消息)
	src:同_gain_compute()

	"""
	try:
		old=str_
		varnames=re.findall('{{(.*?)}}',str_)
		#print(varnames)
		for varname in varnames:
			# try:
			#print("变量名称=>%s"%varname)
			#print("查找变量 author=%s key=%s"%(user.name,varname))
			var=models.Variable.objects.get(key=varname)
			gain_rv=_replace_variable(user,var.gain,src=src,taskid=taskid)
			if gain_rv[0] is not 'success':
				#print(11)
				return gain_rv
			gain=gain_rv[1]

			value_rv=_replace_variable(user, var.value,src=src,taskid=taskid)
			if value_rv[0] is not 'success':
				#print(1221)
				return value_rv
			value=value_rv[1]

			is_cache=var.is_cache

			if len(gain)==0 and len(value)==0:
				warnings.warn("变量%s的获取方式和默认值至少填一项"%varname)
			elif len(gain)>0 and len(value)>0:
				old=old.replace('{{%s}}'%varname,value)
				#__replace_route["%s.%s"%(user.name,varname)]=value
				warnings.warn('变量%s获取方式和值都设定将被当做常量，获取方式和缓存失效'%varname)


			elif len(gain)==0 and len(value)>0:
				old=old.replace('{{%s}}'%varname,value)
				#__replace_route["%s.%s"%(user.name,varname)]=value

			elif len(gain)>0 and len(value)==0:
				v=None
				if is_cache is True:
					v=__varcache.get('%s.%s'%(user,varname)) 
					if v is None:
						v=_gain_compute(user,gain,src=src,taskid=taskid)
						if v[0] is not 'success':
							#print(14441)
							return v
						else:
							v=v[1]
				else:
					v=_gain_compute(user,gain,src=src,taskid=taskid)
					if v[0] is not 'success':
						#print(11999)
						return v
					else:
						v=v[1]
	
					# if v is None:
					# 	return ('error','')
					old=old.replace('{{%s}}'%varname,v)

		return ('success',old)
	except Exception as e:
		print(traceback.format_exc())
		return ('error','字符串[%s]变量替换异常[%s] 请检查包含变量是否已配置'%(str_,traceback.format_exc()))

def is_valid_where_sql(call_str):
	'''
	获取方式输入验证
	'''
	if call_str is None or len(call_str.strip())==0:
		return True

	call_str=call_str.strip()
	is_function=_is_function_call(call_str)
	print('is_function=>',is_function)

	if is_function:return True
	if '@' not in call_str:
		return False

	not_expected_end_char=[';','；']
	sql=call_str.split('@')[0]
	for ch in not_expected_end_char:
		if sql[-1]==ch:
			return False


	return True

def is_valid_gain_value(gain,value):

	if gain and value:
		return '获取方式和value只能选填一个'
	if not gain and not value:
		return '获取方式和value至少选填一个'

	if len(gain.strip())==0 and len(value.strip())==0:
		return '获取方式和value至少选填一个'

	return True


def _is_valid_where_symmetric(input):
	'''
	特殊字符{[('" 左右对称性验证
	'''
	_mata=('{','[','(','\'','\"')
	m=[x for x in input if x in _mata]
	if m%2 is not  0:
		return False

	size=len(m)
	for x in range(size/2):
		if m[x]!=m[size-x-1]:
			return False



	return True



def _is_function_call(call_str):
	'''
	判断获取方式类别
	1.是否有空格
	2.是否带()
	'''
	res_1=re.findall('\s+', call_str)
	res_2=re.findall("\w{1,}\([\w,]*\)",call_str)

	return True if len(res_1)==0 and len(res_2)>0 else False

def _is_sql_call(call_str):
	pass


def _gain_compute(user,gain_str,src=1,taskid=None):
	"""
	获取方式计算  
	返回(success,计算结果)
	返回(fail,错误消息)
	src:1:from sql 2:from function call
	"""
	try:
		# from builtin import *
		# res=re.findall("\w{1,}\([\w,]*\)",gain_str)
		# print('匹配结果=>',res,gain_str)
		if _is_function_call(gain_str):
			##是方法调用
			# tzm=Fu.tzm_compute(gain_str,"(.*?)\((.*?)\)")
			flag=Fu.tzm_compute(gain_str,'(.*?)\((.*?)\)')
			ms=list(models.Function.objects.filter(flag=flag))
			functionid=None
			if len(ms)==0:
				functionid=None
			elif len(ms)==1:
				functionid=ms[0].id
			else:
				functionid=ms[0].id
				warnings.warn('库中存在两个特征码相同的自定义函数')

			a=re.findall('(.*?)\((.*?)\)', gain_str)
			call_method_name=a[0][0]
			call_method_params=a[0][1].split(',')

			# return _callfunction(user, functionid, gain_str)
			return _callfunction(user, functionid, call_method_name,call_method_params,taskid=taskid)
			#return Fu.call(user,tzm,gain_str)

		else:
			#是sql
			op=Mysqloper()
			gain_str_rp=_replace_property(user,gain_str)
			if gain_str_rp[0] is not 'success':
				return gain_str_rp

			gain_str_rv=_replace_variable(user,gain_str_rp[1],taskid=taskid)
			if gain_str_rv[0] is not 'success':
				return gain_str_rv

			gain_str=gain_str_rv[1]
			if src==1:			
				if ';' in gain_str:
					return op.db_execute2(gain_str,taskid=taskid,callername=user.name)
				else:
					return op.db_execute(gain_str,taskid=taskid,callername=user.name)
			else:
				return ('success','"%s"'%gain_str.strip())


	except Exception as e:
	#traceback.print_exc()
		return ('error',traceback.format_exc())


def _replace_property(user,str_):
	"""
	属性右替换
	返回(success,替换后新值)
	返回(fail,错误消息)

	"""
	cur=None
	try:
		old=str_
		username=user.name
		#username=user.name
		#a=re.findall("\$(.*)=", str_)

		print('str_=>',str_)
		b=re.findall("\$\{(.*?)\}", str_)
		#viewcache("b length=>",len(b))
		#c=a+b
		c=b
		for it in c:
			#viewcache("key=>",it)
			#print('tmp==>',it)
			cur=it

			print("取属性==")
			print(_tempinfo,username,it)
			v=_tempinfo.get(username).get(it)


			#viewcache("vvv=>",v)
			if v is None:
				raise RuntimeError('没有定义属性$%s 请先定义'%it)
			old=old.replace(r"${%s}"%it,v)

		#print('属性替换=》',old)

		return ('success',old)
	except Exception as e:
		print(traceback.format_exc())
		return ('error','请检查是否定义属性%s 错误消息:%s'%(cur,traceback.format_exc()))

def _save_builtin_property(taskid,username):
	'''
	测试报告可用内置属性
	 ${TASK_ID}
	 ${TASK_REPORT_URL}
	 ${PLAN_ID}
	 ${PLAN_NAME}
	 ${PLAN_RESULT}
	 ${PLAN_CASE_TOTAL_COUNT}
	 ${PLAN_CASE_SUCCESS_COUNT}
	 ${PLAN_CASE_FAIL_COUNT}
	 ${PLAN_STEP_TOTAL_COUNT}
	 ${PLAN_STEP_SUCCESS_COUNT}
	 ${PLAN_STEP_FAIL_COUNT}
	 ${PLAN_STEP_SKIP_COUNT}
	 #${PLAN_SUCCESS_RATE}
	'''
	detail=gettaskresult(taskid)
	
	base_url=settings.BASE_URL
	url="%s/manager/querytaskdetail/?taskid=%s"%(base_url,taskid)
	save_data(username,_tempinfo,'TASK_ID', detail['taskid'])
	save_data(username,_tempinfo, 'TASK_REPORT_URL', url)
	save_data(username,_tempinfo, 'PLAN_ID', detail['planid'])
	save_data(username,_tempinfo, 'PLAN_NAME', detail['planname'])
	save_data(username,_tempinfo, 'PLAN_RESULT', (lambda:'success' if int(float(detail['success_rate']))==1 else 'fail')())
	save_data(username,_tempinfo, 'PLAN_CASE_TOTAL_COUNT', str(len(detail['cases'])))
	# save_data(username,_tempinfo, 'PLAN_CASE_SUCCESS_COUNT', detail[''])
	# save_data(username,_tempinfo, 'PLAN_CASE_FAIL_COUNT', detail[''])
	save_data(username,_tempinfo, 'PLAN_STEP_TOTAL_COUNT', detail['total'])
	save_data(username,_tempinfo, 'PLAN_STEP_SUCCESS_COUNT', detail['success'])
	save_data(username,_tempinfo, 'PLAN_STEP_FAIL_COUNT', detail['fail'])
	save_data(username,_tempinfo, 'PLAN_STEP_SKIP_COUNT', detail['skip'])
	save_data(username,_tempinfo, 'PLAN_SUCCESS_RATE', detail['success_rate'])


def _find_and_save_property(user,dict_str,reponsetext):
	"""
	属性保存 如响应json中没相关字段 则当做字符串
	"""
	cur=None
	#print(type(dict_str),len(dict_str))
	try:
		if dict_str is None or len(dict_str.strip())==0:
			# print('NOOOO'*100)
			return

		d=eval(dict_str)
		# print(reponsetext)
		# print("d=>",d)
		for k,v in d.items():
			cur=k
			p=JSONParser(reponsetext)
			print('================_find_and_save_property==========')
			print(p)
			print(k,v)
			v1=p.getValue(v)
			print(user.name,k,v1)
			#viewcache("v1=>",v1)
			save_data(user.name, _tempinfo, k, v1)

	except Exception as e:
		print(traceback.format_exc())
		raise RuntimeError("用户%s属性缓存失败=>属性%s"%(user.name,cur))


def save_data(username,d,k,v):
	"""
	"""
	try:
		if d.get(username) is None:
			d[username]={}

		d[username][k]=v

		print('存属性==')
		print(username,k,v)

		viewcache(username,"用户%s缓存数据=> %s=%s"%(username,k,v))

	except:
		raise RuntimeError("存property失败=>%s"%k)

def clear_data(username,d):
	"""
	清空用户相关缓存信息 
	"""
	for key in list(d.keys()):
		if username in key:
			del d[key]

	viewcache(username,"清空用户%s缓存信息"%username)

class Struct(object):

	def __init__(self,data):
		self.datastr=str(data)

	def getValue(self,xpath):
		raise NotImplementedError("")


	def translate(self,chainstr):
		raise NotImplementedError("")

# class XMLParser(Struct):
# 	def __init__(self,data):
# 		pass

# 	def getValue(self,xpath):
# 		pass

# 	def translate(self,chainstr):
# 		pass

class XMLParser(Struct):
    def __init__(self,data):
        self.root=ET.fromstring(str(data))

    def getValue(self,xpath):
        
        print('查找=>',xpath)
        result=''
        route_path=''
        chainlist=xpath.split('.')

        if len(chainlist)>1:
            chainlist.pop(0)
        else:
            pass

        for chain in chainlist:
            o=dict()
            index=None
            propname=None
            tagname=None
            ms=re.findall('\[(.*?)\]', chain)
            # print('ms=>',ms)
            kh=None

            for m in ms:
                try:
                    index=str(int(m))
                except:
                    propname=m

            tagname=re.sub(r'\[.+\]', '', chain)
            chain=re.sub('[.*?]', '', chain)

            route_path+='/'+tagname

            if index:
                route_path+='[%s]'%str(int(index)+1)
            else:
                 route_path+='[1]'

            if propname:
                # print('search=>','.'+route_path)
                # print('res=>',self.root.find('.'+route_path).attrib)
                return self.root.find('.'+route_path).attrib.get(propname,'None')
        try:
            # print('search=>','.'+route_path)
            return self.root.find('.'+route_path).text
        except:
            return 'None'


class JSONParser(Struct):

	def __init__(self,data):
		#print("88"*200)
		#print(data)
		# data=data.replace("\'","\"").replace("None","null").replace("True","true")
		#print(data)
		
		#self.obj=json.loads(data)
		#print("传入=>",data)


		self.obj=eval(self._apply_filter(data))

		#print("待匹配数据=>",self.obj)
	
	def _apply_filter(self,msg):
		#print("leix=",type(msg))
		msg=msg.replace("true","True").replace("false","False").replace("null","None")
		#print(msg)
		return msg


	def translate(self,chainstr):

		def is_ok(chainstr):
			stages=chainstr.split(".")
			for x in stages:
				if len(re.findall("^[0-9]\d+$",x))==1:
					return False
			return True

		if is_ok(chainstr)==True:
			stages=chainstr.split(".")
			return "self.obj."+".".join(["get('%s')[%s"%(stage.split("[")[0],stage.split("[")[1])  if "[" in stage else "get('%s')"%stage for stage in stages ])

		else:
			return False


	def getValue(self,chainstr):
		errms='解析数据链[%s]失败 数据链作为值返回'%chainstr
		xpath=self.translate(chainstr)
		if xpath:
			#print("查询=>"+xpath)
			try:
				r=eval(xpath)
				#print("hello."
				#print("type=>",type(r))
				return r
			except:
				print(errms)
				return chainstr
		else:
			print(errms)
			return chainstr


	# def check(self,chainstr,expected):

	# 	#print(type(self.getValue(chainstr)),type(expected))

	# 	return str(self.getValue(chainstr))==str(expected)




class MainSender:
	'''
	测试报告工具类
	'''
	# my_sender='971406187@qq.com'    # 发件人邮箱账号
	# my_pass = 'mafkywyadboibfbj'              # 发件人邮箱密码
	# my_receive={
	# # 'hujj':'15157266151@126.com',
	# # 'hujj2':'971406187@qq.com',
	# 'hujj3':'hujj@fingard.com',
	# # 'chl':"chenhy@fingard.com",
	# # 'fhp':'fuhp@fingard.com',
	# # 'syc':'shanyc@fingard.com',
	# # 'xsl':'xuesl@fingard.com',
	# # 'zby':'zhengby@fingard.com',
	# # 'zjr':'zhanjr@fingard.com'
	# }
	# subject=""
	# workcontent=[

	'1.新框架所有页面 编辑删除[100% 删除没做依赖检查后面加]',
	'2.测试邮件配置分任务[15% 做了部分接口和数据模型调整]',
	'3.迁移脚本优化',
	'4.迁移用例',
	'5.优化',
	'a.所有接口的session失效跳转',
	'b.一些重要bug修复 如步骤和用例调序bug修复',
	'c.删除依赖检查',
	'd.增加测试步骤测试用例时的批量操作',
	'e.增加文本验证规则',
	'f.@字符数据库关联查询 变量输入快捷键'
	'g.详情查看'

	# ]


	@classmethod
	def _format_addr(cls,s):
		name,addr=parseaddr(s)
		return formataddr((Header(name, 'utf-8').encode(), addr))

	# @classmethod
	# def getworkcontent(cls):
	# 	msg=''
	# 	for line in cls.workcontent:
	# 		msg+="<p>%s</p>"%line
	# 	return msg
	@classmethod
	def gethtmlcontent(cls,taskid,rich_text):

		data=gettaskresult(taskid)

		#cls.subject='%s自动化测试报告-%s'%(data['planname'],str(datetime.datetime.now())[0:10])
		cls.subject='%s自动化测试报告-%s'%(data['planname'],'2019-10-31')
		cssstr='<style type="text/css">body{font-family:Microsoft YaHei}.success{color:#093}.fail{color:#f03}.skip{color:#f90}.error{color:#f0f}table{width:95%;margin:auto}th{background-color:#39c;color:#fff}td{background-color:#eee;text-align:center}</style>'

		bodyhtml='<span style="float:right;font-size:1px;font-color:#eee;">%s-%s</span>'%(data['taskid'],data['planid'])
		bodyhtml+='<h2 style="text-align: center;">[%s]接口测试报告</h2>'%data['planname']
		bodyhtml+="<p class='attribute'><strong>测试结果</strong></p>"
		bodyhtml+="<table><tr><th>#Samples</th><th>Failures</th><th>Success Rate</th><th>Average Time</th><th>Min Time</th><th>Max Time</th></tr><tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr></table>"%(data['total'],data['fail'],data['success_rate'],data['average'],data['min'],data['max'])
		bodyhtml+="<strong>测试详情</strong>"

		for case in data['cases']:
			bodyhtml+='<p style="text-indent:2em;" >用例名[%s]</p>'%(case['casename'])
			bodyhtml+='<table>'
			bodyhtml+="<tr><th>执行序号</th><th>结果</th><th>耗时(ms)</th><th>步骤名称</th><th>api</th><th>接口验证</th><th>数据验证</th><th>消息</th></tr>"
			steps=case['steps']
			for step in steps:
				bodyhtml+='<tr>'
				bodyhtml+='<td style="width:100px;">%s</td>'%step['num']
				bodyhtml+='<td style="width:100px;" class="%s">%s</td>'%(step['result'],step['result'])
				bodyhtml+='<td style="width:100px;">%s</td>'%step['spend']
				bodyhtml+='<td style="width:200px;" title="%s">%s</td>'%(step['stepname'],step['stepname'])
				bodyhtml+='<td style="width:200px;">%s</td>'%step['api']
				bodyhtml+='<td style="width:100px;">%s</td>'%step['itf_check']
				bodyhtml+='<td style="width:100px;">%s</td>'%step['db_check']
				bodyhtml+='<td>%s</td>'%step['error']
				bodyhtml+='</tr>'
				
			bodyhtml+='</table>'

		return cssstr+rich_text+'<br/>'+'-'*40+'<br/>'+bodyhtml



	@classmethod
	def send(cls,taskid,user,mail_config):
		ret=0
		error=''
		try:
			is_send_mail=mail_config.is_send_mail
			if is_send_mail=='close':
				return '=========发送邮件功能没开启 跳过发送================='
			sender_name=mail_config.sender_name
			sender_nick=mail_config.sender_nick
			sender_pass=mail_config.sender_pass
			to_receive=mail_config.to_receive
			cc_receive=mail_config.cc_receive
			rich_text_rp=_replace_property(user,mail_config.rich_text)
			rich_text=''
			if rich_text_rp[0] is 'success':
				rich_text_rv=_replace_variable(user,rich_text_rp[1],taskid=taskid)
				if rich_text_rv[0] is 'success':
					rich_text=rich_text_rv[1]
				else:
					ret=1
					error='变量替换异常,检查变量是否已定义'

			else:
				ret=1
				error='属性替换异常 可用属性'

			smtp_host=mail_config.smtp_host#"smtp.qq.com"
			smtp_port=mail_config.smtp_port#465
			subject=''
			description=mail_config.description
			description_rp=_replace_property(user, description)
			if description_rp[0] is 'success':
				description_rv=_replace_variable(user,description_rp[1],taskid=taskid)
				if description_rv[0] is 'success':
					subject=description_rv[1]
				else:
					ret=1
					error='变量替换异常,检查变量是否已定义'

			else:
				ret=1
				error='属性替换异常 可用属性'



			msg=MIMEText(cls.gethtmlcontent(taskid,rich_text),'html','utf-8')
			msg['From']=formataddr([sender_nick,sender_name])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
			msg['To']='%s'%','.join([cls._format_addr('<%s>'%to_addr) for to_addr in list(to_receive.split(','))])               # 括号里的对应收件人邮箱昵称、收件人邮箱账号
			#msg['Subject']=cls.subject          # 邮件的主题，也可以说是标题
			msg['Subject']=subject
			server=smtplib.SMTP_SSL(smtp_host, smtp_port)  # 发件人邮箱中的SMTP服务器，端口是25
			server.login(sender_name,sender_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
			server.sendmail(sender_name,list(to_receive.split(',')),msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
			server.quit()  # 关闭连接
		except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
			print(traceback.format_exc())
			ret=2
			error=traceback.format_exc()

		print("retret=",ret,error)
		
		
		return cls._getdescrpition(mail_config.to_receive,ret,error)
			
	@classmethod
	def _getdescrpition(cls,to_receive,send_result,error=None):
		res=None
		if send_result is 0:
			res='发送成功'
		elif send_result is 1:
			res='发送成功 但邮件内容可能有小问题[%s]'%error

		elif send_result is 2:
			res='发送失败[%s]'%error

		return '========================发送邮件 收件人:%s 结果：%s'%(to_receive,res)



class Transformer:

	_businessid_cache=dict()

	def __init__(self,callername,byte_list,content_type):

		print('【Transformer工具初始化】')
		self._set_content_type_flag(content_type)

		self._before_transform_check_flag=('success','')

		self._difference_config_file(byte_list)

		self.transform_id=EncryptUtils.md5_encrypt(str(datetime.datetime.now()))
		self.callername=callername


		# self.transform_id=EncryptUtils.md5_encrypt(str(datetime.datetime.now()))
		# self.callername=callername
		# self.act_data=self._get_workbook_sheet_cache(self.data_workbook,'执行数据')
		# self.var_data=self._get_workbook_sheet_cache(self.data_workbook,'变量定义')



	def _difference_config_file(self,byte_list):
		'''
		区分配置文件&用例文件
		'''
		print('【识别上传文件】')
		try:
			print('上传文件数量=>',len(byte_list))
			for byte in byte_list:
				cur_workbook=xlrd.open_workbook(file_contents=byte)
				try:
					global_sheet=cur_workbook.sheet_by_name('Global')
					self.config_workbook=cur_workbook
				except:
					self.data_workbook=getattr(self,'data_workbook',[])
					self.data_workbook.append(cur_workbook)

			##校验文件
			print('配置=>',getattr(self,'config_workbook',None))
			print('数据=>',getattr(self,'data_workbook',[]))
			if getattr(self,'config_workbook',None) is None:
				self._before_transform_check_flag=('fail','没上传配置文件')
				return

			if getattr(self,'data_workbook',[])==[]:
				self.data_workbook=[]
				self._before_transform_check_flag=('fail','没上传用例文件')
				return

		except:
			print(traceback.format_exc())
			self._before_transform_check_flag=('error','无法区分配置和用例文件')
			return

		self._before_transform_check_flag=('success','上传文件识别成功..')




	def _check_file_valid(self):
		"""
		检查文件是否合法
		"""
		return self._before_transform_check_flag


	def _set_content_type_flag(self,kind):
		#kind=('json','xml','urlencode','not json','not xml','not urlencode')
		if kind=='json':
			self.is_json=True
			self.is_xml=False
		elif kind=='xml':
			self.is_xml=True
			self.is_json=False
		elif kind=='urlencode':
			self.is_xml=False
			self.is_json=False
		elif kind=='not_json':
			self.is_json=False
		elif kind=='not_xml':
			self.is_xml=False
		elif kind=='not_urlencode':
			self.is_json=True
			self.is_xml=True

	def _get_itf_basic_conifg(self):
		'''
		获取config init基本配置
		'''
		init_cache=self._get_workbook_sheet_cache(self.config_workbook,'Init')
		for rowdata in init_cache:
			if rowdata['默认对象']=='Y' and rowdata['对象类型']=='interface':
				pv=rowdata['参数']
				if self.isxml:
					return {
					'host':pv.split(',')[0],
					'port':pv.split(',')[1],

					}
				else:
					return {
					'host':pv.split(',')[0]

					}


	def _get_itf_detail_config(self):
		'''	
		获取接口具体配置信息

		'''
		res={}
		
		script_cache=self._get_workbook_sheet_cache(self.config_workbook, 'Scripts')
		for rowdata in script_cache:
			rowdatalist=rowdata['脚本全称'].split(',')

			path=rowdatalist[0]
			method=rowdatalist[1]
			content_type='urlencode'

			if len(rowdatalist)>2:
				content_type=rowdatalist[2]


			res[rowdata['脚本简称']]={
			'path':path,
			'method':method,
			'content_type':content_type
			}

		return res

	def _get_workbook_sheet_cache(self,workbook,sheetname):
		"""
		获取sheet键值数据
		"""

		cache=[]

		sheet=workbook.sheet_by_name(sheetname)
		sheet_rows=sheet.nrows
		titles=sheet.row_values(0)
		title_order_map={}
		for index in range(len(titles)):
			title_order_map[str(index)]=str(titles[index])

		print('titles=>',title_order_map)
		

		for rowindex in range(1, sheet_rows):
			row_map={}
			row=sheet.row_values(rowindex)
			for cellindex in range(len(row)):
				k=title_order_map[str(cellindex)]
				v=row[cellindex]
				print('%s->%s'%(k,v))
				row_map[k]=v

			cache.append(row_map)


		# print(kv_map)
		return cache

	def _get_business_sheet_cache(self):
		'''
		获取业务数据缓存
		'''
		cache={}
		sheets=self.data_workbook.sheet_names()
		for sheetname in sheets and sheetname not in ('变量定义','执行数据'):
			cache[sheetname]=self._get_workbook_sheet_cache(self.data_workbook, sheetname)
		return cache


	def transform(self):

		print('【准备数据转化】')
		resultlist=[]
		for dwb in self.data_workbook:
			result=[]
			status,msg=self._check_file_valid()
			if status!='success':
				return (status,msg)
			else:
				print(msg)

			self.act_data=self._get_workbook_sheet_cache(dwb,'执行数据')
			self.var_data=self._get_workbook_sheet_cache(dwb,'变量定义')

			print('【开始转换】接收数据集[%s,%s]'%(dwb,self.config_workbook))

			resultlist=[]
			
			f1=self.add_var()

			f2=self.addbusinessdata()

			f3=self.addstepdata()

			f4=self.add_case()

			f5=self.add_plan()

			print('f1=>',f1)
			print('f2=>',f2)
			print('f3=>',f3)
			print('f4=>',f4)
			print('f5=>',f5)

			result.append(f1)
			result.append(f2)
			result.append(f3)
			result.append(f4)
			result.append(f5)
			resultlist.append(result)

		##分析结果
		for rs in resultlist:
			for r in rs:
				if r[0]!='success':
					return ('fail','转换失败')

		return('success','转换成功!')


	def addbusinessdata(self):
		'''
		插入业务数据
		'''
		try:
			print('【开始添加业务数据】')
			_meta=['测试点','DB检查数据','UI检查数据','接口检查数据','数据编号']
			_m={
			'测试点':'businessname',
			'DB检查数据':'db_check',
			'UI检查数据':'',
			'接口检查数据':'itf_check',
			'数据编号':''

			}
			for sheetname,cache in self._get_business_sheet_cache().items():
				rowindex=0
				for rowdata in cache:

					business=BusinessData()
					params={}
					for filedname,value in rowdata.items():
						if fieldname  in _m:
							if fieldname =='测试点':
								business.businessname=value
								continue
							elif fieldname=='DB检查数据':
								business.db_check=value
								continue
							elif fieldname=='接口检查数据':
								business.itf_check=value
								continue
						else:
							params[filedname]=value

					##没测试点列 业务名称取值
					if not  business.businessname:
						business.businessname='%s%s'%(sheetname,rowindex+1)

					if not self.is_json:
						params=params.get('json','{}')

					business.params=str(params)
					business.save()
					self._businessid_cache['%s:%s'%(sheetname,rowindex+1)]=business.id
					rowindex=rowindex+1

			return('success','')


		except:
			return ('error','插入业务数据异常=>%s'%traceback.format_exc())



	def _get_step_names(self):
		return [x for x in self.data_workbook.sheet_names() if x not in('变量定义','执行数据')]
		
	def addstepdata(self):
		'''
		添加step
		'''
		try:
			print('【开始添加步骤数据】')
			all_function=list(Function.objects.all())+getbuiltin()
			all_function_name=[x.name for x  in all_function]
			for rowdata in self.act_data:
				step=Step()
				step.author=User.objects.get(name=self.callername)

				func_field_value=rowdata['函数名称']
				if func_field_value  not in all_function_name:
					#接口
					basic_config=self._get_itf_basic_conifg()
					detail_config=self._get_itf_detail_config()
					step.step_type='interface'
					step.description=rowdata['参数值'].split(':')[0]
					step.content_type=detail_config.get('content_type','')
					step.method=detail_config.get('method', '')

					if self.is_xml:
						step.url='%s:%s'%(basic_config.get('host',''),basic_config.get('port',''))
					else:
						step.url="http://%s%s"%(basic_config.get('host',''),detail_config.get('path',''))

				else:
					#函数
					step.step_type='function'
					step.body=func_field_value
					step.description=rowdata['测试要点概要']
					step.related_id=Step.objects.get(name=step.body.strip()).id
				step.save()
		except:
			return ('error','添加步骤异常')

	def add_step_business_relation(self,step_id,business_id):
		'''
		步骤关联业务数据
		'''
		print('【步骤关联业务数据】')
		step=Step.objects.get(id=step_id)
		business=BusinessData.objects.get(id=business_id)
		step.businessdatainfo.add(business)

	def add_plan(self):
		try:
			print('【添加计划】')
			plan=Plan()
			plan.description='计划_%s_%s'%(self.callername,self.transform_id)
			plan.author=User.objects.get(name=self.callername)
			plan.save()
			return ('success','')

		except:
			return ('error','添加计划异常=>%s'%traceback.format_exc())

	def add_case(self):
		try:
			print('【添加用例】')
			case=Case()
			case.description='用例_%s_%s'%(self.callernames,self.transform_id)
			case.author=User.objects.get(naem=self.callername)
			case.save()

			return ('success','')

		except:
			return ('error','添加用例异常=>%s'%traceback.format_exc())

	def add_plan_case_relation(self,plan_id,case_id):
		print('【关联计划和用例】')
		plan=Plan.objects.get(id=plan_id)
		case=Case.objects.get(id=case_id)
		plan.cases.add(case)

		order=Order()
		order.kind='case'
		order.main_id=plan_id
		order.follow_id=case_id
		order.save()

	def add_case_businss_relation(self,case_id,business_id):
		print('【关联用例和业务数据】')
		case=Case.objects.get(id=case_id)
		business=BusinessData.objects.get(id=business_id)
		case.businessdatainfo.add(business)

		order=Order()
		order.kind='step'
		order.main_id=case_id
		order.follow_id=business_id
		order.save()

	def add_var(self):
		try:
			for dwb in self.data_workbook:
				print('【开始添加变量】')
				var_cache=self._get_workbook_sheet_cache(dwb, '变量定义')
				for var in var_cache:
					description=var['变量说明']
					gain=var['获取方式']
					key=var['变量名称']
					value=var['值']
					# is_cache=False
					var=Variable()
					var.description=description
					var.key=key
					var.gain=gain
					if not gain:
						var.value=value
					var.save()
			return ('success','')
		except:
			return ('error','添加变量异常=>%s'%traceback.format_exc())



	def _rollback(self):
		"""
		转换失败回滚操作
		"""
		pass
