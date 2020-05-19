#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-10-12 09:42:34
# @Author  : Blackstone
# @to      :用例管理
import json
import threading

from manager.operate.cron import Cron
from .models import Tag
import traceback, datetime
from django.db.models import Q
from manager import models as mm
from django.db import connection
from ME2.settings import logme

from login import models as lm
from .context import *
from .invoker import runplan, runplans,get_run_node_plan_id
from .core import gettaskid,get_params
from manager.context import Me2Log as logger
from .operate.dataMove import DataMove
from tools.R import R


# addproduct
@monitor(action='添加产品')
def addproduct(request):
	product = None
	try:
		description = request.POST.get('description')
		author = lm.User.objects.get(name=request.session.get('username'))
		product = mm.Product(description=description, author=author)
		product.save()
		return {
			'status': 'success',
			'msg': '新增[%s]成功' % description,
			'data': {
				'id': 'product_%s' % product.id,
				'pId': -1,
				'name': description,
				'type': 'product',
				'textIcon': 'fa icon-fa-home',
			}
		}
	except:
		logger.info(traceback.format_exc())
		return {
			'status': 'error',
			'msg': '新增[%s]异常' % product.description
		}

@monitor(action='删除产品')
def delproduct(request):
	p = None
	try:
		id_ = request.POST.get('ids')
		msg = ''
		ids = id_.split(',')
		for i in ids:
			i = i.split('_')[1]
			p = mm.Product.objects.get(id=int(i))
			if len(getchild('product_plan', i)) > 0:
				return {
					'status': 'fail',
					'msg': '删除失败,[%s]含子数据' % p.description
				}
			p.delete()
			
			return {
				'status': 'success',
				'msg': '删除[%s]成功' % p.description
			}
	
	except:
		return {
			'status': 'error',
			'msg': '删除[%s]异常' % p.description
		}

@monitor(action='编辑产品')
def editproduct(request):
	uid = request.POST.get('uid')
	description = request.POST.get('description')
	try:
		p = mm.Product.objects.get(id=int(uid.split('_')[1]))
		p.description = description
		p.save()
		return {
			'status': 'success',
			'msg': '编辑成功',
			'data': {
				'name': description
			}
		}
	
	except:
		logger.error(traceback.format_exc())
		return {
			'status': 'error',
			'msg': '编辑[%s]异常' % description
		}


# plan
@monitor(action='新建计划')
def addplan(request):
	msg = ''
	try:
		pid = request.POST.get('pid').split('_')[1]
		description = request.POST.get('description')
		db_id = request.POST.get('dbid')
		schemename = request.POST.get('scheme')
		author = lm.User.objects.get(name=request.session.get('username', None))
		run_type = request.POST.get('run_type')
		before_plan = request.POST.get('before_plan')
		is_send_mail = 'open' if request.POST.get('is_send_mail') == 'true' else 'close'
		is_send_dingding = 'open' if request.POST.get('is_send_dingding') == 'true' else 'close'
		mail_config = mm.MailConfig(is_send_mail=is_send_mail, is_send_dingding=is_send_dingding)
		mail_config.save()
		
		plan = mm.Plan(description=description, db_id=db_id, schemename=schemename, author=author,
		               run_type=run_type, mail_config_id=mail_config.id,before_plan=before_plan)
		plan.save()
		addrelation('product_plan', author, pid, plan.id)
		extmsg=''
		if run_type == '定时运行':
			config = request.POST.get('config')
			crontab = mm.Crontab()
			crontab.value = config
			crontab.author = plan.author
			crontab.plan = plan
			crontab.status = 'close'
			crontab.save()
			extmsg = '<br>下次运行时间：%s'%str(Cron.addcrontab(plan.id)).split('+')[0]

		return {
			'status': 'success',
			'msg': '新增[%s]成功%s' % (description,extmsg),
			'data': {
				'id': 'plan_%s' % plan.id,
				'pId': 'product_%s' % pid,
				'name': description,
				'type': 'plan',
				'textIcon': 'fa icon-fa-product-hunt',
			}}
	except:
		return {
			
			'status': 'error',
			'msg': '新增失败[%s]' % traceback.format_exc()
		}


@monitor(action='删除计划')
def delplan(request):
	id_ = request.POST.get('ids')
	msg = ''
	ids = id_.split(',')
	try:
		for i in ids:
			i = i.split('_')[1]
			i = int(i)
			plan = mm.Plan.objects.get(id=i)
			if len(list(getchild('plan_case', i))) > 0:
				return {
					'status': 'fail',
					'msg': '删除失败,[%s]含子数据' % plan.description
				}
			Cron.delcrontab(i)
			# plan.delete()
			##消除上层依赖
			_regen_weight(request.session.get('username'), plan, trigger='del')
		# delrelation('product_plan',None, None,i)
		
		return {
			'status': "success",
			'msg': '删除成功'
		}
	
	except:
		return {
			'status': 'error',
			'msg': "删除失败[%s]" % traceback.format_exc()
		}


def handlebindplans(olddescription, newdescription, id_):
	logger.info("处理计划名修改后的标签中绑定的计划名称")
	oldtags = Tag.objects.values('id', 'planids').filter(Q(planids__contains=olddescription))
	for oldtag in oldtags:
		planids = json.loads(oldtag['planids'])
		if olddescription in planids and id_ in planids[olddescription]:
			edittag = Tag.objects.get(id=oldtag['id'])
			ol = json.loads(edittag.planids)
			ol[newdescription] = ol.pop(olddescription)
			edittag.planids = str(ol).replace("'", '"')
			edittag.save()
			logger.info(str(edittag.id) + '更新完成')


@monitor(action='编辑计划')
def editplan(request):
	id_ = request.POST.get('uid').split('_')[1]
	config = request.POST.get('config')
	run_type = request.POST.get("run_type")
	newdescription = request.POST.get('description')
	msg = ''
	try:
		is_send_mail = request.POST.get("is_send_mail")
		is_send_dingding = request.POST.get("is_send_dingding")
		plan = mm.Plan.objects.get(id=id_)
		olddescription = plan.description
		plan.description = newdescription
		plan.db_id = request.POST.get('dbid')
		plan.before_plan = request.POST.get('before_plan')
		plan.schemename = request.POST.get('scheme')
		logger.info('description=>', plan.description)
		plan.run_type = request.POST.get('run_type')
		plan.save()
		extmsg=''
		if run_type == '定时运行':
			try:
				cron = mm.Crontab.objects.get(plan_id=id_)
				cron.value = config
				cron.save()
			except:
				crontab = mm.Crontab()
				crontab.value = config
				crontab.author = plan.author
				crontab.plan = plan
				crontab.status = 'close'
				crontab.save()
			extmsg = '<br>下次运行时间：%s'%str(Cron.addcrontab(plan.id)).split('+')[0]
		else:
			Cron.delcrontab(plan.id)

		if plan.mail_config_id == '' or plan.mail_config_id is None:  # 针对老任务，没有邮箱配置
			mail_config = mm.MailConfig()
			if is_send_mail == 'true':
				mail_config.is_send_mail = 'open'
			else:
				mail_config.is_send_mail = 'close'
			if is_send_dingding == 'true':
				mail_config.is_send_dingding = 'open'
			else:
				mail_config.is_send_dingding = 'close'
			mail_config.save()
			plan.mail_config_id = mail_config.id
			plan.save()
		else:
			mail_config = mm.MailConfig.objects.get(id=plan.mail_config_id)
			if is_send_mail == 'true':
				mail_config.is_send_mail = 'open'
			else:
				mail_config.is_send_mail = 'close'
			if is_send_dingding == 'true':
				mail_config.is_send_dingding = 'open'
			else:
				mail_config.is_send_dingding = 'close'
			mail_config.save()
		msg = '编辑成功'
		
		if olddescription != newdescription:
			threading.Thread(target=handlebindplans, args=(olddescription, newdescription, id_)).start()
		
		return {
			'status': 'success',
			'msg': '编辑[%s]成功%s' % (plan.description,extmsg),
			'data': {
				'name': plan.description
			}
		}
	except:
		return {
			'status': 'error',
			'msg': "编辑异常[%s]" % traceback.format_exc()
		}


