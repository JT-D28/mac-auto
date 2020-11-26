import difflib, time
import hashlib

import chardet
from django.db import connection, transaction
from django.shortcuts import render, redirect
from django.utils.encoding import escape_uri_path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import HttpResponse, JsonResponse

from django.db.models import Q
from typing import List

from manager.models import *
from manager.db import Mysqloper
from django.conf import settings
from login.models import *
from .StartPlan import RunPlan
from .cm import addrelation, _get_node_parent_info, querynodelink
from .core import *
from manager.operate.cron import Cron
from .invoker import *
from . import cm
import json, xlrd, base64, traceback

from .invoker import _is_function_call
from .operate.dataMove import DataMove
from .operate.transformer import Transformer
from .pa import MessageParser

from manager.context import Me2Log as logger
from tools.mock import TestMind
from manager.cm import getchild


# 文件空间上传前检查文件名重复
@csrf_exempt
def checkfilename(request):
	filename = request.POST.get('filename')
	menu = request.POST.get('menu')
	code = 1 if isfile_exists(menu + '/' + filename) else 0
	return JsonResponse({'code': code})


def isfile_exists(filename):
	filepath = os.path.join(os.path.join(os.path.dirname(__file__), 'storage/private/File'), filename)
	if os.path.exists(filepath):
		return True
	else:
		return False


# 文件上传
@csrf_exempt
def upload(request):
	filemap = dict()
	filenames = []
	content_list = []
	
	files = request.FILES.getlist('file_data')
	for file in files:
		for chunk in file.chunks():
			logger.info('上传文件名称=>', file.name)
			# content_list.append(chunk)
			filemap[file.name] = chunk
	
	callername = request.session.get('username')
	kind = request.POST.get('kind')
	
	logger.info('kind=>', kind)
	content_type = request.POST.get('content_type')
	
	if kind == 'datamovein':
		taskid = EncryptUtils.md5_encrypt(str(datetime.datetime.now()))
		t = Transformer(callername, filemap.values(), content_type, taskid)
		res = t.transform()
		if res[0] == 'success':
			return JsonResponse(simplejson(code=0, msg='excel数据迁移完成 迁移ID=%s' % taskid), safe=False)
		else:
			return JsonResponse(simplejson(code=2, msg='excel数据迁移失败[%s] 迁移ID=%s' % (res[1], taskid)), safe=False)
	
	elif kind == 'dataimport':
		productid = request.POST.get('productid').split('_')[1]
		d = DataMove()
		for f in filemap:
			if f.endswith('.json'):
				res = d.import_plan(productid, filemap.values(), request.session.get('username'))
			elif f.endswith('.har'):
				res = d.har_import(productid, filemap.values(), request.session.get('username'))
		
		if res[0] == 'success':
			return JsonResponse(simplejson(code=0, msg='数据导入完成'), safe=False)
		else:
			return JsonResponse(simplejson(code=2, msg='数据导入失败[%s]' % res[1]), safe=False)
	elif kind == 'personfile':
		upload_dir = os.path.join(os.path.dirname(__file__), 'storage', 'private', 'File')
		menu = request.POST.get('menu')
		customnamemap = json.loads(request.POST.get('customnamemap'))
		try:
			for filename in filemap:
				filepath = os.path.join(upload_dir, menu, filename)
				with open(filepath, 'wb') as f:
					f.write(filemap[filename])
				file_encoding = chardet.detect(filemap[filename]).get('encoding') if getFileFolderSize(
					filepath) != 0 else 'blank'
				try:
					file = FileMap.objects.get(filename=filename, path=menu + '/' + filename)
					file.customname = customnamemap[filename]
					file.code = file_encoding
					file.save()
				except:
					FileMap(filename=filename, path=menu + '/' + filename, customname=customnamemap[filename],
					        code=file_encoding).save()
			
			return JsonResponse(simplejson(code=0, msg='文件上传完成'), safe=False)
		except:
			logger.info(traceback.format_exc())
			return JsonResponse(simplejson(code=3, msg='文件上传异常'), safe=False)
	else:
		return JsonResponse(simplejson(code=4, msg='kind错误'), safe=False)


"""
DB相关
"""


# 数据连接测试
@csrf_exempt
def testdbcon(request):
	description = request.POST.get('description'),
	dbtype = request.POST.get('kind')
	dbname = request.POST.get('dbname')
	host = request.POST.get('host')
	port = request.POST.get('port')
	username = request.POST.get('accountname')
	password = request.POST.get('password')
	if dbtype == 'WinRM':
		try:
			import winrm
			wintest = winrm.Session("http://{}:{}/wsman".format(host, port), auth=(username, password))
			ret = wintest.run_cmd("chdir")
			status = 'success'
			msg = "windows服务器连接成功"
		except:
			status = 'error'
			msg = traceback.format_exc()
	else:
		status, msg = db_connect({
			'description': description,
			'dbtype': dbtype,
			'dbname': dbname,
			'host': host,
			'port': port,
			'username': username,
			'password': password
		})
	
	if status is 'success':
		return JsonResponse(simplejson(code=0, msg=msg), safe=False)
	else:
		return JsonResponse(simplejson(code=4, msg=msg), safe=False)


# 查询一个数据连接
@csrf_exempt
def queryonedb(request):
	code = 0
	msg = ''
	res = None
	try:
		res = DBCon.objects.get(id=request.POST.get('id'))
		pass
	except:
		code = 1
		msg = '查询异常[%s]' % traceback.format_exc()
	finally:
		jsonstr = json.dumps(res, cls=DBEncoder)
		return JsonResponse(jsonstr, safe=False)


# 查询数据连接列表
@csrf_exempt
def querydb(request):
	searchvalue = request.GET.get('searchvalue')
	searchvalue = searchvalue if searchvalue not in [None, ''] else ''
	logger.info("searchvalue=>", searchvalue)
	queryschemevalue = request.GET.get('querySchemeValue')
	queryschemevalue = queryschemevalue if queryschemevalue not in [None, ''] else ''
	logger.info("SchemeValue=>", queryschemevalue)
	res = list(DBCon.objects.filter((Q(description__icontains=searchvalue) | Q(dbname__icontains=searchvalue) | Q(
		host__icontains=searchvalue) | Q(port__icontains=searchvalue) | Q(kind__icontains=searchvalue)) & Q(
		scheme__contains=queryschemevalue)))
	limit = request.GET.get('limit')
	page = request.GET.get('page')
	res, total = getpagedata(res, page, limit)
	
	jsonstr = json.dumps(res, cls=DBEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)


# 新增数据连接
@csrf_exempt
def addcon(request):
	code, msg = (0, '添加成功')
	try:
		description = request.POST.get('description')
		kind = request.POST.get('kind')
		dbname = request.POST.get('dbname')
		host = request.POST.get('host')
		port = request.POST.get('port')
		scheme = request.POST.get('scheme')
		username = request.POST.get('username')
		password = request.POST.get('password')
		DBCon(kind=kind, dbname=dbname, host=host, port=port, username=username, password=password,
		      description=description, scheme=scheme).save()
	except:
		logger.info(traceback.format_exc())
		code, msg = (1, '添加异常%s' % traceback.format_exc())
	return JsonResponse({'code': code, 'msg': msg})


# 删除数据连接
@csrf_exempt
def delcon(request):
	ids = request.POST.get('ids').split(',')
	code, msg = (0, '删除成功')
	try:
		for id in ids:
			DBCon.objects.get(id=id).delete()
	except:
		code, msg = (1, "删除失败[%s]" % traceback.format_exc())
	
	return JsonResponse({'code': code, 'msg': msg})


# 编辑数据连接
@csrf_exempt
def editcon(request):
	code, msg = (0, '编辑成功')
	id = request.POST.get('id')
	try:
		con = DBCon.objects.get(id=id)
		con.kind = request.POST.get('kind')
		con.description = request.POST.get('description')
		con.dbname = request.POST.get('dbname')
		con.username = request.POST.get('username')
		con.password = request.POST.get('password')
		con.host = request.POST.get('host')
		con.port = request.POST.get('port')
		con.scheme = request.POST.get('scheme')
		con.save()
	except:
		code, msg = (1, '添加异常%s' % traceback.format_exc())
		logger.error(msg)
	
	return JsonResponse({'code': code, 'msg': msg})


# 获取用例节点对应的db方案名
def getplan(id, kind):
	logger.info('get', id, kind)
	if kind == 'case':
		try:
			k = Order.objects.get(follow_id=id, kind='plan_case', isdelete=0)
		except:
			k = Order.objects.get(follow_id=id, kind='case_case', isdelete=0)
		schemename = getplan(k.main_id, k.kind.split('_')[0])
		return schemename
	elif kind == 'step':
		k = Order.objects.get(follow_id=id, kind='case_step', isdelete=0)
		schemename = getplan(k.main_id, k.kind.split('_')[0])
		return schemename
	elif kind == 'plan':
		schemename = Plan.objects.get(id=id).dbscheme
		return schemename