@monitor(action='运行用例')
def run(request):
	callername = request.session.get('username')
	runids = [x for x in request.POST.get('ids').split(',')]
	logger.info('runids:',runids)
	is_verify = request.POST.get('is_verify')
	for runid in runids:
		planid=get_run_node_plan_id(runid)
		logger.info('获取待运行节点计划ID:',planid)
		plan = mm.Plan.objects.get(id=planid)
		taskid = gettaskid(plan.__str__())
		logger.info('callername:',callername)
		state_running =getRunningInfo(username=callername,planid=planid,type='isrunning')
		logger.info('flag4')
		
		if state_running != '0':
			msg = '验证' if state_running == 'verify' else '调试'
			return {
				'status': 'fail',
				'msg': '计划正在运行[%s]任务，稍后再试！'%msg
			}
		# logger.info('runidd:',runid)
		t=threading.Thread(target=runplan,args=(callername, taskid, planid, is_verify,None,runid))
		t.start()
	return {
		'status': 'success',
		'msg': str(taskid),
		'data':planid
	}

@monitor(action='导出计划')
def export(request):
	flag = str(datetime.datetime.now()).split('.')[0]
	version = request.GET.get('version')
	logger.info('version=>', version)
	planid = request.GET.get('planid')
	m = DataMove()
	res = m.export_plan(planid, flag, version=int(version))
	return {
		'status': res[0],
		'msg': res[1]
	}


def importplan(request):
	pass


##
@monitor(action='新建用例')
def addcase(request):
	msg = ''
	try:
		pid = request.POST.get('pid').split('_')[1]
		case = mm.Case()
		case.author = lm.User.objects.get(name=request.session.get('username', None))
		case.description = request.POST.get('description')
		case.db_id = request.POST.get('dbid')
		case.save()
		
		addrelation('plan_case', request.session.get('username'), pid, case.id)
		return {
			'status': 'success',
			'msg': '新增成功',
			'data': {
				'id': 'case_%s' % case.id,
				'pid': 'plan_%s' % pid,
				'name': case.description,
				'type': 'case',
				'textIcon': 'fa icon-fa-folder'
			}
			
		}
	except:
		return {
			'status': 'error',
			'msg': '新增失败[%s]' % traceback.format_exc()
		}


@monitor(action='编辑用例')
def editcase(request):
	id_ = request.POST.get('uid').split('_')[1]
	msg = ''
	try:
		case = mm.Case.objects.get(id=id_)
		case.description = request.POST.get('description')
		case.db_id = request.POST.get('dbid')
		case.count = int(request.POST.get('count'))
		case.save()
		casename = case.description
		if case.count == 0:
			casename = '<s>%s</s>' % casename
		
		return {
			'status': 'success',
			'msg': '编辑成功',
			'data': {
				'name': casename
			}
		}
	except:
		return {'status': 'error', 'msg': '编辑失败[%s]' % traceback.format_exc()}

@monitor(action='删除用例')
def delcase(request):
	id_ = request.POST.get('ids')
	ids = id_.split(',')
	try:
		for i in ids:
			i = i.split('_')[1]
			i = int(i)
			case = mm.Case.objects.get(id=i)
			if len(getchild('case_step', i)) or len(getchild('case_case', i)) > 0:
				return {
					'status': 'fail',
					'msg': '删除失败,[%s]含子数据' % case.description
				}
			
			# delrelation('plan_case',None, None,i)
			# case.delete()
			_regen_weight(request.session.get('username'), case, trigger='del')
		return {
			'status': 'success',
			'msg': '删除成功'
		}
	except:
		return {
			'status': 'error',
			'msg': "删除失败[%s]" % traceback.format_exc()
		}


##
@monitor(action='新加步骤')
def addstep(request):
	from .core import getbuiltin
	try:
		pid = request.POST.get('pid').split('_')[1]
		step_type = request.POST.get('step_type')
		description = request.POST.get('description')
		headers = request.POST.get('headers')
		body = request.POST.get("body")
		url = request.POST.get('url')
		if url:
			url = url.strip()
		method = request.POST.get('method')
		content_type = request.POST.get('content_type')
		count = request.POST.get('count')
		tmp = request.POST.get('tmp')
		author = request.session.get('username')
		logger.info("author=>", author)
		businessdata = request.POST.get('business_data')
		logger.info('businessdata=>', type(businessdata), businessdata)
		dbid = request.POST.get('dbid')

		##
		if step_type == 'dir':
			case = mm.Case()
			case.description = description
			
			case.author = lm.User.objects.get(name=author)
			
			case.db_id = dbid
			case.save()
			
			addrelation('case_case', author, pid, case.id)
			return {
				'status': 'success',
				'msg': '新建[%s]成功' % case.description,
				
				'data': {
					'id': 'case_%s' % case.id,
					'pid': 'case_%s' % pid,
					'name': case.description,
					'type': 'case',
					'textIcon': 'fa icon-fa-folder',
					
				}
			}
		
		step = mm.Step()
		step.step_type = step_type
		step.description = description
		step.headers = headers
		step.body = body
		step.url = url
		step.method = method
		step.content_type = content_type
		step.temp = tmp
		step.count=count
		step.author = lm.User.objects.get(name=author)
		
		step.db_id = dbid
		# step.encrypt_type=encrypt_type
		step.save()

		# mounttestdata(author,step.id)
		
		# if 'function'==step.step_type:
		# 	# step.body=body
		# 	funcname=step.body.strip()
		# 	builtinmethods=[x.name for x in getbuiltin() ]
		# 	builtin=(funcname in builtinmethods)
		
		# 	if builtin is False:
		# 		# flag=Fu.tzm_compute(step.body,'(.*?)\((.*?)\)')
		# 		businessdatainst=None
		# 		businessinfo=getchild('step_business',step.id)
		# 		logger.info('vvvv=>',businessinfo,step.id)
		# 		if len(businessinfo)>0:
		# 			businessdatainst=businessinfo[0]
		
		# 		status,res=gettestdataparams(businessdatainst.id)
		# 		logger.info('gettestdataparams=>%s'%res)
		# 		if status is not 'success':
		# 			return (status,res)
		
		# 		params=','.join(res)
		
		# 		call_str='%s(%s)'%(funcname,params)
		# 		flag=Fu.tzm_compute(call_str,'(.*?)\((.*?)\)')
		# 		funcs=list(Function.objects.filter(flag=flag))
		# 		if len(funcs)>1:
		# 			return ('fail','找到多个匹配的自定义函数 请检查')
		# 		related_id=funcs[0].id
		# 		step.related_id=related_id
		
		addrelation('case_step', author, pid, step.id)
		
		return {
			'status': 'success',
			'msg': '新增测试步骤',
			'data': {
				'id': 'step_%s' % step.id,
				'pid': 'case_%s' % pid,
				'name': step.description,
				'type': 'step',
				'textIcon': 'fa icon-fa-file-o',
				
			}
		}
	except Exception as e:
		return {
			'status': 'error',
			'msg': "添加失败[%s]" % traceback.format_exc()
		}

@monitor(action='编辑步骤')
def editstep(request):
	id_ = request.POST.get('uid').split('_')[1]
	try:
		count = request.POST.get('count')
		dbid = request.POST.get('dbid')

		step_type = request.POST.get('step_type')
		description = request.POST.get('description')
		headers = request.POST.get('headers')
		body = request.POST.get("body")
		url = request.POST.get('url')
		method = request.POST.get('method')
		content_type = request.POST.get('content_type')
		
		tmp = request.POST.get('tmp')
		username = request.session.get('username')
		author = lm.User.objects.get(name=username)
		
		step = mm.Step.objects.get(id=id_)
		if step.step_type != step_type:
			return {
				'status': 'fail',
				'msg': '编辑失败[不允许修改类型]'
			}
		
		# if step_type is None:
		# 	step.step_type='function'
		
		step.count = int(count)
		step.description = description
		step.headers = headers
		step.body = body
		step.url = url
		step.method = method
		step.content_type = content_type
		
		step.temp = tmp
		step.db_id = dbid

	
		step.save()

		stepname = description
		
		logger.info('step save,count=>', count)
		if step.count == 0:
			stepname = '<s>%s</s>' % stepname
		
		# mounttestdata(username, step.id,trigger='edit')
		
		logger.info('step save,name=>', stepname)
		return {
			'status': 'success',
			'msg': '编辑成功',
			'data': {'name': stepname}
		}
	
	except Exception as e:
		# logger.info(traceback.format_exc())
		return {
			'status': 'error',
			'msg': '编辑失败[%s]' % traceback.format_exc()
		}

@monitor(action='删除步骤')
def delstep(request):
	id_ = request.POST.get('ids')
	ids = id_.split(',')
	try:
		for i in ids:
			i = i.split('_')[1]
			i = int(i)
			step = mm.Step.objects.get(id=i)
			businessdatainfo = getchild('step_business', i)
			if len(businessdatainfo) > 0:
				return {
					'status': 'fail',
					'msg': '删除失败,[%s]含子数据' % step.description
				}
			# delrelation('case_step',None, None,i)
			# step.delete()
			_regen_weight(request.session.get('username'), step, trigger='del')
		return {
			'status': 'success',
			'msg': '删除成功'
		}
	
	except Exception as e:
		return {
			'status': 'success',
			'msg': "删除失败[%s]" % traceback.format_exc()
		}


def _check_params(param_value):
	if param_value.startswith('{') and param_value.endswith('}'):
		logger.info('f1')
		try:
			
			eval(param_value)
			return True
		except:
			return False
	else:
		logger.info('f2')
		return True


##
@monitor(action='新建测试点')
def addbusiness(request):
	from .core import getbuiltin, Fu
	bname = ''
	try:
		
		pid = request.POST.get('pid').split('_')[1]
		b = mm.BusinessData()
		b.businessname = request.POST.get('businessname')
		bname = b.businessname
		b.itf_check = request.POST.get('itf_check')
		b.db_check = request.POST.get('db_check')
		b.params = request.POST.get('params')
		b.parser_check = request.POST.get('parser_check')
		b.parser_id = request.POST.get('parser_id')
		b.description=request.POST.get('description')
		b.timeout=request.POST.get('timeout')
		
		# check_result=_check_params(b.params)
		# logger.info('nn=>',check_result)
		# if not check_result:
		# 	return{
		# 	'status':'error',
		# 	'msg':'参数json格式异常，请检查！'
		# 	}
		
		b.postposition = request.POST.get('postposition')
		b.preposition = request.POST.get('preposition')
		b.count = int(request.POST.get('count').strip()) if request.POST.get('count') != '' else int(1)
		if b.count == 0:
			bname = '<s>%s</s>' % bname
		
		b.save()
		addrelation('step_business', request.session.get('username'), pid, b.id)
		
		##funcion类型关联realted_id
		
		status, step = mm.BusinessData.gettestdatastep(b.id)
		if status is not 'success':
			return {
				'status': 'fail',
				'msg': '添加测试数据异常[%s]' % step
			}
		
		if 'function' == step.step_type:
			# step.body=body
			funcname = step.body.strip()
			builtinmethods = [x.name for x in getbuiltin()]
			builtin = (funcname in builtinmethods)
			
			if builtin is False:
				# flag=Fu.tzm_compute(step.body,'(.*?)\((.*?)\)')
				businessdatainst = None
				businessinfo = getchild('step_business', step.id)
				logger.info('vvvv=>', businessinfo, step.id)
				if len(businessinfo) > 0:
					businessdatainst = businessinfo[0]
				
				status, res = mm.BusinessData.gettestdataparams(businessdatainst.id)
				logger.info('gettestdataparams=>%s' % res)
				if status is not 'success':
					return {
						'status': status,
						'msg': str(res)
					}
				
				params = ','.join(res)
				
				call_str = '%s(%s)' % (funcname, params)
				flag = Fu.tzm_compute(call_str, '(.*?)\((.*?)\)')
				funcs = list(mm.Function.objects.filter(flag=flag))
				if len(funcs) > 1:
					return {
						'status': 'fail',
						'msg': '查找到多个函数请检查'
					}
				related_id = funcs[0].id
				
				logger.info('修改step related_id=>', related_id)
				step.related_id = related_id
				step.save()
		
		return {
			'status': 'success',
			'msg': '添加[%s]成功' % b.businessname,
			'data': {
				'id': 'business_%s' % b.id,
				'pId': 'step_%s' % pid,
				'name': bname,
				'type': 'business',
				'textIcon': 'fa icon-fa-leaf',
			}
		}
	except:
		return {
			'status': 'error',
			'msg': '添加测试数据异常[%s]' % traceback.format_exc()
		}