# 数据管理页面查询 和 用例管理页面查询数据连接列表
@csrf_exempt
def querydblist(request):
	code, msg = 0, ''
	res = []
	scheme = request.POST.get('schemevalue')
	id = request.POST.get('id')
	type = request.POST.get('type')
	if type is not None:
		try:
			res = list(DBCon.objects.filter().distinct().annotate(name=F('description')).values('name'))
		except:
			logger.info(traceback.format_exc())
			code = 4
			msg = '查询数据库列表信息异常'
			return JsonResponse(simplejson(code=code, msg=msg), safe=False)
	else:
		try:
			if scheme != '':
				res = list(DBCon.objects.filter(scheme=scheme).annotate(name=F('description')).values('name'))
				logger.info(res)
			elif id != '' and id is not None:
				dbscheme = getplan(id.split('_')[1], id.split('_')[0])
				res = list(
					DBCon.objects.filter(scheme=dbscheme).annotate(name=F('description')).values('name'))
		# logger.info('...', res)
		except:
			logger.info(traceback.format_exc())
			code = 4
			msg = '查询数据库列表信息异常'
			return JsonResponse(simplejson(code=code, msg=msg), safe=False)
	return JsonResponse(simplejson(code=0, msg='操作成功', data=res), safe=False)


# 复制数据连接
@csrf_exempt
def copyDbCon(request):
	action = request.POST.get('action')
	dbids = request.POST.get('dbids').split(',')
	copyschemevalue = request.POST.get('copyschemevalue')
	msg = dbconRepeatCheck(dbids, copyschemevalue, action)
	code = 1
	if msg == '':
		try:
			code = 0
			if action == '1':
				for id in dbids:
					dbcon = DBCon.objects.get(id=id)
					newdbcon = DBCon()
					newdbcon.kind = dbcon.kind
					newdbcon.dbname = dbcon.dbname
					newdbcon.host = dbcon.host
					newdbcon.port = dbcon.port
					newdbcon.username = dbcon.username
					newdbcon.password = dbcon.password
					newdbcon.description = dbcon.description
					newdbcon.author = User.objects.get(name=request.session.get('username'))
					newdbcon.scheme = copyschemevalue
					newdbcon.save()
				msg = '复制成功'
			elif action == '0':
				for id in dbids:
					dbcon = DBCon.objects.get(id=id)
					dbcon.scheme = copyschemevalue
					dbcon.save()
				msg = '修改成功'
		except:
			code = 1
			msg = traceback.format_exc()
			logger.info(msg)
	return JsonResponse({'code': code, 'msg': msg})


# 数据连接重复检查 action=0 复制  1 仅仅修改
def dbconRepeatCheck(dbids, copyschemevalue, action):
	logger.info(dbids, copyschemevalue, action)
	msg = ''
	# 一个方案下面描述名不能重复
	if action == '1':
		for id in dbids:
			description = DBCon.objects.get(id=id).description
			dbcon = DBCon.objects.filter(scheme=copyschemevalue, description=description)
			if len(dbcon) == 0:
				continue
			else:
				msg += "<div class='copyerror'>配置方案【%s】下已存在描述为【%s】的数据连接<br></div>" % (copyschemevalue, description)
	elif action == '0':
		for id in dbids:
			description = DBCon.objects.get(id=id).description
			oldcon = DBCon.objects.filter(~Q(id=id) & Q(description=description, scheme=copyschemevalue))
			if len(oldcon) == 0:
				continue
			else:
				msg += "<div class='copyerror'>配置方案【%s】下已存在描述为【%s】的数据连接<br></div>" % (
					copyschemevalue,
					description) if copyschemevalue != '' else "<div class='copyerror'>已存在描述名为【%s】的全局数据连接配置<br></div>" % description
	return msg


"""
变量相关接口
"""


@csrf_exempt
def queryOneVar(request):
	try:
		var = Variable.objects.values().get(id=request.POST.get('id'))
		return JsonResponse({"code": 0,"data":var})
	except:
		logger.info(traceback.format_exc())
		msg = '查询异常[%s]' % traceback.format_exc()
		return JsonResponse({'code': 1, 'msg': msg})


@csrf_exempt
def queryVars(request):
	searchValue = request.POST.get('searchvalue').strip()
	searchValue = '%' + searchValue + '%'
	limit = request.POST.get('limit')
	page = request.POST.get('page')
	userId = request.POST.get('userid')
	spaceId = request.POST.get("spaceid", 0)
	tags = request.POST.get('tags').split(",")
	strtag = '%'
	for tag in tags:
		if tag == '0':
			strtag = '%%'
		else:
			strtag += tag + '%'
	
	with connection.cursor() as cursor:
		sql = '''SELECT v.label,v.space_id,v.id,v.description,v.`key`,v.gain,`value`,is_cache,u.NAME AS author
		FROM `manager_variable` v,login_user u where v.author_id=u.id
		and (v.description like '%s' or v.`key` like '%s' or v.gain like '%s' or value like '%s') and v.space_id=%s and v.label like '%s'
		  ''' % (searchValue, searchValue, searchValue, searchValue, spaceId,strtag)
		print(sql)
		if userId != '-1':
			sql += ' and v.author_id=%s'%userId
		cursor.execute(sql)
		rows = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
		res, total = getpagedata(rows, page, limit)
	jsonstr = json.dumps(res, cls=VarEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)


def queryVarInSpace(request):
	searchValue = request.POST.get("search")
	spaceList = []
	searchValue = '%' + searchValue + '%'
	with connection.cursor() as cursor:
		sql = '''SELECT space_id from manager_variable v where ( v.description like '%s' or v.`key` like '%s' or v.gain like '%s' or value like '%s')''' % (searchValue, searchValue, searchValue, searchValue)
		cursor.execute(sql)
		rows = cursor.fetchall()
		if len(rows)!=0:
			spaceids = []
			for row in rows:
				spaceids.append(row[0])
			querySpace = '''SELECT * from manager_varspace where id in %s'''
			cursor.execute(querySpace,[spaceids])
			if 0 in spaceids or searchValue=="":
				spaceList = [{"id": 0, "name": "全局", "planid": 0}]
			spaceList.extend([dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()])
	return JsonResponse({"code": 0, "data": spaceList})


def editVarSpaceName(request):
	newName = request.POST.get("newName")
	id = request.POST.get("id")

	exits = Varspace.objects.filter(name=newName).exclude(id = id).count()
	if exits!=0:
		return JsonResponse({"code": 1, "msg": "修改失败，存在同名的变量空间"})
	vs = Varspace.objects.get(id=id)
	vs.name = newName
	vs.save()
	return JsonResponse({"code": 0, "msg": "修改成功"})


def delVarSpace(request):
	id = request.POST.get("id")
	if id=="0":
		return JsonResponse({'code': 1, 'msg': "不能删除全局空间"})
	try:
		Varspace.objects.get(id=id).delete()
		Variable.objects.filter(space_id=id).delete()
		
		return JsonResponse({'code': 0, 'msg': "删除成功"})
	except:
		logger.info(traceback.format_exc())
		msg = '删除异常[%s]' % traceback.format_exc()
		return JsonResponse({'code': 1, 'msg': msg})
	
def addVarSpace(request):
	name = request.POST.get("name")
	if name =="全局":
		return JsonResponse({'code': 1, 'msg': "不能命名为全局"})
	if Varspace.objects.filter(name=name).exists():
		return JsonResponse({'code': 1, 'msg': "已存在名称为[%s]的空间"%name})
	Varspace(name=name).save()
	return JsonResponse({'code': 0, 'msg': "新建空间%s成功"%name})


def queryAllVarsInSpace(request):
	spaceid = request.POST.get("spaceid")
	varList = Variable.objects.values().filter(space_id=spaceid)
	return JsonResponse({'code': 0, "data":list(varList)})


def copyVars(request):
	ids = request.POST.get("ids").split(",")
	toSpace = request.POST.get("toSpace")
	with transaction.atomic():
		save_id = transaction.savepoint()
		for id in ids:
			oldVar = Variable.objects.get(id=id)
			if Variable.objects.filter(space_id=toSpace,key=oldVar.key).exists():
				transaction.savepoint_rollback(save_id)
				return JsonResponse({'code': 1, "msg": "key ：[%s]在目标空间中已存在,全部复制未生效"%oldVar.key})
			newVar = Variable(description=oldVar.description,key=oldVar.key,value=oldVar.value,gain=oldVar.gain,is_cache=oldVar.is_cache,
			                  author_id=oldVar.author_id,space_id=toSpace,label=oldVar.label)
			newVar.save()
	return JsonResponse({'code': 0, "msg": "全部复制成功"})

	
@csrf_exempt
def delVar(request):
	id_ = request.POST.get('ids')
	ids = id_.split(',')
	code = 0
	msg = '删除成功.'
	try:
		for i in ids:
			vf = Variable.objects.get(id=i)
			vf.delete()
	except:
		code = 1
		msg = "删除失败[%s]" % traceback.format_exc()
	finally:
		return JsonResponse({"code":code,"msg":msg})