@monitor(action='编辑测试点')
def editbusiness(request):
	from .core import getbuiltin, Fu
	bname = ''
	try:
		
		b = mm.BusinessData.objects.get(id=request.POST.get('uid').split('_')[1])
		b.businessname = request.POST.get('businessname')
		bname = b.businessname
		b.itf_check = request.POST.get('itf_check')
		b.db_check = request.POST.get('db_check')
		b.params = request.POST.get('params')
		b.postposition = request.POST.get('postposition')
		b.preposition = request.POST.get('preposition')
		b.count = int(request.POST.get('count').strip()) if request.POST.get('count') != '' else int(1)
		b.parser_check = request.POST.get('file_check')
		b.parser_id = request.POST.get('parser_id')
		b.description=request.POST.get('description')
		b.timeout=request.POST.get('timeout')
		# check params
		check_result = _check_params(b.params)
		
		# if not check_result:
		# 	return{
		# 	'status':'error',
		# 	'msg':'参数json格式异常，请检查！'
		# 	}
		
		if b.count == 0:
			bname = '<s>%s</s>' % bname
		
		b.save()
		
		status, step = mm.BusinessData.gettestdatastep(b.id)
		if status is not 'success':
			return {
				'status': 'fail',
				'msg': '编辑业务数据异常[%s]' % step
			}
		
		##重新计算related_id
		if 'function' == step.step_type:
			# funcname=re.findall("(.*?)\(.*?\)", step.body)[0]
			funcname = step.body.strip()
			builtinmethods = [x.name for x in getbuiltin()]
			builtin = (funcname in builtinmethods)
			
			if builtin is False:
				businessdatainst = None
				# businessinfo=list(step.businessdatainfo.all())
				businessinfo = getchild('step_business', step.id)
				if len(businessinfo) > 0:
					businessdatainst = businessinfo[0]
				
				status, res = mm.BusinessData.gettestdataparams(businessdatainst.id)
				if status is not 'success':
					return (status, res)
				
				params = ','.join(res)
				calll_str = '%s(%s)' % (step.body.strip(), params)
				flag = Fu.tzm_compute(calll_str, '(.*?)\((.*?)\)')
				funcs = list(mm.Function.objects.filter(flag=flag))
				if len(funcs) > 1:
					return ('fail', '找到多个匹配的自定义函数 请检查')
				related_id = funcs[0].id
				step.related_id = related_id
		
		return {
			'status': 'success',
			'msg': '编辑成功',
			'data': {
				'name': bname
			}}
	except:
		return {
			'status': 'error',
			'msg': '编辑业务数据异常[%s]' % traceback.format_exc()
		}


@monitor(action='删除测试点')
def delbusiness(request):
	try:
		
		id_ = request.POST.get('ids')
		ids = id_.split(',')
		for i in ids:
			i = int(i.split('_')[1])
			
			business = mm.BusinessData.objects.get(id=i)
			# business.delete()
			_regen_weight(request.session.get('username'), business, trigger='del')
		return {
			'status': 'success',
			'msg': '删除成功'
		}
	
	except:
		return {
			'status': 'error',
			'msg': '删除业务异常[%s]' % traceback.format_exc()
		}


@monitor(action='移动|复制节点')
def movenode(request):
	try:
		is_copy = request.POST.get('is_copy')
		movetype = request.POST.get('move_type')
		srcid = request.POST.get('src_id')
		if srcid.split('_')[0] in ['product','root']:
			return {
				'status': 'error',
				'msg': '操作失败，不允许移动'
			}
		targetid = request.POST.get('target_id')
		user = lm.User.objects.get(name=request.session.get('username'))
		# elementclass=srcid.split('_')[0]
		# elementid=srcid.split('_')[1]
		# if elementclass=='business':
		# 	elementclass='businessData'
		# elementclass=_first_word_up(elementclass)
		# element=eval("%s.objects.get(id=%s)"%(elementclass,elementid))
		_build_all(srcid, targetid, movetype, user, is_copy, user.name)
		
		return {
			'status': 'success',
			'msg': '操作成功'}
	except:
		logger.info(traceback.format_exc())
		return {
			'status': 'error',
			'msg': '移动异常'
		}

def movemulitnodes(request):
	try:
		is_copy = request.POST.get('is_copy')
		movetype = request.POST.get('move_type')
		src_ids = request.POST.get('src_ids')[:-1]
		src_ids = src_ids.split(';')
		targetid = request.POST.get('target_id')
		user = lm.User.objects.get(name=request.session.get('username'))
		logger.info('开始批量移动/复制')
		for srcid in src_ids:
			logger.info('移动/复制节点：{}，目标节点{},复制{},移动类型{}'.format(srcid,targetid,is_copy,movetype))
			_build_all(srcid, targetid, movetype, user, is_copy, user.name)
		
		return {
			'status': 'success',
			'msg': '操作成功'}
	except:
		logger.info(traceback.format_exc())
		return {
			'status': 'error',
			'msg': '移动异常'
		}



################

####################


_order_value_cache = dict()


def addrelation(kind, callername, main_id, follow_id):
	order = mm.Order()
	order.kind = kind
	order.main_id = main_id
	order.follow_id = follow_id
	order.value = getnextvalue(kind, main_id)
	order.author = lm.User.objects.get(name=callername)
	
	order.save()


def delrelation(kind, callername, main_id, follow_id):
	# logger.info('==删除关联关系')
	# logger.info('kind=>',kind)
	# logger.info('main_id=>',main_id)
	# logger.info('follow_id=>',follow_id)
	try:
		ol = mm.Order.objects.get(kind=kind, main_id=main_id, follow_id=follow_id)
		logger.info('==删除节点关联[%s]' % ol)
		ol.delete()
	# length=len(ol)
	# logger.info('找到[%s]条待删除'%length)
	# for o in ol:
	# 	o.delete()
	
	# if kind=='plan_case' and length==0:
	# 	Order.objects.get(kind='case_case',follow_id=follow_id).delete()
	
	except:
		logger.info('==删除节点关联报错')
		logger.info(traceback.format_exc())


# logger.info('删除完毕')
def getchild(kind, main_id):
	'''
	返回有序子项
	'''
	child = []
	orderlist = ordered(list(mm.Order.objects.filter(kind=kind, main_id=main_id)))
	if kind == 'product_plan':
		for order in orderlist:
			logger.info('planid=>', order.follow_id)
			try:
				logger.info('plan class=>', mm.Plan)
				p = mm.Plan.objects.get(id=order.follow_id)
				# logger.info('添加计划=>',plan)
				child.append(p)
			# pirnt('child=>',child)
			except:
				logme.warn('找不到计划 ID=%s'%order.follow_id)
				#logger.info(traceback.format_exc())
	elif kind == 'plan_case':
		for order in orderlist:
			logger.info('case class=>', mm.Case)
			child.append(mm.Case.objects.get(id=order.follow_id))
	elif kind == 'case_step':
		for order in orderlist:
			logger.info('main=>%s follow=>%s v=%s' % (order.main_id, order.follow_id, order.value))
			
			child.append(mm.Step.objects.get(id=order.follow_id))
	elif kind == 'step_business':
		for order in orderlist:
			child.append(mm.BusinessData.objects.get(id=order.follow_id))
	elif kind == 'case_case':
		for order in orderlist:
			child.append(mm.Case.objects.get(id=order.follow_id))
	
	else:
		orderlist = list(mm.Order.objects.filter(Q(main_id=main_id) & Q(kind__contains=kind)))
		for order in orderlist:
			kind = order.kind
			ctype = kind.split('_')[1]
			# logger.info('old ctype=>',ctype)
			if ctype in ('business', 'businessdata'):
				ctype = "BusinessData"
			else:
				ctype = ctype[0].upper() + ctype[1:]
			
			# logger.info('last ctype=>',ctype)
			
			child.append(eval('mm.%s.objects.get(id=%s)' % (ctype, order.follow_id)))
	
	# logger.info('ck=>',child)
	return child


def ordered(iterator, key='value', time_asc=True):
	"""
	执行列表根据value从小到大排序
	"""
	try:
		for i in range(len(iterator) - 1):
			for j in range(i + 1, len(iterator)):
				groupa = int(str(getattr(iterator[i], key)).split(".")[0])
				groupb = int(str(getattr(iterator[j], key)).split(".")[0])
				if groupa > groupb:
					tmp = iterator[i]
					iterator[i] = iterator[j]
					iterator[j] = tmp
				
				elif groupa == groupb:
					indexa = int(getattr(iterator[i], key).split(".")[1])
					indexb = int(getattr(iterator[j], key).split(".")[1])
					if indexa > indexb:
						tmp = iterator[i]
						iterator[i] = iterator[j]
						iterator[j] = tmp
					
					elif indexb == indexa:
						timea = getattr(iterator[i], 'updatetime')
						timeb = getattr(iterator[j], 'updatetime')
						
						if time_asc == True:
							if timea > timeb:
								iterator[i], iterator[j] = iterator[j], iterator[i]
						
						elif time_asc == False:
							if timea < timeb:
								iterator[i], iterator[j] = iterator[j], iterator[i]
	
	except:
		logger.info(traceback.format_exc())
	finally:
		return iterator


def _regen_weight_force(parent_type, parent_id, ignore_id=None):
	'''
	重排父级权重
	'''
	logger.info('==强制删除后兄弟节点权重调整')
	try:
		kind = ''
		ol = ordered(list(mm.Order.objects.filter(Q(kind__contains='%s_' % parent_type) & Q(main_id=parent_id))))
		mx = len(ol)
		cur = 0
		for idx in range(1, mx + 1):
			
			if str(ol[idx - 1].follow_id) == str(ignore_id):
				pass
			else:
				cur = cur + 1
				
				ol[idx - 1].value = '1.%s' % cur
				ol[idx - 1].save()
	except:
		logger.info('强制删除后兄弟节点权重调整异常=>', traceback.format_exc())


def _regen_weight(callername, element, trigger='prev', target_id=None):
	'''
	删除移动复制节点重新生成权重 事件节点的order除外 保持分组(flag)
	'''
	##删除事件节点引用
	if trigger == 'del':
		c = element.__class__.__name__.lower()
		if c == 'businessdata':
			c = 'business'
		order = mm.Order.objects.get(Q(kind__contains='_%s' % c) & Q(follow_id=element.id))
		parentid = order.main_id
		group = order.value.split('.')[0]
		parentkind = order.kind.split('_')[0]
		text = '%s_' % parentkind
		
		delrelation(order.kind, callername, parentid, element.id)
		
		logger.info('==删除节点[%s]' % element)
		element.delete()
		logger.info('==删除后重新生成权重')
		orderlist = ordered(list(mm.Order.objects.filter(Q(kind__contains=text) & Q(main_id=parentid))))
		
		index = 0
		for order in orderlist:
			old = order
			index = index + 1
			curgroup = order.kind.split('.')[0]
			if curgroup != group:
				continue
			
			weight = '%s.%s' % (group, index)
			order.value = weight
			order.save()
			logger.info('[%s]=>[%s]' % (old, order))
		
		logger.info('生成后=>', orderlist)
	
	else:
		c = element.__class__.__name__.lower()
		if c == 'businessdata':
			c = 'business'
		order = mm.Order.objects.get(Q(kind__contains='_%s' % c) & Q(follow_id=element.id))
		parentid = order.main_id
		group = order.value.split('.')[0]
		parentkind = order.kind.split('_')[0]
		text = '%s_' % parentkind
		# logger.info('text=%s main_id=%s'%(text,parentid))
		orderlist = ordered(list(mm.Order.objects.filter(Q(kind__contains=text) & Q(main_id=parentid))))
		
		if trigger == 'prev':
			orderlist = ordered(orderlist, time_asc=False)
		elif trigger == 'next':
			orderlist = ordered(orderlist, time_asc=True)
		elif trigger == 'inner':
			# 最后一个不用在处理
			pass
		
		logger.info('===[%s]操作 根据时间处理再排序=>%s' % (trigger, orderlist))
		
		##重新生成序号 只处理同组号的数据
		logger.info('==兄弟节点重新生成权重')
		
		index = 0
		for order in orderlist:
			old = order
			index = index + 1
			curgroup = order.value.split('.')[0]
			
			logger.info('==拖动组号=>%s 兄弟节点组号=>%s 相等=>%s' % (group, curgroup, group == curgroup))
			if curgroup != group:
				continue
			
			weight = '%s.%s' % (group, index)
			order.value = weight
			order.save()
			logger.info('[%s]=>[%s]' % (old, order))
		
		logger.info('生成后=>', orderlist)


def _resort_by_create_when_equal(orderlist, asc=True):
	for i in range(len(orderlist) - 1):
		for j in range(i + 1, len(orderlist)):
			if orderlist[j] == orderlist[i]:
				if asc:
					if getattr(orderlist[i], 'updatetime') > getattr(orderlist[j], 'updatetime'):
						orderlist[i], orderlist[j] = orderlist[j], orderlist[i]
				
				else:
					if getattr(orderlist[i], 'updatetime') < getattr(orderlist[j], 'updatetime'):
						orderlist[i], orderlist[j] = orderlist[j], orderlist[i]
	
	return orderlist


def getnextvalue(kind, main_id, flag=0):
	max_value = 0
	orderlist = []
	if kind in ('case_case', 'case_step'):
		orderlist = list(mm.Order.objects.filter(kind='case_case', main_id=main_id)) + list(
			mm.Order.objects.filter(kind='case_step', main_id=main_id))
	else:
		orderlist = list(mm.Order.objects.filter(kind=kind, main_id=main_id))
	# logger.info('list=>',orderlist)
	
	if len(orderlist) == 0:
		return '1.1'
	else:
		lastvalue = ordered(orderlist)[-1].value
		group = lastvalue.split('.')[0]
		index = lastvalue.split('.')[1]
		newvalue = '%s.%s' % (group, int(index) + 1)
		return newvalue


def _get_delete_node(src_uid, src_type, iscopy, del_nodes):
	# logger.info('iscopy=>',iscopy)
	if iscopy == 'true':
		logger.info('==复制操作 略过添加待删除源数据')
	else:
		logger.info('==计算待删除源数据==')
		del_nodes.append((src_type, str(src_uid)))
		parent_type, parent_id = _get_node_parent_info(src_type, src_uid)
		
		# kind='%s_%s'%(parent_type,src_type)
		
		# logger.info('k1=>',kind)
		childs = getchild('%s_' % src_type, src_uid)  ##??
		# logger.info('childs=>',childs)
		for child in childs:
			child_type = child.__class__.__name__.lower()
			_get_delete_node(child.id, child_type, False, del_nodes)