@csrf_exempt
def editVariable(request):
	logger.info("===============editvar=========================================================")
	varId = request.POST.get('id')
	code = 0
	msg = ''
	try:
		key = request.POST.get("key")
		spaceid = request.POST.get("spaceid")
		exits = Variable.objects.filter(space_id=spaceid,key=key).exclude(id=varId).count()
		if exits!=0:
			spaceName = "全局" if spaceid=='0' else Varspace.objects.get(id=spaceid).name
			return JsonResponse({'code': 2, 'msg': "编辑失败，空间[%s]下已存在key为[%s]的变量" % (spaceName, key)})
		
		var = Variable.objects.get(id=varId)
		var.key = key
		var.value = request.POST.get("value")
		var.description = request.POST.get("description")
		var.gain = request.POST.get("gain")
		var.is_cache = True if request.POST.get("is_cache") == "true" else False
		var.label = request.POST.get("tag")
		var.author_id= User.objects.get(name=request.session.get('username', None)).id
		var.save()
		code = 0
		msg = "变量[%s]编辑成功"%var.description
	except:
		logger.info(traceback.format_exc())
		code = 1
		msg = "编辑失败[%s]" % traceback.format_exc()
	
	return JsonResponse({"code":code,"msg":msg})


@csrf_exempt
def editmultivar(request):
	# 绑定计划修改不考虑
	datas = eval(request.POST.get('datas'))
	code = 0
	msg = '修改成功'
	try:
		for data in datas:
			bindplans = Tag.objects.get(var=Variable.objects.get(id=data['id'])).planids
			state = varRepeatCheck(data['key'], bindplans, data['id'])
			if state != '':
				msg = state
				break
			data['customize'] = data['customize'].replace(
				"<span class='layui-badge' onclick=tagSpanClick(this) style='cursor:pointer;'>", '').replace('</span> ',
			                                                                                                 ';')
			var = Variable.objects.get(id=data['id'])
			var.value = data['value']
			var.description = data['description']
			var.gain = data['gain']
			var.key = data['key']
			var.save()
			tag = Tag.objects.get(var=var)
			tag.customize = data['customize']
			tag.save()
	except:
		logger.error(traceback.format_exc())
		msg = traceback.format_exc()
		code = 1
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


def varRepeatCheck(key, bindplans, editid=0):
	# 校验重复：同一个key只能最多只能有一个全局变量：isglobal=1;可以有多个绑定了计划的变量，其中绑定的计划不能有重复项
	logger.info(key, bindplans)
	bindplans = json.loads(bindplans)
	state = '变量重复校验出错！'
	try:
		if editid != 0:
			vars = Variable.objects.filter(key=key).exclude(id=editid)
		else:
			vars = Variable.objects.filter(key=key)
		logger.info(vars)
		if vars:
			# 如果没有传入绑定的计划id，先判断是否有全局变量
			if not bindplans:
				for var in vars:
					try:
						tag = Tag.objects.get(var=var, isglobal=1)
						if tag:
							state = "已经存在相同键名的全局变量！"
							break
					except:
						state = ''
			else:
				str = ''
				for var in vars:
					try:
						tag = Tag.objects.get(var=var, isglobal=0)
						if tag:
							planids = json.loads(tag.planids)
							for k, v in planids.items():
								if k in bindplans and bindplans[k] == v:
									str += k + '<br>'
					except:
						tag = Tag.objects.get(var=var, isglobal=1)
						if tag:
							logger.info('没有绑定计划的变量,有全局变量;')
							state = ''
				state = "变量%s已经绑定过计划：<br>%s" % (key, str) if str != '' else ''
		
		else:
			state = ''
	except:
		logger.info(traceback.format_exc())
		state = traceback.format_exc()
	finally:
		logger.info(state)
		return state


@csrf_exempt
def addVariable(request):
	code = 0
	msg = ''
	try:
		key = request.POST.get('key')
		spaceid = request.POST.get("spaceid")
		exitVars = Variable.objects.filter(space_id=spaceid, key=key).count()
		if exitVars != 0:
			spaceName = "全局" if spaceid=='0' else Varspace.objects.get(id=spaceid).name
			return JsonResponse({'code': 2, 'msg': "空间[%s]下已存在key为[%s]的变量" % (spaceName, key)})
		
		value = request.POST.get("value")
		description = request.POST.get("description")
		gain = request.POST.get("gain")
		is_cache = request.POST.get("is_cache")
		is_cache = True if is_cache =="true" else False
		tag = request.POST.get("tag")
		userid = User.objects.get(name=request.session.get('username', None)).id
		Variable(description=description,key=key,value=value,gain=gain,is_cache=is_cache,author_id=userid,space_id=spaceid,label=tag).save()
		msg = "变量[%s]新增成功"%description
	except:
		logger.info(traceback.format_exc())
		code = 1
		msg = "新增失败"
	return JsonResponse({'code': code, 'msg': msg})


@csrf_exempt
def copyVar(request):
	code = 0
	msg = ''
	varids = request.POST.getlist('varids[]')
	if not varids:
		varids = request.POST.get('varids', []).split(',')
	bindplans = request.POST.get('bindplans')
	action = request.POST.get('action')
	tags = request.POST.get('tags')
	logger.info(varids, bindplans)
	
	repvarkey = []
	for varid in varids:
		key = Variable.objects.get(id=varid).key
		if key not in repvarkey:
			repvarkey.append(key)
		else:
			return JsonResponse({'code': 1, 'msg': '你选择了多个相同键名的变量'})
	
	if action == '1':
		for varid in varids:
			key = Variable.objects.get(id=varid).key
			state = varRepeatCheck(key, bindplans)
			if state != '':
				return JsonResponse({'code': 1, 'msg': state})
			try:
				var = Variable.objects.get(id=varid)
				copyvar = Variable()
				tag = Tag()
				copyvar.description = var.description
				copyvar.key = var.key
				copyvar.gain = var.gain
				copyvar.is_cache = var.is_cache
				copyvar.value = var.value
				copyvar.author_id = User.objects.get(name=request.session.get('username', None)).id
				copyvar.save()
				tag.var = copyvar
				tag.isglobal = 1 if bindplans == '{}' else 0
				tag.customize = Tag.objects.get(var=var).customize if tags == '' else tags
				tag.planids = bindplans
				tag.save()
			except:
				msg = traceback.format_exc()
				logger.info(traceback.format_exc())
	elif action == '0':
		for varid in varids:
			key = Variable.objects.get(id=varid).key
			state = varRepeatCheck(key, bindplans, varid)
			if state != '':
				return JsonResponse({'code': 1, 'msg': state})
			try:
				tag = Tag.objects.get(var=Variable.objects.get(id=varid))
				tag.planids = bindplans
				if tags != '':
					tag.customize = tags
				tag.save()
			except:
				msg = traceback.format_exc()
				logger.info(traceback.format_exc())
	logger.info(msg)
	return JsonResponse({'code': code, 'msg': msg})


"""
用例管理

"""


@csrf_exempt
def queryonecase(request):
	code = 0
	msg = ''
	res = None
	try:
		res = Case.objects.get(id=request.POST.get('id').split('_')[1])
		pass
	except:
		code = 1
		msg = '查询异常[%s]' % traceback.format_exc()
	finally:
		jsonstr = json.dumps(res, cls=CaseEncoder)
		return JsonResponse(jsonstr, safe=False)


"""
计划管理
"""


@csrf_exempt
def transform(request):
	try:
		#
		dirname = os.path.dirname(__file__)
		excel_save = os.path.join(dirname, 'Excels')
		if not os.path.exists(excel_save):
			os.makedirs(excel_save)
		
		# 缓存转换文件
		tag = EncryptUtils.md5_encrypt(str(datetime.datetime.now()))
		config_wb = None
		data_wb = None
		#
		FILE_COUNT = 0
		FILE_CHECK = False
		
		for i in request.FILES:
			FILE_COUNT = FILE_COUNT + 1
			myFile = request.FILES[i]
			
			logger.info('接收文件=>', myFile.name)
			# logger.info('tmp=>',myFile.temporary_file_path())
			if myFile.name.__contains__('Config'):
				logger.info('包含=>', myFile.name)
				FILE_CHECK = True
				config_wb = xlrd.open_workbook(filename=None, file_contents=myFile.read())
			else:
				logger.info('部包含=>', myFile.name)
				data_wb = xlrd.open_workbook(filename=None, file_contents=myFile.read())
		
		logger.info('file_check=>%s file_count=>%s' % (FILE_CHECK, FILE_COUNT))
		if FILE_CHECK is False:
			return JsonResponse(simplejson(code=100, msg='没检查到配置文件Config.xlsx'), safe=False)
		
		if FILE_COUNT != 2:
			return JsonResponse(simplejson(code=101, msg='转换需要配置文件(Config.xlsx)和用例文件 实际上传%s个文件' % FILE_COUNT),
			                    safe=False)
		
		t = Transformer(config_wb, data_wb)
		t.transform()
		
		return JsonResponse(simplejson(code=0, msg='转换成功..'), safe=False)
	
	except:
		err = traceback.format_exc()
		return JsonResponse(simplejson(code=4, msg='转换异常[%s]' % err), safe=False)