def _sort_by_weight(childs):
	result = list()
	_m = {}
	_len = len(childs)
	
	if _len == 1:
		return childs
	
	elif _len > 1:
		for c in childs:
			node_type = c.__class__.__name__.lower()
			if node_type == 'businessdata':
				node_type = 'business'
			
			descp = ''
			try:
				desp = c.description
			except:
				desp = c.businessname
			logger.info('desp=>', descp)
			parent_type, parent_id = _get_node_parent_info(node_type, c.id)
			
			# if parent_id==-1:
			# 	return childs
			
			logger.info('p=>', node_type, c.id)
			logger.info('res=>', parent_type, parent_id)
			kind = '%s_%s' % (parent_type, node_type)
			logger.info('o info=>%s %s %s' % (kind, parent_id, c.id))
			ov = mm.Order.objects.get(kind=kind, main_id=parent_id, follow_id=c.id).value
			_m[str(ov)] = c
		###
		akeys = [int(k.replace('1.', '')) for k in _m.keys()]
		bkeys = sorted(akeys)
		ckeys = ['1.' + str(k) for k in bkeys]
		
		for key in ckeys:
			result.append(_m.get(str(key)))
		
		return result
	
	else:
		return []


def _build_node(kind, src_uid, target_uid, move_type, user, build_nodes):
	target_type = kind.split('_')[0]
	target_type_upper = target_type[0].upper() + target_type[1:]
	if target_type_upper == 'Business':
		target_type_upper = 'BusinessData'
	
	src_type = kind.split('_')[1]
	# logger.info('src_type=>',src_type)
	src_type_upper = src_type[0].upper() + src_type[1:]
	if src_type_upper == 'Businessdata' or src_type_upper == 'Business':
		src_type_upper = 'BusinessData'
	
	##构造target数据(重新生成)
	logger.info('==构建新节点实体数据')
	if kind in ('step_businessdata'):
		kind = 'step_business'
	logger.info(src_type_upper, '=>', src_uid)
	src = eval("mm.%s.objects.get(id=%s)" % (src_type_upper, src_uid))
	# logger.info('老id=>',src.id)
	src.id = None
	src.save()
	logger.info('构建完成[%s]' % src)
	build_nodes.append(src)
	# logger.info('新id=>',src.id)
	
	##构造target关联
	logger.info('==构建新节点关联关联==')
	# logger.info(move_type)
	# logger.info('kind=>',kind)
	# logger.info('%s->%s'%(target_uid,src.id))
	
	if move_type == 'inner':
		order = mm.Order()
		order.kind = kind
		order.main_id = target_uid
		order.follow_id = src.id
		order.value = getnextvalue(kind, target_uid)
		order.author = user
		logger.info('inner 构建完成[%s]' % order)
		order.save()
	else:
		kindlike = '%s_' % target_type
		
		logger.info('kindlike=>', kindlike)  ##error
		logger.info('targetid=>', target_uid)
		
		parent_order = mm.Order.objects.get(Q(kind__contains=kindlike) & Q(follow_id=target_uid))
		parent_type = parent_order.kind.split('_')[0]
		##不可能为business
		parent_type_upper = parent_type.split('_')[0][0].upper() + parent_type.split('_')[0][1:]
		parent = eval("mm.%s.objects.get(id=%s)" % (parent_type_upper, parent_order.main_id))
		
		order = mm.Order()
		order.author = user
		order.kind = '%s_%s' % (parent_type, src_type)  ###?
		order.main_id = parent.id
		order.follow_id = src.id
		
		o = mm.Order.objects.get(Q(kind__contains='%s_' % target_type) & Q(follow_id=target_uid))
		if len(build_nodes) == 1 and move_type == 'prev':
			ogroup = o.value.split('.')[0]
			oindex = int(o.value.split('.')[1])
			order.value = '%s.%s' % (ogroup, oindex)
		elif len(build_nodes) == 1 and move_type == 'next':
			ogroup = o.value.split('.')[0]
			oindex = int(o.value.split('.')[1])
			order.value = '%s.%s' % (ogroup, oindex)
		
		else:
			order.value = getnextvalue(kind, target_uid)
		
		logger.info('%s 构建完成[%s]' % (move_type, order))
		
		order.save()
	
	##子节点存在情况
	# parent_type,parent_id=_get_node_parent_info(src_type,src_uid)
	# k2='%s_%s'%('',src_type)
	# logger.info('k2=>',k2)
	childs = getchild('%s_' % src_type, src_uid)  ##???
	# logger.info('==兄弟节点排序=>',childs)
	childs = _sort_by_weight(childs)
	# logger.info('排序结果=>',childs)
	
	# if child_type=='businessdata':
	# 	continue;
	
	if len(childs) > 0:
		logger.info('==构建新节点下子节点数据')
	for child in childs:
		child_type = child.__class__.__name__.lower()  ###?
		src_type = src.__class__.__name__.lower()
		
		_build_node('%s_%s' % (src_type, child_type), child.id, src.id, 'inner', user, build_nodes)


def _build_all(src_id, target_id, move_type, user, is_copy, callername):
	logger.info('==开始构建目标位置所有节点==')
	src_uid = src_id.split('_')[1]
	target_uid = target_id.split('_')[1]
	src_type = src_id.split('_')[0]
	target_type = target_id.split('_')[0]
	kind = '%s_%s' % (target_type, src_type)
	
	###获取事件节点model对象
	elementclass = src_id.split('_')[0]
	elementid = src_id.split('_')[1]
	if elementclass == 'business':
		elementclass = 'businessData'
	elementclass = _first_word_up(elementclass)
	element = eval("mm.%s.objects.get(id=%s)" % (elementclass, elementid))
	##
	if move_type != 'inner':
		logger.info('targetid=>', target_uid)
		# order=Order.objects.get(follow_id=target_uid)
		# parenttype=order.kind.split('_')[0]
		# kind='%s_%s'%(parenttype,src_type)
		parent_type, parent_id = _get_node_parent_info(src_type, src_uid)
		kind = '%s_%s' % (parent_type, src_type)
	
	build_nodes = []
	_build_node(kind, src_uid, target_uid, move_type, user, build_nodes)
	
	logger.info('--构建目标位置所有节点结束')
	del_nodes = []
	_get_delete_node(src_uid, src_type, is_copy, del_nodes)
	# 移动目标区域兄弟节点需重新生成权重
	logger.info('==获取移动复制构造的第一个model对象=>', build_nodes[0])
	##处理源数据
	logger.info('==获取拖动源待处理节点列表=>', del_nodes)
	for t in del_nodes:
		tclass = _first_word_up(t[0])
		if tclass in ('Business', 'Businessdata'):
			tclass = 'BusinessData'
		el = eval("mm.%s.objects.get(id=%s)" % (tclass, t[1]))
		_regen_weight(callername, el, trigger='del', target_id=target_id)
	logger.info('--拖动源处理结束')
	#
	logger.info('==处理拖动目标位置的排序显示')
	_regen_weight(callername, build_nodes[0], trigger=move_type, target_id=target_id)