def third_party_call(request):
	planid = request.GET.get('planid')
	taskid = gettaskid(planid)
	dbscheme = request.GET.get('scheme')
	runkind = request.GET.get('is_verify')
	if getRunningInfo(planid, 'isrunning') != '0':
		return JsonResponse(simplejson(code=1, msg="调用失败，任务正在运行中，稍后再试！"), safe=False)
	
	logger.info('调用计划=>', planid)
	logger.info('调用数据连接方案=>', dbscheme)
	x = RunPlan(taskid, planid, runkind, '定时任务', startNodeId='plan_' + str(planid))
	threading.Thread(target=x.start).start()
	return JsonResponse(simplejson(code=0, msg="调用成功,使用DB配置:[%s]" % dbscheme, taskid=taskid), safe=False)


@csrf_exempt
def queryoneplan(request):
	code, data, msg, dingding, mail, cron = (0, {}, '', 'close', 'close', {})
	planid = request.POST.get('id').split('_')[1]
	plan = Plan.objects.get(id=planid)
	try:
		mailconfig = MailConfig.objects.get(id=plan.mail_config_id)
		dingding = mailconfig.is_send_dingding
		mail = mailconfig.is_send_mail
	except:
		pass
	try:
		mailconfig = MailConfig.objects.get(id=plan.mail_config_id)
		dingding = mailconfig.is_send_dingding
		mail = mailconfig.is_send_mail
	except:
		pass
	
	try:
		crontab = Crontab.objects.values('status', 'value').filter(plan_id=planid)
		if crontab:
			crontab = crontab.first()
			cron = {
				'status': crontab['status'],
				'value': crontab['value']
			}
	except:
		print(traceback.format_exc())
		pass
	
	data = {
		'id': planid,
		'description': plan.description,
		'db_id': plan.db_id,
		'dbscheme': plan.dbscheme,
		'before_plan': plan.before_plan,
		'proxy': plan.proxy,
		'run_type': plan.run_type,
		'is_send_mail': mail,
		'is_send_dingding': dingding,
		'cron': cron,
		'varspace':plan.varspace
	}
	
	return JsonResponse({'code': code, 'data': data})


"""
任务相关
"""


@csrf_exempt
def runtask(request):
	callername = request.session.get('username')
	planid = request.POST.get('ids')
	runkind = request.POST.get('runkind')
	logger.info('获取待运行节点计划ID:', planid)
	taskid = gettaskid(planid)
	
	state_running = getRunningInfo(planid=planid, type='isrunning')
	
	if state_running != '0':
		msg = {"1": "验证", "2": "调试", "3": "定时"}[state_running]
		return JsonResponse(simplejson(code=1, msg='计划正在运行[%s]任务，稍后再试！' % msg), safe=False)
	
	x = RunPlan(taskid, planid, runkind, callername, startNodeId='plan_%s' % planid)
	threading.Thread(target=x.start).start()
	
	request.session['console_taskid'] = taskid
	return JsonResponse(simplejson(code=0, msg="你的任务开始运行", taskid=taskid), safe=False)


@csrf_exempt
def querytaskdetail(request):
	detail = {}
	taskid = request.GET.get('taskid')
	detail = Mongo.taskreport().find_one({"taskid": taskid})
	if request.POST.get('taskid'):
		detail = Mongo.taskreport().find_one({"taskid": request.POST.get('taskid')}, {'_id': 0})
		return JsonResponse({'data': json.dumps(detail)})
	
	return render(request, 'manager/taskdetail.html', locals())


"""

函数相关
"""


@csrf_exempt
def queryonefunc(request):
	code = 0
	msg = ''
	res = None
	try:
		res = Function.objects.get(id=request.POST.get('id'))
		res.body = base64.b64decode(res.body).decode(encoding='utf-8')
	
	except:
		code = 1
		msg = '查询异常[%s]' % traceback.format_exc()
	finally:
		jsonstr = json.dumps(res, cls=FunctionEncoder)
		return JsonResponse(jsonstr, safe=False)


@csrf_exempt
def queryfunc(request):
	searchvalue = request.GET.get('searchvalue')
	logger.info("searchvalue=>", searchvalue)
	res = []
	if searchvalue:
		res = list(Function.objects.filter(Q(name__icontains=searchvalue.strip())))
		res = res + getbuiltin(searchvalue)
	
	else:
		res = list(Function.objects.all()) + getbuiltin()
	
	limit = request.GET.get('limit')
	page = request.GET.get('page')
	res, total = getpagedata(res, page, limit)
	jsonstr = json.dumps(res, cls=FunctionEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)


@csrf_exempt
def delfunc(request):
	id_ = request.POST.get('ids')
	code = 0
	msg = ''
	ids = id_.split(",")
	try:
		for i in ids:
			if i != 'NaN':
				Function.objects.get(id=i).delete()
		msg = '删除成功'
	except:
		code = 1
		msg = "删除失败[%s]" % traceback.format_exc()
	
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def editfunc(request):
	id_ = request.POST.get('id')
	code = 0
	msg = ''
	try:
		func = Function.objects.get(id=id_)
		func.description = request.POST.get('description')
		func.name = Fu.getfuncname(request.POST.get('body'))[0]
		func.body = base64.b64encode(request.POST.get('body').encode('utf-8')).decode()
		func.flag = Fu.tzm_compute(request.POST.get('body'), "def\s+(.*?)\((.*?)\):")
		
		func.save()
		msg = '编辑成功'
	except:
		code = 1
		logger.info(traceback.format_exc())
		msg = "编辑失败[%s]" % traceback.format_exc()
	
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def addfunc(request):
	code = 0
	msg = ''
	try:
		f = Function()
		f.description = request.POST.get("description")
		# base64 str 存储
		tbody = request.POST.get("body")
		f.name = Fu.getfuncname(tbody)[0]
		f.body = base64.b64encode(tbody.encode('utf-8')).decode()
		f.flag = Fu.tzm_compute(tbody, "def\s+(.*?)\((.*?)\):")
		f.save()
		msg = '添加成功'
	except Exception as e:
		logger.info(e)
		code = 1
		msg = '添加失败'
	# traceback.logger.info_exc(e)
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def updatefunc(request):
	return JsonResponse(simplejson(code=Fu.load_data(), msg=""), safe=False)


@csrf_exempt
def queryfunclist(request):
	code, msg = 0, ''
	res = []
	try:
		res = list(Function.objects.all())
		
		res = res + getbuiltin()
		data = list()
		for x in res:
			op = {}
			op['value'] = x.name
			op['description'] = ("%s -> %s" % (x.name, x.description)).replace('\n', ' ').replace('\t', '')
			data.append(op)
		
		logger.info('查函数下拉信息=>', data)
		
		return JsonResponse(simplejson(code=0, msg='操作成功', data=data), safe=False)
	
	except:
		logger.info(traceback.format_exc())
		code = 4
		msg = '查询函数下拉框信息异常'
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


"""
测试步骤相关
"""


@csrf_exempt
def queryonestep(request):
	code, msg = (0, '查询成功')
	urid = request.POST.get('id').split('_')[1]
	step = None
	try:
		step = Step.objects.values().get(id=urid)
	except:
		logger.info(traceback.format_exc())
		code, msg = (1, '查询失败%s' % traceback.format_exc())
	return JsonResponse({'code': code, 'msg': msg, 'data': step})


# 查询计划邮件配置
@csrf_exempt
def queryonemailconfig(request):
	try:
		id_ = request.POST.get('id')
		plan = Plan.objects.get(id=id_)
		mail_config_id = plan.mail_config_id
		
		logger.info('获取计划[%s]邮件配置=>%s' % (plan.description, mail_config_id))
		
		if mail_config_id:
			config = MailConfig.objects.get(id=mail_config_id)
			jsonstr = json.dumps(config, cls=MailConfigEncoder)
			return JsonResponse(jsonstr, safe=True)
		else:
			jsonstr = json.dumps('', cls=MailConfigEncoder)
			return JsonResponse(jsonstr, safe=True)
	# return JsonResponse(simplejson(code=1,msg='计划[%s]还未关联邮件'%plan.description),safe=False)
	except:
		logger.info(traceback.format_exc())
		return JsonResponse(simplejson(code=2, msg='查询异常[%s]' % traceback.format_exc()), safe=False)


@csrf_exempt
def editmailconfig(request):
	code = 0
	msg = ''
	try:
		id_ = request.POST.get('id')
		plan = Plan.objects.get(id=id_)
		mail_config_id = plan.mail_config_id
		
		to_receive = request.POST.get('to_receive') if request.POST.get('to_receive') is not None else ''
		description = request.POST.get('description') if request.POST.get('description') is not None else ''
		rich_text = request.POST.get('rich_text') if request.POST.get('rich_text') is not None else ''
		color_scheme = request.POST.get('color_scheme') if request.POST.get('color_scheme') is not None else 'red'
		dingdingtoken = request.POST.get('dingdingtoken') if request.POST.get('dingdingtoken') is not None else ''
		if mail_config_id:
			config = MailConfig.objects.get(id=mail_config_id)
			config.to_receive = to_receive
			config.color_scheme = color_scheme
			config.description = description
			config.dingdingtoken = dingdingtoken
			config.rich_text = rich_text
			config.save()
			msg = '编辑成功'
		else:
			config = MailConfig()
			config.to_receive = to_receive
			config.color_scheme = color_scheme
			config.description = description
			config.dingdingtoken = dingdingtoken
			config.rich_text = rich_text
			config.save()
			plan.mail_config_id = config.id
			plan.save()
			msg = '新建成功'
	
	except:
		logger.info(traceback.format_exc())
		code = 1
		msg = '操作异常[%s]' % traceback.format_exc()
	
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def queryoneproduct(request):
	code = 0
	msg = ''
	res = None
	try:
		res = Product.objects.get(id=request.POST.get('id').split('_')[1])
		logger.info('product=>', res)
	
	except:
		code = 1
		msg = '查询异常[%s]' % traceback.format_exc()
	finally:
		jsonstr = json.dumps(res, cls=ProductEncoder)
		return JsonResponse(jsonstr, safe=False)