def _resort(orderlist, movetype, src_uid, target_uid):
	indexa = None
	indexb = None
	a = None
	b = None
	cindex = None
	
	target_uid = target_uid.split('.')[1]
	i = 0
	for order in orderlist:
		if order.follow_id == src_uid:
			indexa = i
		
		if order.follow_id == target_uid:
			indexb = i
		i = i + 1
	
	a = orderlist.pop(indexa)
	l = abs(indexb - indexa)
	
	if movetype == 'prev':
		orderlist.insert(indexb - 1, a)
	elif movetype == 'next':
		orderlist.insert(indexb + 1, a)
	
	return orderlist


def get_search_match(searchvalue):
	'''1.匹配的是父节点
	   2.匹配的是子节点
	   3.无匹配结果
	'''
	import time
	logger.info('1=>', time.time())
	nodes = get_full_tree()
	logger.info('2=>', time.time())
	for node in nodes:
		if searchvalue in node.get('name'):
			# node['name']="<s>%s</s>"%node['name']
			# node['name']="<span style='color:red;'>%s</span>"%node['name']
			_expand_parent(node, nodes)
	logger.info('3=>', time.time())
	return nodes


icon_map = {
	'product': 'fa icon-fa-home',
	'plan': 'fa icon-fa-product-hunt',
	'case': 'fa icon-fa-folder',
	'step': 'fa icon-fa-file-o',
	'business': 'fa icon-fa-leaf'
}


def get_full_tree():
	nodes = []
	root = {'id': -1, 'name': '产品线', 'type': 'root', 'textIcon': 'fa fa-pinterest-p', 'open': True}
	# products = list(mm.Product.objects.all())
	query_product_sql = 'select description,author_id,id from manager_product'
	with connection.cursor() as cursor:
		cursor.execute(query_product_sql)
		products = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
	# logger.info('products=>',products)
	for product in products:
		productname = product['description']
		productobj = {
			'id': 'product_%s' % product['id'],
			'pId': -1,
			'name': productname,
			'type': 'product',
			'textIcon': icon_map.get('product')
		}
		
		nodes.append(productobj)
		# plan_order_list = list(mm.Order.objects.filter(kind='product_plan', main_id=product['id']))
		
		query_plan_order_list = "select * from manager_order where kind='product_plan' and main_id=%s"
		with connection.cursor() as cursor:
			cursor.execute(query_plan_order_list, [product['id']])
			plan_order_list = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
		
		logger.info('$' * 200)
		logger.info('plan_order_list=>', plan_order_list, len(plan_order_list))
		for order in plan_order_list:
			try:
				# plan = mm.Plan.objects.get(id=int(order.follow_id))
				query_plan_sql = 'select * from manager_plan where id=%s'
				with connection.cursor() as cursor:
					cursor.execute(query_plan_sql, [order['follow_id']])
					plan = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()][0]
				
				planname = plan['description']
				planobj = {
					'id': 'plan_%s' % plan['id'],
					'pId': 'product_%s' % product['id'],
					'name': planname,
					'type': 'plan',
					'textIcon': icon_map.get('plan')
				}
				
				nodes.append(planobj)
			except:
				# logger.info('异常查询 planid=>', order['follow_id'])
				continue;
			
			# case_order_list = ordered(list(mm.Order.objects.filter(kind='plan_case', main_id=plan['id'])))
			
			query_case_order_list_sql = "select * from manager_order where kind='plan_case' and main_id=%s"
			with connection.cursor() as cursor:
				cursor.execute(query_case_order_list_sql, [plan['id']])
				case_order_list = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
				case_order_list.sort(key=lambda e: e.get('value'))
			
			logger.info('case_order_list=>', case_order_list, len(case_order_list))
			
			for order in case_order_list:
				# case = mm.Case.objects.get(id=order.follow_id)
				query_case_sql = 'select * from manager_case where id=%s'
				with connection.cursor() as cursor:
					cursor.execute(query_case_sql, [order['follow_id']])
					caselist = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
				if len(caselist) > 0:
					case = caselist[0]
					casename = case['description']
					caseobj = {
						'id': 'case_%s' % case['id'],
						'pId': 'plan_%s' % plan['id'],
						'name': case['description'],
						'type': 'case',
						'textIcon': icon_map.get('case')
					}
					nodes.append(caseobj)
				_add_next_case_node(plan, case, nodes)
	
	nodes.append(root)
	return nodes


def _add_next_case_node(parent, case, nodes):
	##处理所属单节点
	# step_order_list = ordered(list(mm.Order.objects.filter(kind='case_step', main_id=case['id'])))
	query_step_order_sql = 'select * from manager_order where kind=%s and main_id=%s'
	with connection.cursor() as cursor:
		cursor.execute(query_step_order_sql, ['case_step', case['id']])
		step_order_list = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
		step_order_list.sort(key=lambda e: e.get('value'))
	
	# logger.info('step_order_list11=>',step_order_list,len(step_order_list))
	
	for order in step_order_list:
		# logger.info('stepid=>', order['follow_id'])
		# step = mm.Step.objects.get(id=order['follow_id'])
		query_step_sql = 'select * from manager_step where id=%s'
		with connection.cursor() as cursor:
			cursor.execute(query_step_sql, [order['follow_id']])
			steplist = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
		
		# logger.info('#'*200)
		# logger.info('steplist=>',len(steplist))
		if len(steplist) > 0:
			step = steplist[0]
			nodes.append({
				'id': 'step_%s' % step['id'],
				'pId': 'case_%s' % case['id'],
				'name': step['description'],
				'type': 'step',
				'textIcon': icon_map.get('step')
			})
		
		# business_order_list = ordered(list(mm.Order.objects.filter(kind='step_business', main_id=step['id'])))
		query_business_order_list_sql = "select * from manager_order where kind='step' and main_id=%s"
		with connection.cursor() as cursor:
			cursor.execute(query_business_order_list_sql, [step['id']])
			business_order_list = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
			business_order_list.sort(key=lambda e: e.get('value'))
		
		for order in business_order_list:
			# business = mm.BusinessData.objects.get(id=order.follow_id)
			query_business_sql = 'select * from manager_businessdata where id=%s'
			
			with connection.cursor() as cursor:
				cursor.execute(query_business_sql, [order['follow_id']])
				businesslist = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
			
			if len(businesslist) > 0:
				business = businesslist[0]
				nodes.append({
					'id': 'business_%s' % business['id'],
					'pId': 'step_%s' % step['id'],
					'name': business['businessname'],
					'type': 'business',
					'textIcon': icon_map.get('business')
				})
	
	##处理多级节点
	# case_order_list = ordered(list(mm.Order.objects.filter(kind='case_case', main_id=case['id'])))
	query_case_order_list_sql = "select * from manager_order where kind='case_case' and main_id=%s"
	with connection.cursor() as cursor:
		cursor.execute(query_case_order_list_sql, [case['id']])
		case_order_list = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
		case_order_list.sort(key=lambda e: e.get('value'))
	for order in case_order_list:
		# case0 = mm.Case.objects.get(id=order.follow_id)
		query_case_sql = 'select * from manager_case where id=%s'
		with connection.cursor() as cursor:
			cursor.execute(query_case_sql, [order['follow_id']])
			case0 = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()][0]
		
		nodes.append({
			'id': 'case_%s' % case0['id'],
			'pId': 'case_%s' % case['id'],
			'name': case0['description'],
			'type': 'case',
			'textIcon': icon_map.get('case')
		})
		
		_add_next_case_node(case, case0, nodes)


def _expand_parent(node, node_set):
	for c in node_set:
		if node.get('pId') == c.get('id'):
			c['open'] = True
			_expand_parent(c, node_set)


def _get_parent_info(node):
	pass


def _get_child_info(node):
	pass


def _first_word_up(text):
	if len(text) == 1:
		return text.upper()
	elif len(text) > 1:
		return text[0].upper() + text[1:]
	else:
		return ''


def weight_decorate(kind, followid):
	final = ''
	weight = '-9999'
	text = ''
	t = kind.split('_')[1][0].upper() + kind.split('_')[1][1:]
	desp = 'description'
	if t == 'Business':
		t = 'BusinessData'
		desp = 'businessname'
	text = eval('mm.%s.objects.get(id=%s).%s' % (t, followid, desp))
	logger.info('kin=>', kind)
	logger.info('fl=>', followid)
	weight = mm.Order.objects.get(kind=kind, follow_id=followid).value
	# final=weight+' ' +text
	final = text
	return final


def _status_decorate(decoratename, text):
	if decoratename == 'error':
		text = "<span class='error'>%s</span>" % text
	
	elif decoratename == 'fail':
		text = "<span class='fail'>%s</span>" % text
	
	elif decoratename == 'success':
		text = "<span class='success'>%s</span>" % text
	
	elif decoratename == 'skip':
		text = "<span class='skip'>%s</span>" % text
	
	elif decoratename == 'disabled':
		text = "<s>%s</s>" % text
	
	elif decoratename == 'high_light':
		text = "<span style='background-color:#FFFF00'>%s</span>" % text
	
	return text


def del_node_force(request):
	'''强制递归删除节点
	'''
	
	logger.info('=强制del_node_force删除数据')
	id_ = request.POST.get('ids')
	ids = id_.split(',')
	for i in ids:
		node_type = i.split('_')[0]
		idx = i.split('_')[1]
		
		# logger.info('node_type=>',node_type)
		# logger.info('idx=>',idx)
		
		##重排序
		parent_type, parent_id = _get_node_parent_info(node_type, idx)
		
		_regen_weight_force(parent_type, parent_id, ignore_id=idx)
		
		#
		
		if node_type == 'product':
			_del_product_force(idx)
		
		elif node_type == 'plan':
			Cron.delcrontab(idx)
			_del_plan_force(idx)
		elif node_type == 'case':
			up = _get_case_parent_info(idx)[0]
			_del_case_force(idx, up='%s_case' % up)
		elif node_type == 'step':
			_del_step_force(idx)
	
	return {
		'status': 'success',
		'msg': '删除成功.'
	}


def _get_node_parent_info(node_type, node_id):
	if node_type == 'case':
		return _get_case_parent_info(node_id)
	elif node_type == 'product':
		return ('root', -1)
	else:
		if node_type in ('businessdata'):
			node_type = 'business'
		
		kindlike = '_%s' % node_type
		logger.info('fid=>%s kind like=>%s' % (node_id, kindlike))
		o = mm.Order.objects.get(Q(kind__contains=kindlike) & Q(follow_id=node_id))
		return (o.kind.split('_')[0], o.main_id)


def _get_case_parent_info(case_id):
	# logger.info('del case id=>',case_id)
	case_desp = mm.Case.objects.get(id=case_id).description
	o = list(mm.Order.objects.filter(Q(kind__contains='_case') & Q(follow_id=case_id)))[0]
	# logger.info('order=>',o)
	kind = o.kind.split('_')[0]
	# logger.info('获得文件夹[%s]上层节点类型=>%s'%(case_desp,kind))
	return (kind, o.main_id)


def _del_product_force(product_id):
	try:
		product = mm.Product.objects.get(id=product_id)
		product_order_list = list(mm.Order.objects.filter(kind='product_plan', main_id=product_id))
		
		for o in product_order_list:
			# o.delete()
			_del_plan_force(o.follow_id)
		
		product.delete()
	except:
		logger.info(traceback.format_exc())


def _del_plan_force(plan_id):
	# 取消上层依赖
	try:
		mm.Order.objects.get(kind='product_plan', follow_id=plan_id).delete()
	except:
		logger.info('取消上层依赖异常.')
	try:
		plan = mm.Plan.objects.get(id=plan_id)
		plan_order_list = list(mm.Order.objects.filter(kind='plan_case', main_id=plan_id))
		
		if len(plan_order_list) > 0:
			for o in plan_order_list:
				# o.delete()
				_del_case_force(o.follow_id, up='plan_case')
		
		plan.delete()
	except:
		logger.info(traceback.format_exc())


def _del_case_force(case_id, up='plan_case'):
	# 取消上层依赖
	try:
		mm.Order.objects.get(kind=up, follow_id=case_id).delete()
	except:
		logger.info('取消上层依赖异常.case_id=%s type=%s' % (case_id, up))
	
	case = mm.Case.objects.get(id=case_id)
	case_order_list = list(mm.Order.objects.filter(kind='case_step', main_id=case_id))
	case_order_list_2 = list(mm.Order.objects.filter(kind='case_case', main_id=case_id))
	
	##处理case->step
	for o in case_order_list:
		# o.delete()
		# Step.objects.get(id=o.follow_id).delete()
		_del_step_force(o.follow_id)
	
	# 处理case->case
	for o in case_order_list_2:
		c = mm.Case.objects.get(id=o.follow_id)
		_del_case_force(c.id, up='case_case')
	# c.delete()
	# o.delete()
	#
	case.delete()


def _del_step_force(step_id):
	# 取消上层依赖
	try:
		mm.Order.objects.get(kind='case_step', follow_id=step_id).delete()
	except:
		logger.info('取消上层依赖异常.')
	
	try:
		
		step = mm.Step.objects.get(id=step_id)
		step_order_list = list(mm.Order.objects.filter(kind='step_business', main_id=step_id))
		for o in step_order_list:
			o.delete()
			business = mm.BusinessData.objects.get(id=o.follow_id)
			business.delete()
		
		step.delete()
	
	except:
		logger.info('删除步骤异常=>', traceback.format_exc())


def replacetext(request):
	'''
	文本替换
	'''
	node_id=request.POST.get('uid')
	old=request.POST.get('old')
	expected=request.POST.get('new')
	callername=request.session.get('username')
	r=R(callername,startnode_id=node_id, old=old, expected=expected )
	scope={
		'check_plan':request.POST.get('check_plan'),
		'check_case':request.POST.get('check_case'),
		'check_step':request.POST.get('check_step'),
		'check_business':request.POST.get('check_business'),
		'check_url':request.POST.get('check_url'),
		'check_header':request.POST.get('check_header'),
		'check_property':request.POST.get('check_property'),
		}
	logger.info('scope:',scope)
	res= r.replace(scope)
	logger.info('文本替换结果:',res)
	return res

def replacerecover(request):
	'''
	文本替换回复
	'''
	uid=request.POST.get('uid')
	logger.info('开始节点文本恢复 uid=',uid)
	return R(request.session.get('username')).recover(uid)