@csrf_exempt
def treecontrol(request):
	def _add_link_task(request):
		cm.addeditlink(request)
	
	action = request.GET.get('action') or request.POST.get('action', '')
	asyn = request.GET.get('asyn') or request.POST.get('asyn', '')
	logger.info('action:', action)
	if action in ('loadpage', 'view'):
		page = request.GET.get('page') or request.POST.get('page')
		# logger.info('loadpage')
		try:
			return render(request, "cm/%s.html" % page)
		except:
			logger.info(traceback.format_exc())
			return JsonResponse(pkg(code=4, msg='%s' % traceback.format_exc()), safe=False)
	
	else:
		
		callstr = "cm.%s(request)" % (request.POST.get('action') or request.GET.get('action'))
		status = v = None
		try:
			# logger.info('callstr=>',callstr)
			if not asyn:
				k = eval(callstr)
				# logger.info('k=>', k)
				status, v, data = k.get('status'), k.get('msg'), k.get('data')
				
				if status is not 'success':
					return JsonResponse(pkg(code=2, msg=str(v)), safe=False)
				else:
					
					if action == 'export':
						logger.info('export %s' % v)
						flag = str(datetime.datetime.now()).split('.')[0]
						response = HttpResponse(str(v))
						response['content-type'] = 'application/json'
						response['Content-Disposition'] = 'attachment;filename=plan.ME2'
						return response
					
					return JsonResponse(pkg(code=0, msg=str(v), data=data), safe=False)
			else:
				threading.Thread(target=_add_link_task, args=(request,)).start()
				return JsonResponse(pkg(code=0, msg='你已完成提交 请稍等片刻'), safe=False)
		
		except:
			logger.info(traceback.format_exc())
			return JsonResponse(pkg(code=4, msg='%s' % traceback.format_exc()), safe=False)


"""
录制操作
"""


def record(request):
	response = render(request, 'manager/record.html', locals())
	return response


def stoprecord(request):
	return JsonResponse({}, safe=False)


@csrf_exempt
def getusernews(request):
	userid = User.objects.get(name=request.session.get('username')).id
	return JsonResponse(News.get_user_news(userid), safe=False)


@csrf_exempt
def getusernewsflagstatus(request):
	userid = User.objects.get(name=request.session.get('username')).id
	return JsonResponse(News.has_no_read_msg(userid), safe=False)


@csrf_exempt
def hasread(request):
	uid = request.POST.get('uid')
	try:
		n = News.objects.get(id=uid)
		n.is_read = 1
		n.save()
		logger.error('标位已读 消息ID:', uid)
		return JsonResponse(pkg(code=0, msg=''), safe=False)
	
	except:
		logger.error('标位已读异常:', traceback.format_exc())
		return JsonResponse(pkg(code=4, msg=''), safe=False)


@csrf_exempt
def queryonebusiness(request):
	code, msg = (0, '')
	id = request.POST.get('vid').split('_')[1]
	try:
		sql = '''SELECT id,count,businessname,params as body,preposition,postposition,description,timeout,queryparams as params ,bodytype,
        CONCAT_WS('|',itf_check,db_check) as dataCheck FROM manager_businessdata where id =%s and isdelete=0'''
		with connection.cursor() as cursor:
			cursor.execute(sql, [id])
			row = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()][0]
			row['timeout'] = 60 if row['timeout'] is None else row['timeout']
		return JsonResponse({'code': 0, 'data': row})
	# return JsonResponse(jsonstr, safe=False)
	except:
		code = 4
		msg = '查询异常[%s]' % traceback.format_exc()
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


def querytreelist(request):
	from .cm import getchild, get_search_match, get_link_left_tree, get_link_right_tree
	datanode = []
	
	def _get_pid_data(idx, type, data, srcid=None, checkflag=None, flag=None):
		
		if type == 'product':
			plans = cm.getchild('product_plan', idx)
			for plan in plans:
				data.append({
					'id': 'plan_%s' % plan.id,
					'pId': 'product_%s' % idx,
					'name': plan.description,
					'type': 'plan',
					'textIcon': 'fa icon-fa-product-hunt',
				})
				
				if flag == '1':
					is_exits = EditLink.objects.filter(snid=srcid, tnid='plan_%s' % plan.id).exists()
					if is_exits:
						data[-1]['checked'] = True
				elif flag == '0':
					if str(plan.id) == srcid.split('_')[1]:
						data[-1]['checked'] = True
			
			return data
		
		elif type == 'plan':
			cases = cm.getchild('plan_case', idx)
			logger.info('cases=>', cases)
			for case in cases:
				logger.info('case=>', case)
				casename = case.description
				if case.count in (0, '0'):
					casename = '<s>%s</s>' % casename
				data.append({
					'id': 'case_%s' % case.id,
					'pId': 'plan_%s' % idx,
					'name': casename,
					'type': 'case',
					'textIcon': 'fa icon-fa-folder',
				})
				
				if flag == '1':
					ex = EditLink.objects.filter(tnid='case_{}'.format(case.id))
					for o in ex:
						bname2 = Case.objects.get(id=o.snid.split('_')[1]).description
						if casename == bname2:
							data[-1]['checked'] = True
							break;
				elif flag == '0':
					ex = EditLink.objects.filter(snid='case_%s' % case.id)
					if ex.exists():
						data[-1]['checked'] = True
			
			return data
		
		elif type == 'case':
			# orders = Order.objects.filter(kind__contains='case_', main_id=idx,isdelete=0).extra(
			# select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
			orders = list(Order.objects.filter(kind__contains='case_', main_id=idx, isdelete=0))
			print("aaaaaaaaaaa", orders, idx)
			orders.sort(key=lambda a: int(a.value.split('.')[1]))
			
			for order in orders:
				obj = None
				try:
					
					nodekind = order.kind.split('_')[1]
					nodeid = order.follow_id
					obj = eval("%s.objects.values('description','count').get(id=%s)" % (nodekind.capitalize(), nodeid))
					name = '<s>%s</s>' % obj['description'] if obj['count'] in (0, '0') else obj['description']
					textIcon = 'fa icon-fa-file-o' if nodekind == 'step' else 'fa icon-fa-folder'
					data.append({
						'id': '%s_%s' % (nodekind, nodeid),
						'pId': 'case_%s' % idx,
						'name': name,
						'type': nodekind,
						'textIcon': textIcon,
					})
				except:
					pass
				
				if flag == '1':
					
					if nodekind == 'step':
						ex = EditLink.objects.filter(tnid='step_{}'.format(nodeid))
						for o in ex:
							bname2 = Step.objects.get(id=o.snid.split('_')[1]).description
							if obj['description'] == bname2:
								data[-1]['checked'] = True
								break;
					elif nodekind == 'case':
						ex = EditLink.objects.filter(tnid='case_{}'.format(nodeid))
						for o in ex:
							bname2 = Case.objects.get(id=o.snid.split('_')[1]).description
							if obj['description'] == bname2:
								data[-1]['checked'] = True
								break;
				elif flag == '0':
					if nodekind == 'step':
						ex = EditLink.objects.filter(snid='%s_%s' % (nodekind, nodeid))
						if ex.exists():
							data[-1]['checked'] = True
					elif nodekind == 'case':
						ex = EditLink.objects.filter(snid='%s_%s' % (nodekind, nodeid))
						if ex.exists():
							data[-1]['checked'] = True
			
			return data
		
		elif type == 'step':
			businesslist = cm.getchild('step_business', idx)
			
			for business in businesslist:
				bname = business.businessname
				
				if business.count in (0, '0'):
					bname = '<s>%s</s>' % bname
				
				data.append({
					'id': 'business_%s' % business.id,
					'pId': 'step_%s' % idx,
					'name': bname,
					'type': 'business',
					'textIcon': 'fa icon-fa-leaf',
				})
				if flag == '1':
					##这里有有个场景暂时不考虑
					ex = EditLink.objects.filter(tnid='business_{}'.format(business.id))
					for o in ex:
						bname2 = BusinessData.objects.get(id=o.snid.split('_')[1]).businessname
						if bname == bname2:
							data[-1]['checked'] = True
							break;
				elif flag == '0':
					ex = EditLink.objects.filter(snid='business_%s' % business.id)
					if ex.exists():
						data[-1]['checked'] = True
			
			return data
		else:
			return data
	
	id_ = request.POST.get('id')
	if id_:
		id_ = id_.split('_')[1]
	
	type_ = request.POST.get('type')
	callername = request.session.get('username')
	searchvalue = request.POST.get('searchvalue')
	
	nid = request.POST.get('srcid') or request.GET.get('srcid')
	flag = request.POST.get('flag') or request.GET.get('flag')
	checkflag = get_params(request).get('checkflag')
	
	if id_:
		datanode = _get_pid_data(id_, type_, datanode, srcid=nid, checkflag=checkflag, flag=flag)
		print("aaaaaaaaaaa", datanode)
		if get_params(request).get('flag') == '1':
			for node in datanode:
				if node['id'] == get_params(request).get('srcid'):
					datanode.remove(node)
		
		elif get_params(request).get('flag') == '0':
			nodecopy = copy.deepcopy(datanode)
			
			for node in datanode:
				if node['type'] == 'plan' and node['id'] != get_params(request).get('srcid'):
					nodecopy.remove(node)
			# logger.info('移除计划节点:{}'.format(node['name']))
			
			# logger.info('移除操作后 大小:{}'.format(len(nodecopy)))
			
			datanode = nodecopy
	
	elif searchvalue:
		datanode = get_search_match(searchvalue)
	
	elif nid:
		if flag == '0':
			datanode = get_link_left_tree(nid)
		elif flag == '1':
			datanode = get_link_right_tree(nid)
	
	else:
		datanode.append({'id': -1, 'name': '产品池', 'type': 'root', 'textIcon': 'fa fa-pinterest-p33', 'open': True})
		productlist = list(Product.objects.exclude(isdelete=1))
		# logger.info('productlist:',productlist)
		for product in productlist:
			datanode.append({
				'id': 'product_%s' % product.id,
				'pId': -1,
				'name': product.description,
				'type': 'product',
				'textIcon': 'fa icon-fa-home'
			})
	
	logger.info('tree查询返回节点大小:{}'.format(len(datanode)))
	
	return JsonResponse(simplejson(code=0, data=datanode), safe=False)


@csrf_exempt
def querytaglist(request):
	namelist = []
	userid = request.POST.get('userid')
	data = []
	try:
		with connection.cursor() as cursor:
			if userid != '-1':
				userid = userid if userid != '0' else str(
					User.objects.values('id').get(name=request.session.get('username'))['id'])
				sql = "SELECT customize FROM manager_variable v,manager_tag t where author_id=%s and t.var_id=v.id"
				cursor.execute(sql, [userid])
			elif userid == '-1':
				sql = "SELECT customize from manager_tag "
				cursor.execute(sql)
			rows = cursor.fetchall()
		for i in rows:
			m = list(i)[0].split(';')[:-1]
			for x in m:
				if x not in namelist:
					namelist.append(x)
		logger.info('tag列表：', namelist)
		data = [{'id': '0', 'name': '全部标记'}]
		for m, n in enumerate(namelist):
			data.append({'id': str(m + 1) + '_' + n, 'name': n})
	except:
		logger.info(traceback.format_exc())
		logger.info('==获取标签列表异常')
	finally:
		return JsonResponse(pkg(code=0, data=data))


@csrf_exempt
def querytags(request):
	data = []
	s = time.time()
	with connection.cursor() as cursor:
		sql = "SELECT customize from manager_tag "
		cursor.execute(sql)
		rows = cursor.fetchall()
	for row in rows:
		m = list(row)[0].split(';')[:-1]
		for x in m:
			if x not in data:
				data.append(x)
	logger.info('tag列表：', data)
	return JsonResponse({'code': 0, 'data': data})


@csrf_exempt
def querytag(request):
	# 查询tag最近一次更新，避免重复填写
	userid = str(User.objects.values('id').get(name=request.session.get('username'))['id'])
	try:
		varhis = list(Variable.objects.values('tag').filter(author_id=userid).order_by('-updatetime')[0:1])[0]
		code = 0
	except:
		code, data = 1, '出错了！'
	return JsonResponse({'code': 0, 'data': varhis['tag'].split(';')[:-1]})


def queryVarSpace(request):
	spaceList = [{"id": 0, "name": "全局", "planid": 0}]
	spaces = Varspace.objects.values().all()
	spaceList.extend(list(spaces))
	return JsonResponse({'code': 0, 'data': spaceList})


'''
报文模板
'''


@csrf_exempt
def querytemplatecommon(request):
	p = MessageParser.query_template_common(request.POST.get('tid'))
	return JsonResponse(p, safe=False)


@csrf_exempt
def querytemplatelist(request):
	return JsonResponse(MessageParser.query_template_name_list(), safe=False)


@csrf_exempt
def addtemplate(request):
	pa = get_params(request)
	p = MessageParser.add_template(**pa)
	return JsonResponse(p, safe=False)


@csrf_exempt
def deltemplate(request):
	return JsonResponse(MessageParser.del_template(request.POST.get('ids')), safe=False)


@csrf_exempt
def edittemplate(request):
	return JsonResponse(MessageParser.edit_template(**get_params(request)), safe=False)


@csrf_exempt
def querytemplate(request):
	searchvalue = request.GET.get('searchvalue')
	logger.info("searchvalue=>", searchvalue)
	
	if searchvalue:
		logger.info("变量查询条件=>")
		res = list(Template.objects.filter(name__icontains=searchvalue))
	else:
		res = list(Template.objects.all())
	
	limit = request.GET.get('limit')
	page = request.GET.get('page')
	# logger.info("res old size=>",len(res))
	res, total = getpagedata(res, page, limit)
	jsonstr = json.dumps(res, cls=TemplateEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)


def templatefield(request):
	tid = request.GET.get('tid')
	kind = Template.objects.get(id=tid).kind
	is_sort_display = '' if kind != 'length' else 'none'
	is_start_display = '' if kind == 'length' else 'none'
	show_index = 'false' if kind != 'length' else 'true'
	
	return render(request, 'manager/templatefield.html', locals())


@csrf_exempt
def querytemplatefield(request):
	return JsonResponse(MessageParser.query_template_field(**get_params(request)), safe=False)


@csrf_exempt
def addtemplatefield(request):
	return JsonResponse(MessageParser.add_field(**get_params(request)), safe=False)


@csrf_exempt
def deltemplatefield(request):
	return JsonResponse(MessageParser.del_field(request.POST.get('ids')), safe=False)


@csrf_exempt
def edittemplatefield(request):
	return JsonResponse(MessageParser.edit_field(**get_params(request)), safe=False)


@csrf_exempt
def queryfielddetail(request):
	return JsonResponse(MessageParser.query_field_detail(request.POST.get('tid')), safe=False)


# 变量页面查询用户
@csrf_exempt
def queryUser(request):
	name = request.session.get('username')
	user = list(User.objects.values('id', 'name').exclude(name__in=[name, "定时任务", "system"]))
	return JsonResponse({'data': user})


@csrf_exempt
def queryDbScheme(request):
	action = request.POST.get('action')
	sql = "SELECT distinct scheme as 'value',scheme as 'label' FROM `manager_dbcon` where scheme not in ('全局','')"
	with connection.cursor() as cursor:
		cursor.execute(sql)
		desc = cursor.description
		rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
	if action == '1':
		data = [{
			'value': '全局',
			'label': '全局'
		}]
	else:
		data = [{
			'value': '',
			'label': '全部'
		}, {
			'value': '全局',
			'label': '全局'
		}]
	for row in rows:
		data.append(row)
	return JsonResponse({'code': 0, 'data': data})


@csrf_exempt
def queryDbSchemebyVar(request):
	code = 0
	msg = ''
	dbs = list((DBCon.objects.values('scheme').filter(description=request.POST.get('db'))))
	try:
		planbinds = json.loads(
			Tag.objects.values('planids').get(var=Variable.objects.get(id=request.POST.get('id'))).get('planids'))
		plans = []
		for i in planbinds:
			plans.append({'label': i, 'value': '"%s":%s' % (i, json.dumps(planbinds[i]).replace(' ', ''))})
		if not plans:
			plans.append({'label': '全局', 'value': '{}'})
	except:
		print(traceback.format_exc())
		code = 1
		msg = '这个变量可能有些问题'
		planbinds = {}
	if len(dbs) == 0:
		code = 1
		msg = '@的库名没有在任何方案下找到'
	return JsonResponse({'code': code, 'msg': msg, 'data': dbs, 'plans': plans})


'''
个人空间管理
'''


@csrf_exempt
def querywinrm(request):
	m = []
	data = DBCon.objects.values('id', 'host', 'description').filter(kind="WinRM")
	for i in data:
		m.append({'id': str(i['id']), 'description': i['description']})
	return JsonResponse({'code': 0, 'data': m})


def _formatSize(bytes):
	try:
		bytes = float(bytes)
		kb = bytes / 1024
	except:
		logger.info("传入的字节格式不对")
		return "Error"
	
	if kb >= 1024:
		M = kb / 1024
		if M >= 1024:
			G = M / 1024
			return "%.2fG" % (G)
		else:
			return "%.2fM" % (M)
	else:
		return "%.2fkb" % (kb)


def getFileFolderSize(fileOrFolderPath):
	totalSize = 0
	if not os.path.exists(fileOrFolderPath):
		return totalSize
	if os.path.isfile(fileOrFolderPath):
		totalSize = os.path.getsize(fileOrFolderPath)
		return totalSize
	if os.path.isdir(fileOrFolderPath):
		with os.scandir(fileOrFolderPath) as dirEntryList:
			for curSubEntry in dirEntryList:
				curSubEntryFullPath = os.path.join(fileOrFolderPath, curSubEntry.name)
				if curSubEntry.is_dir():
					curSubFolderSize = getFileFolderSize(curSubEntryFullPath)
					totalSize += curSubFolderSize
				elif curSubEntry.is_file():
					curSubFileSize = os.path.getsize(curSubEntryFullPath)  # 1891
					totalSize += curSubFileSize
			return totalSize


@csrf_exempt
def queryspacemenu(request):
	basedir = get_space_dir()
	if not os.path.exists(os.path.join(basedir, '默认')):
		os.makedirs(os.path.join(basedir, '默认'))
	files = os.listdir(basedir)
	menu = []
	for file in files:
		path = os.path.join(basedir, file)
		if os.path.isdir(path):
			menu.append({'menuname': file, 'path': path,
			             'createtime': time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getctime(path)))})
	menu.sort(key=lambda e: e.get('createtime'), reverse=True)
	return JsonResponse({'code': 0, 'data': menu})


@csrf_exempt
def queryspacefiles(request):
	menuname = request.POST.get('menuname')
	basedir = os.path.join(get_space_dir(), menuname)
	files = os.listdir(basedir)
	filename = []
	for file in files:
		path = os.path.join(basedir, file)
		if os.path.isfile(path):
			try:
				FileMap.objects.get(path=menuname + '/' + file)
			except:
				print(traceback.format_exc())
				size = getFileFolderSize(path)
				if size / 1024 / 1024 > 5:
					FileMap(filename=file, path=menuname + '/' + file, customname=file, code="big").save()
				elif size == 0:
					FileMap(filename=file, path=menuname + '/' + file, customname=file, code="blank").save()
				else:
					with open(path, 'rb') as f:
						data = f.read()
						FileMap(filename=file, path=menuname + '/' + file, customname=file,
						        code=chardet.detect(data).get('encoding')).save()
			filename.append({'filename': file, 'menu': menuname, 'path': path,
			                 'customname': FileMap.objects.get(path=menuname + '/' + file).customname,
			                 'createtime': time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getctime(path)))})
	filename.sort(key=lambda e: e.get('createtime'), reverse=True)
	return JsonResponse({'code': 0, 'data': filename})


@csrf_exempt
def getfiledetail(request):
	filename = request.POST.get('filename')
	menu = request.POST.get('menu')
	path = os.path.join(get_space_dir(), menu, filename)
	filedata = ''
	code = 1
	filemap = FileMap.objects.values('customname', 'code', 'targetpath', 'targetserver').get(filename=filename,
	                                                                                         path=menu + "/" + filename)
	if filemap['code'] in [None, 'big', 'blank']:
		if getFileFolderSize(path) == 0:
			return JsonResponse({'code': 0, 'filedata': '', "fileinfo": filemap})
		return JsonResponse({'code': code, "fileinfo": filemap})
	else:
		try:
			with open(path, 'r', encoding=filemap['code'])as file:  # 使用得到的文件编码格式打开文件
				filedata = file.read()
				code = 0
		except:
			return JsonResponse({'code': code, "fileinfo": filemap})
	return JsonResponse({'code': code, 'filedata': filedata, "fileinfo": filemap})


@csrf_exempt
def addmenu(request):
	name = request.POST.get('name')
	path = os.path.join(get_space_dir(), name)
	if os.path.exists(path):
		return JsonResponse({'code': 1, 'info': '已存在相同名称文件夹'})
	else:
		os.mkdir(path)
		return JsonResponse({'code': 0, 'info': '创建成功'})


@csrf_exempt
def downloadfile(request):
	filepath = request.POST.get('path')
	downloadname = request.POST.get('name')
	with open(filepath, 'rb') as f:
		response = HttpResponse(f)
		response['Content-Type'] = 'application/octet-stream'
		response["Content-Disposition"] = "attachment; filename*=UTF-8''{}".format(escape_uri_path(downloadname))
		return response


@csrf_exempt
def editpathname(request):
	newname = request.POST.get('newname')
	newpath = os.path.join(get_space_dir(), newname)
	path = request.POST.get('path')
	code, info = 0, "修改成功"
	try:
		os.rename(path, newpath)
	except Exception as e:
		code = 1
		info = re.findall(", '(.*?)'\)", repr(e))[0]
		print(re.findall(", '(.*?)'\)", repr(e))[0])
	return JsonResponse({'code': code, 'info': info})


@csrf_exempt
def editfile(request):
	code, info = 0, '修改成功'
	try:
		path = request.POST.get('path')
		file = FileMap.objects.get(path=path)
		oldfilename = file.filename
		newfilename = request.POST.get('filename')
		newpath = path.replace(oldfilename, newfilename)
		if request.POST.get('content') is not None:
			with open(os.path.join(get_space_dir(), path), 'wb') as f:
				f.write(request.POST.get('content').encode('UTF-8'))
		os.rename(os.path.join(get_space_dir(), path), os.path.join(get_space_dir(), newpath))
		file.filename = newfilename
		file.customname = request.POST.get('customname')
		file.targetpath = request.POST.get('targetpath')
		file.targetserver = request.POST.get('targetserver')
		file.path = newpath
		file.code = 'utf-8'
		file.save()
	except:
		print(traceback.format_exc())
		code = 1
		info = traceback.format_exc()
	
	return JsonResponse({'code': code, 'info': info})


@csrf_exempt
def delfile(request):
	path = request.POST.get('path')
	code, info = 0, '删除成功'
	try:
		if os.path.isdir(path):
			if len(os.listdir(path)) == 0:
				os.rmdir(path)
			else:
				info = '文件夹下存在文件'
		elif os.path.isfile(path):
			FileMap.objects.get(path=request.POST.get('shortpath')).delete()
			os.remove(path)
	
	except Exception as e:
		code = 1
		info = re.findall(", '(.*?)'\)", repr(e))[0]
		print(re.findall(", '(.*?)'\)", repr(e))[0])
	return JsonResponse({'code': code, 'info': info})


'''
MOCK替换测试
'''


@csrf_exempt
def simpletest(request):
	nodeid = request.GET.get('nodeid')
	is_mock_open = Step.objects.get(id=nodeid.split('_')[1]).is_mock_open
	if is_mock_open is None:
		is_mock_open = 0
	return render(request, 'manager/simpletest.html', locals())


@csrf_exempt
def querysimpletest(request):
	node_id = request.GET.get('nodeid')
	return JsonResponse(TestMind().query_simple_test(node_id), safe=False)


@csrf_exempt
def updatesimpletest(request):
	return JsonResponse(TestMind().update_simple_test(**get_params(request)), safe=False)


@csrf_exempt
def opensimpletest(request):
	return JsonResponse(TestMind().open_simple_test(request.POST.get('tid'), request.POST.get('checked')), safe=False)


@csrf_exempt
def openstepmock(request):
	return JsonResponse(TestMind().open_step_mock(request.POST.get('tid'), request.POST.get('checked')), safe=False)


@csrf_exempt
def querysteptype(request):
	code, msg = 0, ''
	kind = Step.objects.get(id=request.GET.get('sid').split('_')[1]).step_type
	content_type = Step.objects.get(id=request.GET.get('sid').split('_')[1]).content_type
	
	logger.info('kind:', kind)
	if kind == 'function':
		return JsonResponse({'code': 1, 'msg': '函数暂不支持'}, safe=False)
	elif content_type == 'xml':
		return JsonResponse({'code': 1, 'msg': 'xml暂不支持'}, safe=False)
	else:
		childs = getchild('step_business', request.GET.get('sid').split('_')[1])
		if len(childs) == 0:
			return JsonResponse({'code': 1, 'msg': '此功能需要至少挂一个带参数的测试点'}, safe=False)
		else:
			params = ''
			for c in childs:
				params = params + c.params
			params = params.replace('{', '').replace('}', '').replace('\s+', '')
			if not params.strip():
				return JsonResponse({'code': 1, 'msg': '此功能需要至少挂一个带参数的测试点'}, safe=False)
	
	return JsonResponse({
		'code': code,
		'msg': msg}, safe=False)


@csrf_exempt
def regentest(request):
	TestMind().gen_simple_test_cases(request.POST.get('uid'))
	return JsonResponse(pkg(code=0, msg=''), safe=False)


@csrf_exempt
def queryrecyclelist(request):
	qtype = request.POST.get('type')
	qid = request.POST.get('nid')
	kind = request.POST.get('kind')
	isdelete = [0, 1] if kind == 'old' else [0]
	datanode = []
	if qtype == 'root':
		productlist = list(Product.objects.filter(isdelete__in=isdelete))
		print(productlist)
		for product in productlist:
			datanode.append({'id': product.createtime, 'nid': product.id, 'name': product.description,
			                 'type': 'product', 'icon': 'fa icon-fa-home',
			                 'hasChildren': True, 'isdelete': product.isdelete})
	elif qtype == 'product':
		orders = Order.objects.filter(kind='product_plan', main_id=qid, isdelete__in=isdelete).extra(
			select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
		for order in orders:
			try:
				plan = Plan.objects.get(id=order.follow_id)
				datanode.append({'id': plan.createtime, 'nid': plan.id, 'name': plan.description,
				                 'type': 'plan', 'icon': 'fa icon-fa-product-hunt',
				                 'hasChildren': True, 'isdelete': plan.isdelete})
			except:
				pass
	elif qtype == 'plan':
		orders = Order.objects.filter(kind='plan_case', main_id=qid, isdelete__in=isdelete).extra(
			select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
		for order in orders:
			try:
				case = Case.objects.get(id=order.follow_id)
				datanode.append({
					'id': case.createtime,
					'nid': case.id,
					'name': case.description,
					'type': 'case',
					'icon': 'fa icon-fa-folder',
					'hasChildren': True,
					'isdelete': case.isdelete
				})
			except:
				pass
	elif qtype == 'case':
		orders = Order.objects.filter(kind__contains='case_', main_id=qid, isdelete__in=isdelete).extra(
			select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
		for order in orders:
			try:
				nodekind = order.kind.split('_')[1]
				nodeid = order.follow_id
				name = eval("%s.objects.values('description','createtime','isdelete').get(id=%s)" % (
					nodekind.capitalize(), nodeid))
				textIcon = 'fa icon-fa-file-o' if nodekind == 'step' else 'fa icon-fa-folder'
				datanode.append({
					'id': name['createtime'],
					'nid': nodeid,
					'name': name['description'],
					'type': nodekind,
					'icon': textIcon,
					'hasChildren': True,
					'isdelete': name['isdelete']
				})
			except:
				pass
	elif qtype == 'step':
		orders = Order.objects.filter(kind='step_business', main_id=qid, isdelete__in=isdelete).extra(
			select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
		for order in orders:
			try:
				businessdata = BusinessData.objects.get(id=order.follow_id)
				datanode.append({
					'id': businessdata.businessname + str(businessdata.id),
					'nid': businessdata.id,
					'name': businessdata.businessname,
					'type': 'businessdata',
					'icon': 'fa icon-fa-leaf',
					'hasChildren': False,
					'isdelete': businessdata.isdelete
				})
			except:
				print(traceback.format_exc())
	return JsonResponse({'code': 0, 'data': datanode})


@csrf_exempt
def recyclenode(request):
	type = request.POST.get('type')
	id = request.POST.get('id')
	porder = Order.objects.get(kind__contains='_%s' % type.replace("data", ''), follow_id=id)
	pkind = porder.kind.split("_")[0]
	pid = porder.main_id
	if eval('%s.objects.get(id=%s)' % (pkind.capitalize(), pid)).isdelete == 1:
		return JsonResponse({'code': 1, 'data': '请先还原上级节点'})
	maxv = list(
		Order.objects.values_list('value', flat=True).filter(isdelete=0, kind__contains='%s_' % pkind, main_id=pid))
	li = [int(i.split(".")[1]) for i in maxv] if maxv else [0]
	orderobj = Order.objects.get(kind__contains='_%s' % type.replace('data', ''), follow_id=id)
	orderobj.value = '1.' + str(max(li) + 1)
	orderobj.save()
	print(orderobj.value)
	recyclenodes(type, id)
	return JsonResponse({'code': 0, 'data': '操作成功', 'pkind': pkind, 'pid': pid})


def recyclenodes(type, id):
	type = 'businessData' if type in ['business', 'businessdata'] else type
	try:
		print(type, id)
		orderobj = Order.objects.get(kind__contains='_%s' % type.replace('Data', ''), follow_id=id)
		orderobj.isdelete = 0
		orderobj.save()
		nodeobj = eval("%s.objects.get(id=%s)" % (type.title().replace('data', 'Data'), id))
		nodeobj.isdelete = 0
		nodeobj.save()
		orders = Order.objects.filter(kind__contains='%s_' % type.replace('Data', ''), main_id=id)
		for o in orders:
			recyclenodes(o.kind.split("_")[1], o.follow_id)
	
	except:
		print(traceback.format_exc())


@csrf_exempt
def getStepKind(request):
	id = request.POST.get('id')
	step = Step.objects.filter(id=id).first()
	shuldJudge = False
	uptime = int(time.mktime(step.updatetime.timetuple()))
	if step.step_type == 'interface' and step.content_type == 'xml' and uptime < 1600845096 and not step.url.__contains__(
			"http"):
		shuldJudge = True
	
	return JsonResponse({'code': 0, 'data': '操作成功', 'type': step.step_type, 'shuldJudge': shuldJudge})


def editStepKind(request):
	id = request.POST.get('id')
	step_type = request.POST.get('step_type')
	step = Step.objects.get(id=id)
	step.step_type = step_type
	if step_type == 'interface':
		step.content_type = 'application/xml'
	else:
		step.content_type = ''
	step.save()
	return JsonResponse({'code': 0, 'data': '操作成功'})


def getTree(request):
	# 给外部用，获取用例节点数据
	type = request.GET.get('type')
	id = request.GET.get('id')
	data = []
	if type == 'root':
		sql = "SELECT id,description as label,'product' as type,true as disabled from manager_product where isdelete=0"
	elif type == 'product':
		sql = """SELECT p.id,p.description as label,'plan' as type FROM manager_plan p ,manager_order o
        where  o.main_id=%s and o.follow_id=p.id and o.kind='product_plan'
        and o.isdelete=0 and p.isdelete=0 ORDER BY cast(SUBSTR(o.value,3) as DECIMAL(9,5))""" % id
	elif type == 'plan':
		sql = """ SELECT c.id,c.description as label,'case' as type FROM manager_case c ,manager_order o
        where  o.main_id=%s and o.follow_id=c.id and o.kind='plan_case' and o.isdelete=0
        and c.isdelete=0 ORDER BY cast(SUBSTR(o.value,3) as DECIMAL(9,5))""" % id
	elif type == 'case':
		sql = """ SELECT c.id,c.description as label,'case' as type FROM manager_case c ,manager_order o
        where  o.main_id=%s and o.follow_id=c.id and o.kind='case_case' and o.isdelete=0
        and c.isdelete=0 ORDER BY cast(SUBSTR(o.value,3) as DECIMAL(9,5))
        """ % id
	with connection.cursor() as cursor:
		cursor.execute(sql)
		data = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
	
	return JsonResponse({'code': 0, 'data': data})


@csrf_exempt
def recordBuildNodes(request):
	id = request.POST.get('id')
	type = request.POST.get('type')
	text = request.POST.get('text')
	casename = request.POST.get('casename')
	username = request.POST.get('username')
	msg = ''
	try:
		with transaction.atomic():
			case = Case(description=casename, db_id='')
			case.save()
			caseId = case.id
			addrelation('%s_case' % type, id, caseId)
			
			for key, value in json.loads(text).items():
				headers = value.get('headers', {})
				content_type = headers.get('Content-Type', 'application/x-www-form-urlencoded')
				content_type.replace('; charset=UTF-8', '')
				del headers['Content-Type']
				url = value.get('url', '')
				businessName = value.get('测试点名', '')
				method = value.get('method', 'POST')
				body = value.get('body', '')
				response = value.get('response', '')
				
				step = Step(step_type='interface', count=1, description=key,
				            headers=json.dumps(headers, ensure_ascii=False), url=url,
				            method=method,
				            content_type=content_type,
				            temp='',
				            db_id='')
				step.save()
				stepId = step.id
				addrelation('case_step', caseId, stepId)
				
				try:
					if 'urlencoded' in content_type:
						bodytype = 'KeyValue'
						body = parse.urlencode(ast.literal_eval(body))
					elif 'xml' in content_type:
						bodytype = 'xml'
					elif 'json' in content_type:
						body = json.dumps(body, ensure_ascii=False)
						bodytype = 'json'
					else:
						bodytype = 'text'
				except:
					pass
				params = url.split('?')[1] if url.find("?") != -1 else ''
				
				check = []
				if response:
					if isinstance(response, dict):
						for k, v in response.items():
							check.append('%s=%s' % (k, v))
					else:
						check = ['response.text$%s' % response]
				
				check = '|'.join(check)
				for badstr in ['\\n', '\\r', '\n', '<br>']:
					check = check.replace(badstr, '')
				check = check.replace('null', "'None'").replace('true', "'True'").replace("false", "'False'")
				
				bus = BusinessData(businessname=businessName, itf_check=check, queryparams=params, params=body,
				                   bodytype=bodytype,
				                   db_check='', preposition='', postposition='', parser_id='', parser_check='',
				                   timeout=30, count=1, description='')
				
				bus.save()
				addrelation('step_business', stepId, bus.id)
	except:
		logger.error("导入失败:%s" % traceback.format_exc())
		msg = traceback.format_exc()
	
	return JsonResponse({'code': 0, 'data': text, 'msg': msg})


@csrf_exempt
def getVars(request):
	vars = Variable.objects.values("key", "description").filter()
	data = []
	for i in vars:
		tmp = {'value': '%s(%s)' % (i['key'], i['description'])}
		if tmp not in data:
			data.append(tmp)
	return JsonResponse({'code': 0, 'data': data, 'msg': ''})
