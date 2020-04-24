import difflib

from django.db import connection
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import HttpResponse, JsonResponse

from django.db.models import Q
from manager.models import *
from manager.db import Mysqloper
from django.conf import settings
from login.models import *
from .cm import addrelation
from .core import *
from .invoker import *
from . import cm
import json, xlrd, base64, traceback

from .invoker import _is_function_call
from .pa import MessageParser
from .ar import Grant,RoleData

from manager.context import Me2Log as logger


# # Create your views here.

@csrf_exempt
def index(request):
	if request.session.get('is_login', None):
		return render(request, 'manager/start.html', locals())
	
	else:
		return redirect("/account/login/")


def help(request):
	me2url=request.get_raw_uri().replace(request.path,'')
	return redirect("%s/static/PDF.js/web/viewer.html?file=%s/static/PDF.js/ME2.pdf" % (me2url, me2url))


# @csrf_exempt
# def testjson(request):
# 	return HttpResponse("{'a':1}")


# @csrf_exempt
# def recvdata(request):
# 	data = request.POST
# 	logger.info(data)
# 	# case=json.loads(jsonstr)
# 	# proxy.Q.push(case)
# 	logger.info('入队列=>')
# 	logger.info(data)
# 	logger.info("*" * 100)


"""
数据迁移
"""


@csrf_exempt
def datamove(request):
	kind = 'datamovein'
	return render(request, 'manager/datamove.html', locals())


@csrf_exempt
def uploadfile(request):
	kind = 'persionfile'
	return render(request, 'manager/myspace.html', locals())


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
		# logger.info('res=>',res)
		
		if res[0] == 'success':
			# logger.info('flag1_1')
			return JsonResponse(simplejson(code=0, msg='excel数据迁移完成 迁移ID=%s' % taskid), safe=False)
		else:
			# logger.info('flag1_2')
			return JsonResponse(simplejson(code=2, msg='excel数据迁移失败[%s] 迁移ID=%s' % (res[1], taskid)), safe=False)
	
	elif kind == 'dataimport':
		d = DataMove()
		productid = request.POST.get('productid').split('_')[1]
		
		res = d.import_plan(productid, filemap.values(), request.session.get('username'))
		if res[0] == 'success':
			return JsonResponse(simplejson(code=0, msg='数据导入完成'), safe=False)
		else:
			return JsonResponse(simplejson(code=2, msg='数据导入失败[%s]' % res[1]), safe=False)
	elif kind == 'personfile':
		status, msg = upload_personal_file(filemap, request.session.get('username'))
		if status is 'success':
			return JsonResponse(simplejson(code=0, msg='文件上传完成'), safe=False)
		else:
			return JsonResponse(simplejson(code=3, msg='文件上传异常'), safe=False)
	else:
		return JsonResponse(simplejson(code=4, msg='kind错误'), safe=False)


def querymovedata(request):
	return JsonResponse(simplejson(code=0, msg=''), safe=False)


def dataimport(request):
	return JsonResponse(simplejson(code=0, msg=''), safe=False)


def dataexport(request):
	flag = str(datetime.datetime.now()).split('.')[0]
	version = request.GET.get('version')
	planid = request.GET.get('planid')
	m = DataMove()
	res = m.export_plan(planid, flag, version=int(version))
	# logger.info('res[0]=>',res[0])
	if res[0] is 'success':
		# logger.info('equals')
		
		response = HttpResponse(str(res[1]))
		response['content-type'] = 'application/json'
		response['Content-Disposition'] = 'attachment;filename=plan_%s.ME2' % flag
		# response.write(str(res[1]))
		# response=FileResponse(res[1],as_attachment=True,filename='plan_%s.json'%flag)
		return response
	else:
		logger.info('导出失败:', res[1])
		return JsonResponse(simplejson(code=2, msg='导出失败[%s]' % res[1]), safe=False)


def datamovnin(request):
	return JsonResponse(simplejson(code=0, msg=''), safe=False)


"""
DB相关
"""


def dbcon(request):
	return render(request, 'manager/db.html')


@csrf_exempt
def testdbcon(request):
	status, msg = db_connect({
		'description': request.POST.get('description'),
		'dbtype': request.POST.get('kind'),
		'dbname': request.POST.get('dbname'),
		'host': request.POST.get('host'),
		'port': request.POST.get('port'),
		'username': request.POST.get('accountname'),
		'password': request.POST.get('password')
		
	})
	if status is 'success':
		return JsonResponse(simplejson(code=0, msg=msg), safe=False)
	
	else:
		return JsonResponse(simplejson(code=4, msg=msg), safe=False)


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


@csrf_exempt
def querydb(request):
	searchvalue = request.GET.get('searchvalue')
	searchvalue = searchvalue if searchvalue not in [None, ''] else ''
	logger.info("searchvalue=>", searchvalue)
	queryschemevalue = request.GET.get('querySchemeValue')
	queryschemevalue = queryschemevalue if queryschemevalue not in [None, ''] else ''
	logger.info("SchemeValue=>", queryschemevalue)
	res = None
	# if searchvalue:
	# 	logger.info("变量查询条件=>")
	# 	res = list(DBCon.objects.filter((Q(description__icontains=searchvalue) | Q(dbname__icontains=searchvalue) | Q(
	# 		host__icontains=searchvalue) | Q(port__icontains=searchvalue) | Q(kind__icontains=searchvalue)) & Q(
	# 		scheme=queryschemevalue)))
	# else:
	# 	res = list(DBCon.objects.filter(Q(scheme__contains=queryschemevalue)))
	#
	res = list(DBCon.objects.filter((Q(description__icontains=searchvalue) | Q(dbname__icontains=searchvalue) | Q(
		host__icontains=searchvalue) | Q(port__icontains=searchvalue) | Q(kind__icontains=searchvalue)) & Q(
		scheme__contains=queryschemevalue)))
	limit = request.GET.get('limit')
	page = request.GET.get('page')
	res, total = getpagedata(res, page, limit)
	
	jsonstr = json.dumps(res, cls=DBEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)


@csrf_exempt
def addcon(request):
	code, msg = 0, ''
	try:
		description = request.POST.get('description')
		kind = request.POST.get('kind')
		dbname = request.POST.get('dbname')
		host = request.POST.get('host')
		port = request.POST.get('port')
		schemevalue = request.POST.get('schemevalue')
		username = request.POST.get('accountname')
		callername = request.session.get('username', None)
		password = request.POST.get('password')
		
		con = DBCon()
		con.kind = kind
		con.dbname = dbname
		con.host = host
		con.port = port
		con.username = username
		con.password = password
		con.description = description
		con.scheme = schemevalue
		con.author = User.objects.get(name=callername)
		con.save()
		msg = '添加成功'
	except:
		logger.info(traceback.format_exc())
		code = 1
		msg = '添加异常'
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def delcon(request):
	id_ = request.POST.get('ids')
	# logger.info('ids=>',id_)
	ids = id_.split(',')
	code = 0
	msg = ''
	try:
		for i in ids:
			DBCon.objects.get(id=i).delete()
		msg = '删除成功'
	except:
		code = 1
		msg = "删除失败[%s]" % traceback.format_exc()
	
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def editcon(request):
	code = 0
	msg = ''
	id_ = request.POST.get('id')
	try:
		logger.info("id=>", id_)
		con = DBCon.objects.get(id=id_)
		con.kind = request.POST.get('kind')
		con.description = request.POST.get('description')
		con.dbname = request.POST.get('dbname')
		con.username = request.POST.get('accountname')
		con.password = request.POST.get('password')
		con.host = request.POST.get('host')
		con.port = request.POST.get('port')
		con.scheme = request.POST.get('schemevalue')
		con.save()
		
		msg = '编辑成功'
	
	except:
		msg = '编辑异常[%s]' % traceback.format_exc()
		logger.error(msg)
		code = 1
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def editmultidbcon(request):
	code = 0
	msg='修改成功'
	try:
		datas = eval(request.POST.get('datas'))
		for data in datas:
			oldcon = DBCon.objects.filter(~Q(id=data['id']) & Q(description=data['description'], scheme=data['scheme']))
			if len(oldcon)!=0:
				msg = "配置方案【%s】下已存在描述为【%s】的数据连接" % (data['scheme'], data['description'])
				break
			con = DBCon.objects.get(id=data['id'])
			con.kind = data['kind']
			con.description = data['description']
			con.dbname = data['dbname']
			con.username = data['username']
			con.password = data['password']
			con.host = data['host']
			con.port = data['port']
			con.scheme = data['scheme']
			con.save()
	except:
		logger.error(traceback.format_exc())
		msg=traceback.format_exc()
		code = 1
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)





def getplan(id, kind):
	logger.info('get', id, kind)
	if kind == 'case':
		try:
			k = Order.objects.get(follow_id=id, kind='plan_case')
		except:
			k = Order.objects.get(follow_id=id, kind='case_case')
		schemename = getplan(k.main_id, k.kind.split('_')[0])
		return schemename
	elif kind == 'step':
		k = Order.objects.get(follow_id=id, kind='case_step')
		schemename = getplan(k.main_id, k.kind.split('_')[0])
		return schemename
	elif kind == 'plan':
		schemename = Plan.objects.get(id=id).schemename
		return schemename


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


@csrf_exempt
def querydblistdefault(request):
	code, msg = 0, ''
	kind = None
	uid = None
	dbname = ''
	try:
		kind = request.POST.get('kind')
		uid = request.POST.get('uid')
		
		if kind == 'step':
			dbid = Step.objects.get(id=uid).db_id
			if dbid:
				dbname = DBCon.objects.get(id=dbid).description
		
		elif kind == 'case':
			dbid = Case.objects.get(id=uid).db_id
			if dbid:
				dbname = DBCon.objects.get(id=dbid).description
		elif kind == 'plan':
			dbid = Plan.objects.get(id=uid).db_id
			if dbid:
				dbname = DBCon.objects.get(id=dbid).description
		
		return JsonResponse(simplejson(code=0, msg='查询成功', data=dbname), safe=False)
	
	except:
		error = traceback.format_exc()
		logger.info(error)
		return JsonResponse(simplejson(code=4, msg='库名下拉列表默认值返回异常'), safe=False)


@csrf_exempt
def copyDbCon(request):
	action = request.POST.get('action')
	dbids = request.POST.getlist('dbids[]')
	copyschemevalue = request.POST.get('copyschemevalue')
	s = dbconRepeatCheck(dbids, copyschemevalue, action)
	code = 1
	if s == '':
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
				s = '复制成功'
			elif action == '0':
				for id in dbids:
					dbcon = DBCon.objects.get(id=id)
					dbcon.scheme = copyschemevalue
					dbcon.save()
				s = '修改成功'
		except:
			code = 1
			s = traceback.format_exc()
			logger.info(s)
	return JsonResponse({'code': code, 'msg': s})


def dbconRepeatCheck(dbids, copyschemevalue, action):
	logger.info(dbids, copyschemevalue, action)
	s = ''
	# 一个方案下面描述名不能重复
	if action == '1':
		for id in dbids:
			description = DBCon.objects.get(id=id).description
			dbcon = DBCon.objects.filter(scheme=copyschemevalue, description=description)
			if len(dbcon) == 0:
				continue
			else:
				s += "<div class='copyerror'>配置方案【%s】下已存在描述为【%s】的数据连接<br></div>" % (copyschemevalue, description)
	elif action == '0':
		for id in dbids:
			description = DBCon.objects.get(id=id).description
			oldcon = DBCon.objects.filter(~Q(id=id) & Q(description=description, scheme=copyschemevalue))
			if len(oldcon) == 0:
				continue
			else:
				s += "<div class='copyerror'>配置方案【%s】下已存在描述为【%s】的数据连接<br></div>" % (
					copyschemevalue,
					description) if copyschemevalue != '' else "<div class='copyerror'>已存在描述名为【%s】的全局数据连接配置<br></div>" % description
	return s


"""
变量相关接口
"""


def var(request):
	return render(request, 'manager/var.html')


@csrf_exempt
def queryonevar(request):
	code = 0
	msg = ''
	res = None
	try:
		res = Variable.objects.get(id=request.POST.get('id'))
		tag = Tag.objects.values('planids', 'customize').get(var=res)
		logger.info(tag['customize'])
		planids = json.loads(tag['planids'])
		des = ''
		ids = []
		for k, v in planids.items():
			des += k + ';'
			ids.append(v)
		tag['des'] = des
		tag['ids'] = ids
		jsonstr = json.dumps(res, cls=VarEncoder)
		jsonstr['tags'] = tag
		return JsonResponse(jsonstr, safe=False)
	except:
		logger.info(traceback.format_exc())
		code = 1
		msg = '查询异常[%s]' % traceback.format_exc()
		return JsonResponse({'code': code, 'msg': msg})


@csrf_exempt
def queryvar(request):
	logger.info('fdaldalfdj')
	searchvalue = request.POST.get('searchvalue')
	searchvalue = '%' + searchvalue + '%'
	userid = request.POST.get('userid')
	tags = request.POST.getlist('tags[]')
	strtag = '%'
	for i in tags:
		if i == '0':
			strtag = '%%'
		elif i != '0':
			strtag += i.split('_')[1] + '%'
	logger.info(strtag)
	
	bindplan = request.POST.get('bindplan') if request.POST.get('bindplan') != '' else ''
	bindstr = '%","' + bindplan + '"]%' if bindplan != '' else '%%'
	userid = userid if userid != '0' else str(User.objects.values('id').get(name=request.session.get('username'))['id'])
	logger.info("searchvalue=>", searchvalue)
	
	with connection.cursor() as cursor:
		sql = '''SELECT t.customize ,t.planids,v.id,description,`key`,gain,value,is_cache,u.name as author FROM `manager_variable` v,login_user u
					,manager_tag t where (description like %s or `key` like %s or gain like %s)
					and t.customize like %s and v.author_id=u.id AND t.var_id=v.id  and planids like %s '''
		if userid != '-1':
			sql += 'and v.author_id=%s'
			cursor.execute(sql, [searchvalue, searchvalue, searchvalue, strtag, bindstr, userid])
		else:
			cursor.execute(sql, [searchvalue, searchvalue, searchvalue, strtag, bindstr])
		desc = cursor.description
		
		rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
		for i in rows:
			m = ''
			for j in i['customize'].split(';'):
				if j != '':
					m += "<span class='layui-badge' onclick=tagSpanClick(this) style='cursor:pointer;'>" + j + "</span> "
			i['customize'] = m
		for i in rows:
			n = ''
			x = json.loads(i['planids'])
			for k, v in x.items():
				n += "<span class='layui-badge layui-bg-green' id=" + v[
					1] + " onclick=planSpanClick(this) style='cursor:pointer;'>" + k + "</span> "
			i['planids'] = n
		limit = request.POST.get('limit')
		page = request.POST.get('page')
		res, total = getpagedata(rows, page, limit)
		jsonstr = json.dumps(res, cls=VarEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)


@csrf_exempt
def delvar(request):
	id_ = request.POST.get('ids')
	# logger.info('ids=>',id_)
	ids = id_.split(',')
	code = 0
	msg = '删除成功.'


	try:
		for i in ids:
			vf=list(Variable.objects.filter(id=i))
			for v in vf:
				Tag.objects.filter(var=v).delete()
				v.delete()

	
	except:
		code = 1
		msg = "删除失败[%s]" % traceback.format_exc()
	
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def editvar(request):
	logger.info("===============editvar=========================================================")
	id_ = request.POST.get('id')
	code = -1
	msg = ''
	key = request.POST.get('key')
	bindplans = request.POST.get('bindplans')
	state = varRepeatCheck(key, bindplans, id_)
	if state != '':
		return JsonResponse(simplejson(code=1, msg=state), safe=False)
	description = request.POST.get('description')
	gain = request.POST.get('gain')
	value = request.POST.get('value')
	tags = request.POST.get('tag') if request.POST.get('tag') != ';' else ''
	is_cache = request.POST.get('is_cache')
	try:
		if is_valid_where_sql(gain) is False:
			return JsonResponse(simplejson(code=2, msg='获取方式输入可能有错误 请检查.'), safe=False)
		c1 = is_valid_gain_value(gain, value)
		if c1 is not True:
			return JsonResponse(simplejson(code=2, msg=c1), safe=False)
		
		var = Variable.objects.get(id=id_)
		var.value = value
		var.description = description
		var.gain = gain
		var.key = key
		var.is_cache = is_cache
		var.is_cache = True if var.is_cache is 'ON' else False
		var.save()
		
		tag = Tag.objects.get(var=var)
		tag.planids = bindplans
		tag.customize = tags
		tag.isglobal = 1 if bindplans == '{}' else 0
		tag.save()
		msg = '编辑成功'
		code = 0
	except:
		logger.info(traceback.format_exc())
		code = 1
		msg = "编辑失败[%s]" % traceback.format_exc()
	
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)

@csrf_exempt
def editmultivar(request):
	# 绑定计划修改不考虑
	datas = eval(request.POST.get('datas'))
	code = 0
	msg = '修改成功'
	try:
		for data in datas:
			bindplans=Tag.objects.get(var = Variable.objects.get(id=data['id'])).planids
			state = varRepeatCheck(data['key'],bindplans,data['id'])
			if state!= '':
				msg = state
				break
			data['customize']=data['customize'].replace(
				"<span class='layui-badge' onclick=tagSpanClick(this) style='cursor:pointer;'>",'').replace('</span> ',';')
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
				state = "变量%s已经绑定过计划：<br>%s" % (key,str) if str != '' else ''
		
		else:
			state = ''
	except:
		logger.info(traceback.format_exc())
		state = traceback.format_exc()
	finally:
		logger.info(state)
		return state


@csrf_exempt
def addvar(request):
	code = 0
	msg = ''
	try:
		key = request.POST.get('key')
		bindplans = request.POST.get('bindplans')
		state = varRepeatCheck(key, bindplans)
		if state != '':
			return JsonResponse(simplejson(code=1, msg=state), safe=False)
		description = request.POST.get('description')
		value = request.POST.get('value')
		gain = request.POST.get("gain").replace("\n", "")  # 修复前端联想bug
		is_cache = request.POST.get('is_cache')
		tags = request.POST.get('tag') if request.POST.get('tag') != ';' else ''
		author = User.objects.get(name=request.session.get('username', None))
		# gain为sql时格式验证
		if is_valid_where_sql(gain) is False:
			return JsonResponse(simplejson(code=2, msg='获取方式输入可能有错误 请检查.'), safe=False)
		# gain&value 单输入验证
		c1 = is_valid_gain_value(gain, value)
		if c1 is not True:
			return JsonResponse(simplejson(code=2, msg=c1), safe=False)
		
		var = Variable()
		var.description = description
		var.key = key
		var.value = value
		var.gain = gain
		var.author = author
		var.is_cache = True if is_cache == 'ON' else False
		var.save()
		
		tag = Tag()
		tag.planids = bindplans
		tag.customize = tags
		tag.isglobal = 1 if bindplans == '{}' else 0
		tag.var = var
		tag.save()
		msg = '新增成功'
	except:
		logger.info(traceback.format_exc())
		code = 1
		msg = "新增失败"
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def copyVar(request):
	code = 0
	msg = ''
	varids = request.POST.getlist('varids[]')
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
				copyvar.author = User.objects.get(name=request.session.get('username', None))
				copyvar.save()
				tag.var = copyvar
				tag.isglobal = 1 if bindplans == '{}' else 0
				tag.customize = Tag.objects.get(var=var).customize if tags == '' else tag
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


def case(request):
	return render(request, 'manager/case.html')


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
		
		t = T.Transformer(config_wb, data_wb)
		t.transform()
		
		return JsonResponse(simplejson(code=0, msg='转换成功..'), safe=False)
	
	except:
		err = traceback.format_exc()
		return JsonResponse(simplejson(code=4, msg='转换异常[%s]' % err), safe=False)


def third_party_call(request):
	res = decrypt_third_invoke_url_params(request.GET.get('v'))
	planid = request.GET.get('planid')
	plan = Plan.objects.get(id=planid)
	taskid = gettaskid(plan.__str__())
	dbscheme = request.GET.get('scheme')
	clear_task_before(taskid)
	callername = res['callername']
	is_verify = request.GET.get('is_verify')
	
	if getRunningInfo(callername, planid, 'isrunning') != '0':
		return JsonResponse(simplejson(code=1, msg="调用失败，任务正在运行中，稍后再试！"), safe=False)
	
	logger.info('调用方=>', callername)
	logger.info('调用计划=>', planid)
	logger.info('调用数据连接方案=>', dbscheme)
	runplans(callername, taskid, [planid], is_verify, None, dbscheme)
	return JsonResponse(simplejson(code=0, msg="调用成功,使用DB配置:[%s]" % dbscheme, taskid=taskid), safe=False)


@xframe_options_exempt
def plan(request):
	return render(request, 'manager/plan.html')


@csrf_exempt
def mailcontrol(request):
	code = 0
	msg = ''
	try:
		plan = Plan.objects.get(id=request.POST.get('planid'))
		is_send_mail = request.POST.get('is_send_mail')
		config = MailConfig.objects.get(id=plan.mail_config_id)
		config.is_send_mail = is_send_mail
		config.save()
		msg = "[%s]发送邮件功能" % is_send_mail
	except:
		logger.info(traceback.format_exc())
		code = 2
		msg = '操作失败[%s]' % traceback.format_exc()
	
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def queryoneplan(request):
	code = 0
	msg = ''
	res = None
	try:
		res = Plan.objects.get(id=request.POST.get('id').split('_')[1])
		pass
	except:
		code = 1
		msg = '查询异常[%s]' % traceback.format_exc()
	finally:
		jsonstr = json.dumps(res, cls=PlanEncoder)
		return JsonResponse(jsonstr, safe=False)


@csrf_exempt
def queryplantaskid(request):
	"""
	查询计划关联任务id 包含定时任务
	按时间降序返回
	"""
	code = 0
	msg = ''
	taskids = None
	try:
		planid = request.POST.get('planid')
		plan = Plan.objects.get(id=planid)
		detail = list(ResultDetail.objects.filter(plan=plan).order_by('-createtime'))
		taskids = [x for x in set([x.taskid for x in detail])]
	except Exception as e:
		code = 1
		msg = str(e)
	
	return JsonResponse(simplejson(code=code, msg=msg, data=taskids), safe=False)


def querytaskdetail(request):
	detail = {}
	taskid = request.GET.get('taskid')
	
	detail = gettaskresult(taskid)
	
	# logger.info(detail)
	
	# import json
	# jsonstr=json.dumps(detail)
	# return JsonResponse(jsonstr,safe=False)
	return render(request, 'manager/taskdetail.html', locals())


# def rendertaskdetail(request):
# 	return render(request, 'manager/taskdetail.html',locals())

"""
任务相关
"""


@csrf_exempt
def runtask(request):
	planids = request.POST.get("ids")
	list_ = [int(x) for x in planids.split(",")]
	for planid in list_:
		plan = Plan.objects.get(id=planid)
		username = request.session.get('username')
		state_running =getRunningInfo(username, planid, 'isrunning')
		if state_running != '0':
			msg = '验证' if state_running == 'verify' else '调试'
			return JsonResponse(simplejson(code=1, msg='计划正在运行[%s]任务，稍后再试！'%msg), safe=False)
		
		taskid = gettaskid(plan.__str__())
		is_verify = request.POST.get('is_verify')
		runplans(username, taskid, list_, is_verify)
	return JsonResponse(simplejson(code=0, msg="你的任务开始运行", taskid=taskid), safe=False)


@csrf_exempt
def callfromthreeparty(request):
	str_ = '' % ()
	key = Fu._md5(obj)


@csrf_exempt
def changetocrontab(request):
	code = 0
	msg = ""
	try:
		planid = request.POST.get("planid")
		author = User.get(name=request.session.get('username', None))
		plan = Plan.objects.get(id=planid)
		taskid = gettaskid(plan.__str__())
		config = Crontab()
		config.plan = plan
		config.taskid = taskid
		config.value = ''
		config.author = author
		
		config.save()
		plan.run_type = '定时运行'
		plan.save()
	
	except:
		code = 1
		msg = '操作失败'
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def changetonormal(request):
	code = 0
	msg = ""
	try:
		planid = request.POST.get('planid')
		plan = Plan.objects.get(id=planid)
		taskid = gettaskid(plan.__str__())
		config = Crontab.get(plan=plan)
		config.delete()
		
		plan.run_type = '手动运行'
		plan.save()
	
	except:
		code = 1
		msg = '操作失败'
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def opencrontab(request):
	code = 0
	msg = ''
	username = 'tester'
	planid = 1
	res = Cron.opencrontab(username, planid)
	if res == True:
		msg = "开启计划[%s]的定时任务成功"
	else:
		code = 1
		msg = "开启计划[%s]的定时任务失败"
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def closecrontab(request):
	code = 0
	msg = ''
	username = 'tester'
	planid = 1
	res = Cron.closecrontab(username, planid)
	if res == True:
		msg = "关闭计划[%s]的定时任务成功"
	else:
		code = 1
		msg = "关闭计划[%s]的定时任务失败"
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)

@csrf_exempt
def resultdetail(request):
	return render(request, 'manager/resultdetail.html')


@csrf_exempt
def queryresultdetail(request):
	searchvalue = request.GET.get('searchvalue')
	logger.info("searchvalue=>", searchvalue)
	res = None
	if searchvalue:
		logger.info("变量查询条件=>")
		res = list(ResultDetail.objects.filter(
			Q(description__icontains=searchvalue) | Q(key__icontains=searchvalue) | Q(value__icontains=searchvalue)))
	else:
		res = list(ResultDetail.objects.all())
	
	limit = request.GET.get('limit')
	page = request.GET.get('page')
	res, total = getpagedata(res, page, limit)
	
	jsonstr = json.dumps(res, cls=ResultDetailEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)


@csrf_exempt
def delresultdetail(request):
	id_ = request.POST.get('id')
	code = 0
	msg = ''
	try:
		ResultDetail.objects.get(id=id_).delete()
	except:
		code = 1
		msg = "删除失败"
	
	finally:
		return JsonResponse(simplejson(code=code, msg=""))


"""
远端日志相关
"""


def logconfig(request):
	return render(request, "manager/logconfig.html")


def queryonelogconfig(request):
	pass


def querylogconfig(request):
	pass


def addlogconfig(request):
	pass


def editlogconfig(request):
	pass


def dellogconfig(request):
	pass


def remote_log_recv(request):
	pass
	linemsg = request.POST.get('linemsg')
	key = '#host#logfile'


"""

函数相关
"""


def func(request):
	return render(request, "manager/func.html")


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
		f.author = User.objects.get(name=request.session.get('username', None))
		f.description = request.POST.get("description")
		# base64 str 存储
		tbody = request.POST.get("body")
		f.name = Fu.getfuncname(tbody)[0]
		# logger.info("函数名称=>",f.name)
		# logger.info("tbody=>",tbody)
		f.body = base64.b64encode(tbody.encode('utf-8')).decode()
		# f.flag=Fu.flag(f.body)
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


def step(request):
	return render(request, 'manager/step.html')


@csrf_exempt
def queryonestep(request):
	code = 0
	msg = ''
	urid = request.POST.get('id').split('_')[1]
	try:
		
		if urid is None:
			return JsonResponse(simplejson(code=2, msg='查询urid异常'), safe=False)
		
		step = Step.objects.get(id=urid)
		jsonstr = json.dumps(step, cls=StepEncoder)
		return JsonResponse(jsonstr, safe=True)
	
	
	except:
		logger.info(traceback.format_exc())
		return JsonResponse(simplejson(code=3, msg='查询异常'), safe=False)


@csrf_exempt
def querystep(request):
	limit = request.GET.get('limit')
	page = request.GET.get('page')
	searchvalue = request.GET.get('searchvalue')
	main_id = request.POST.get("mainid")
	logger.info("searchvalue=>", searchvalue)
	logger.info("mainid=>", main_id)
	
	res = []
	# 1.有searchvalue 无mainid的查询
	
	# 2.有mainid 无searchvalue的子步骤查询
	
	# 3.searchvalue&mianid都没 返回all step
	
	# if searchvalue&len(searchvalue.strip())==0:
	# 	searchvalue=None
	
	if searchvalue and main_id is None:
		logger.info("querystep 查询情况1")
		# tags=list(Tag.objects.filter(Q(name__contains=searchvalue)))
		# for tag in tags:
		# 	tagid=tag.id
		# 	r=list(Step.objects.filter(Q(tag_id=tagid)))
		# 	res=res+r
		res = res + list(
			Step.objects.filter(Q(description__icontains=searchvalue) | Q(step_type__icontains=searchvalue)))
	
	elif main_id and searchvalue is None:
		'''@delete
		'''
		logger.info("querystep 查询情况2")
		res = list(Case.objects.get(id=main_id).steps.all())
	
	
	
	elif main_id is None and not searchvalue:
		logger.info("querystep 查询情况3")
		res = list(Step.objects.all())
	# res=list(BusinessData.objects.all())
	# res,total=getpagedata(res, page, limit)
	# jsonstr=json.dumps(res,cls=BusinessDataEncoder,total=total)
	# return JsonResponse(jsonstr,safe=False)
	else:
		# warnings.warn("querystep不支持这种情况..")
		pass
	
	logger.info("查询结果：", res)
	# res=getpagedata(res, request)
	
	res, total = getpagedata(res, page, limit)
	
	jsonstr = json.dumps(res, cls=StepEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)


"""邮件配置相关
"""


@csrf_exempt
def mailconfig(request):
	return render(request, 'manager/mailconfig.html')


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
			author = User.objects.get(name=request.session.get('username'))
			config.author = author
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
def querymailconfig(request):
	searchvalue = request.GET.get('searchvalue')
	# logger.info("searchvalue=>",searchvalue)
	res = None
	if searchvalue:
		logger.info("变量查询条件=>")
		res = list(MailConfig.objects.filter(
			Q(description__icontains=searchvalue) | Q(rich_text__icontains=searchvalue) | Q(
				to_receive__icontains=searchvalue) | Q(cc_receive__icontains=searchvalue)))
	else:
		res = list(MailConfig.objects.all())
	
	limit = request.GET.get('limit')
	page = request.GET.get('page')
	res, total = getpagedata(res, page, limit)
	
	jsonstr = json.dumps(res, cls=MailConfigEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)


"""执行顺序相关
"""


@csrf_exempt
def addorder(request):
	code = 0
	msg = ''
	main_id = request.POST.get("main_id")
	follow_id = request.POST.get("follow_id")
	username = request.session.get('username', None)
	kind = request.POST.get("kind")
	
	try:
		
		#
		if kind == 'case':
			case = Case.objects.get(id=main_id)
			step = Step.objects.get(id=follow_id)
			case.steps.add(step)
			case.save()
		
		elif kind == 'plan':
			plan = Plan.objects.get(id=main_id)
			case = Case.objects.get(id=follow_id)
			plan.cases.add(case)
			plan.save()
		else:
			pass
		#
		LIST = list(Order.objects.filter(main_id=main_id, kind=kind, follow_id=follow_id))
		if len(LIST) > 0:
			for item in LIST:
				item.delete()
		
		order = Order()
		order.main_id = main_id
		order.follow_id = follow_id
		order.author = User.objects.get(name=username)
		order.kind = kind
		order.save()
	
	except Exception as e:
		logger.info(e)
		traceback.logger.info_exc(e)
		code = 1
	
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def addordervalue(request):
	code = 0
	msg = ""
	try:
		main_id = request.POST.get("main_id")
		follow_id = request.POST.get("follow_id")
		type_ = request.POST.get("kind")
		
		genorder(type_=kind, parentid=main_id, childid=follow_id)
	except:
		code = 1
		msg = ""
	
	return JsonResponse(simplejson(code=code, msg=""))



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
	'''
	'''
	action = request.GET.get('action') or request.POST.get('action', '')
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
			k = eval(callstr)
			logger.info('k=>', k)
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
		
		except:
			logger.info(traceback.format_exc())
			return JsonResponse(pkg(code=4, msg='%s' % traceback.format_exc()), safe=False)


"""
录制操作
"""


def record(request):
	response = render(request, 'manager/record.html', locals())
	# response["Access-Control-Allow-Origin"] = "*"
	# response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
	# response["Access-Control-Max-Age"] = "1000"
	# response["Access-Control-Allow-Headers"] = "*"
	return response


# @csrf_exempt
# def changepos(requests):
# 	res0 = {
# 		"code": 0,
# 		"msg": '',
# 		"data": None
# 	}
# 	try:

# 		# logger.info('KK'*100)

# 		move_kind = requests.POST.get('move_kind')
# 		main_id = requests.POST.get("main_id")
# 		follow_id = requests.POST.get("follow_id")
# 		kind = requests.POST.get("kind")
# 		username = requests.session.get('username', None)
# 		move = requests.POST.get("move")
# 		aid = requests.POST.get('aid')
# 		bid = requests.POST.get('bid')

# 		if 'swap' == move_kind:
# 			res = swap(kind, main_id, aid, bid)
# 			# logger.info('swap结果=>',res)
# 			if res[0] is not 'success':
# 				raise RuntimeError(res[1])
# 		else:
# 			changepostion(kind, main_id, follow_id, move)

# 		_main_order = ordered(list(Order.objects.filter(main_id=main_id, kind=kind)))
# 		# logger.info(_main_order)
# 		res = []
# 		for item in _main_order:
# 			# desp=BusinessData.objects.get(id=item.follow_id).businessname if kind=="step" else Case.objects.get(id=item.follow_id).description
# 			desp = None

# 			if kind == 'step':
# 				business = BusinessData.objects.get(id=item.follow_id)
# 				status, stepinst = gettestdatastep(business.id)
# 				if status is not 'success':
# 					return JsonResponse(simplejson(code=3, msg=stepinst), safe=False)

# 				desp = "%s_%s" % (stepinst.description, business.businessname)
# 			else:
# 				desp = Case.objects.get(id=item.follow_id).description

# 			obj = {
# 				"id": item.follow_id,
# 				"description": desp,
# 				"order": Order.objects.get(main_id=main_id, follow_id=item.follow_id, kind=kind).value
# 			}
# 			res.append(obj)

# 		res0["data"] = res
# 		res0['msg'] = '操作成功'

# 		return JsonResponse(json.dumps(res0), safe=False)
# 	except:
# 		error = traceback.format_exc()
# 		return JsonResponse(simplejson(code=4, msg='交换异常[%s]' % error), safe=False)


# @csrf_exempt
# def aftergroup(request):
# 	res0 = {
# 		"code": 0,
# 		"msg": '',
# 		"data": None
# 	}

# 	main_id = request.POST.get("main_id")
# 	follow_id = request.POST.get("follow_id")
# 	kind = request.POST.get("kind")

# 	genorder(kind, main_id, follow_id)

# 	_main_order = ordered(list(Order.objects.filter(main_id=main_id, kind=kind)))
# 	# logger.info(_main_order)
# 	res = []
# 	for item in _main_order:
# 		# desp=BusinessData.objects.get(id=item.follow_id).businessdata if kind=="step" else Case.objects.get(id=item.follow_id).description
# 		desp = None

# 		if kind == 'step':
# 			business = BusinessData.objects.get(id=item.follow_id)
# 			status, stepinst = gettestdatastep(business.id)
# 			if status is not 'success':
# 				return JsonResponse(simplejson(code=3, msg=stepinst), safe=False)
# 			desp = "%s_%s" % (stepinst.description, business.businessname)
# 		else:
# 			desp = Case.objects.get(id=item.follow_id).description

# 		obj = {
# 			"id": item.follow_id,
# 			"description": desp,
# 			"order": Order.objects.get(main_id=main_id, follow_id=item.follow_id, kind=kind).value
# 		}
# 		res.append(obj)

# 	res0["data"] = res

# 	return JsonResponse(json.dumps(res0), safe=False)


'''
业务数据相关
'''


# @csrf_exempt
# def querybusinessdata(request):
# 	code, msg = 0, ''
# 	res = []
# 	try:

# 		callername = request.session.get('username')
# 		stepid = request.POST.get('stepid')
# 		flag = request.POST.get('flag')
# 		vids_ = request.POST.get('vids')
# 		vid = request.POST.get('vid')
# 		vids = []
# 		if vids_:
# 			vids = vids_.split(',')

# 		extdata = {
# 			'id': request.POST.get('id'),
# 			'businessname': request.POST.get('businessname'),
# 			'itf_check': request.POST.get('itf_check'),
# 			'db_check': request.POST.get('db_check'),
# 			'params': request.POST.get('params')
# 		}

# 		if flag == '0':
# 			res = querytestdata(callername, stepid)
# 		elif flag == '1':
# 			res = qa(callername, stepid, extdata)
# 		elif flag == '2':
# 			res = qe(callername, stepid, extdata)
# 		elif flag == '3':
# 			res = qd(callername, stepid, vids)
# 		elif flag == '4':
# 			res = qc(callername, stepid, vid)

# 		jsonstr = json.dumps(res, cls=BusinessDataEncoder)
# 		return JsonResponse(jsonstr, safe=False)
# 	except:
# 		error = traceback.format_exc()
# 		logger.info(error)
# 		code = 4
# 		msg = '操作异常[%s]' % error
# 		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def queryonebusiness(request):
	code = 0
	msg = ''
	try:
		callername = request.session.get('username')
		# vid = request.POST.get('vid').split('_')[1]
		# business = BusinessData.objects.get(id=vid)
		# logger.info('business=>', business)
		# jsonstr = json.dumps(business, cls=BusinessDataEncoder)
		sql = '''
		SELECT b.id,count,businessname,timeout,itf_check,db_check,params,preposition,postposition,value as weight,parser_id,parser_check,description
		FROM manager_businessdata b, manager_order o WHERE b.id=%s and o.follow_id=b.id
		'''
		with connection.cursor() as cursor:
			cursor.execute(sql, [request.POST.get('vid').split('_')[1]])
			desc = cursor.description
			row = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
		return JsonResponse({'code': 0, 'data': row})
	# return JsonResponse(jsonstr, safe=False)
	except:
		code = 4
		msg = '查询异常[%s]' % traceback.format_exc()
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


# @csrf_exempt
# def queryonebusinessdata(request):
# 	code = 0
# 	msg = ''
# 	res = None
# 	try:
# 		callername = request.session.get('username')
# 		stepid = request.POST.get('stepid')
# 		vid = request.POST.get('vid')
# 		res = querytestdata(callername, stepid, trigger='detail')
# 		t = [r for r in res if str(r.id) == str(vid)]
# 		if len(t) > 0:
# 			t = t[0]
# 		else:
# 			return JsonResponse(simplejson(code=3, msg='查询失败 缓存里没找到id=%s对应测试数据' % vid), safe=False)

# 		jsonstr = json.dumps(t, cls=BusinessDataEncoder)
# 		return JsonResponse(jsonstr, safe=False)
# 	except:
# 		code = 1
# 		msg = '查询异常[%s]' % traceback.format_exc()
# 		return JsonResponse(simplejson(code=4, msg=msg), safe=False)


@csrf_exempt
def querybusinessdatalist(request):
	code, msg = 0, ''
	try:
		res = list(BusinessData.objects.all())
		
		jsonstr = json.dumps(res, cls=BusinessDataEncoder)
		# logger.info('json=>',jsonstr)
		return JsonResponse(jsonstr, safe=False)
	except:
		err = (traceback.format_exc())
		logger.info(err)
		return JsonResponse(simplejson(code=4, msg='查询异常[%s]' % err))


@csrf_exempt
def querytreelist(request):
	from .cm import getchild, get_search_match
	datanode = []
	
	def _get_pid_data(idx, type, data):
		
		if type == 'product':
			
			product = Product.objects.get(id=idx)
			logger.info('product=>', product)
			plans = cm.getchild('product_plan', idx)
			logger.info('plans=>', plans)
			for plan in plans:
				data.append({
					
					'id': 'plan_%s' % plan.id,
					'pId': 'product_%s' % product.id,
					'name': plan.description,
					'type': 'plan',
					'textIcon': 'fa icon-fa-product-hunt',
					# 'open':True
				})
			
			return data
		
		elif type == 'plan':
			plan = Plan.objects.get(id=idx)
			cases = cm.getchild('plan_case', idx)
			logger.info('cases=>', cases)
			for case in cases:
				logger.info('case=>', case)
				casename = case.description
				if case.count in (0, '0'):
					casename = '<s>%s</s>' % casename
				data.append({
					'id': 'case_%s' % case.id,
					'pId': 'plan_%s' % plan.id,
					'name': casename,
					'type': 'case',
					'textIcon': 'fa icon-fa-folder',
					# 'open':True
				})
			return data
		# return get_pid_data(case.id,'case',data)
		
		elif type == 'case':  ###这里会有个乱序的问题
			case = Case.objects.get(id=idx)
			
			steps = cm.getchild('case_step', idx)
			
			for step in steps:
				stepname = step.description
				if step.count in (0, '0'):
					stepname = '<s>%s</s>' % stepname
				data.append({
					'id': 'step_%s' % step.id,
					'pId': 'case_%s' % case.id,
					'name': stepname,
					'type': 'step',
					'textIcon': 'fa icon-fa-file-o',
					# 'open':True
				})
			
			cases = cm.getchild('case_case', idx)
			for case0 in cases:
				casename = case0.description
				if case0.count in (0, '0'):
					casename = '<s>%s</s>' % casename
				data.append({
					'id': 'case_%s' % case0.id,
					'pId': 'case_%s' % idx,
					'name': casename,
					'type': 'case',
					'textIcon': 'fa icon-fa-folder',
				})
			
			return data
		
		
		elif type == 'step':
			step = Step.objects.get(id=idx)
			businesslist = cm.getchild('step_business', idx)
			
			for business in businesslist:
				bname = business.businessname
				if business.count in (0, '0'):
					bname = '<s>%s</s>' % bname
				data.append({
					'id': 'business_%s' % business.id,
					'pId': 'step_%s' % step.id,
					'name': bname,
					'type': 'business',
					'textIcon': 'fa icon-fa-leaf',
					# 'open':True
				})
			
			# return get_pid_data(business.id,'business', data)
			return data
		else:
			return data
	
	####
	id_ = request.POST.get('id')
	if id_:
		id_ = id_.split('_')[1]
	
	type_ = request.POST.get('type')
	callername = request.session.get('username')
	searchvalue = request.POST.get('searchvalue')
	
	##
	
	if id_:
		datanode = _get_pid_data(id_, type_, datanode)
		logger.info('cur d=>', datanode)
	elif searchvalue:
		datanode = get_search_match(searchvalue)
	
	else:
		logger.info('query id is None')
		
		datanode.append({'id': -1, 'name': '产品池', 'type': 'root', 'textIcon': 'fa fa-pinterest-p33', 'open': True})
		productlist = list(Product.objects.all())
		for product in productlist:
			datanode.append({
				'id': 'product_%s' % product.id,
				'pId': -1,
				'name': product.description,
				'type': 'product',
				'textIcon': 'fa icon-fa-home'
			})
	
	##
	
	logger.info('query tree result=>%s' % datanode)
	return JsonResponse(simplejson(code=0, data=datanode), safe=False)


@csrf_exempt
def treetest(request):
	return render(request, 'manager/tree.html')


"""
标签管理
"""


def tag(request):
	return render(request, 'manager/tag.html')


@csrf_exempt
def addtag(request):
	t = Tag()
	try:
		
		all_name = [_.name for _ in list(Tag.objects.all())]
		t.name = request.POST.get('name')
		if t.name in all_name:
			return JsonResponse(pkg(code=3, msg='标签[%s]已存在' % t.name))
		t.author = User.objects.get(name=request.session.get('username'))
		t.save()
		return JsonResponse(pkg(code=0, msg='添加标签[%s]' % t.name, data={'id': t.id, 'name': t.name}))
	except:
		return JsonResponse(pkg(code=4, msg='添加标签[%s]异常' % t.name))


@csrf_exempt
def deltag(request):
	try:
		
		ids = [int(_) for _ in request.POST.get('ids').split(',')]
		for id_ in ids:
			Tag.objects.get(id=id_).delete()
		
		return JsonResponse(pkg(code=0, msg='删除成功.'))
	except:
		return JsonResponse(pkg(code=4, msg='删除标签异常'))


def edittag(request):
	pass


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
		data = [{'id': 0, 'name': '全部标记'}]
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


@csrf_exempt
def varBatchEdit(request):
	ids = request.POST.getlist('ids[]')
	tags = request.POST.get('tags')
	logger.info(ids)
	logger.info(tags)
	for id in ids:
		try:
			var = Variable.objects.get(id=id)
			var.tag = tags
			var.save()
		except:
			return JsonResponse({'code': 1, 'msg': '变量' + var.description + '标签更改失败！'})
	return JsonResponse({'code': 0, 'msg': 'success'})


'''
报文模板

'''


def template(request):
	return render(request, 'manager/template.html')


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
	pa['author'] = User.objects.get(name=request.session.get('username'))
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
	is_sort_display = ''
	is_start_display = ''
	kind = Template.objects.get(id=tid).kind
	if kind == 'length':
		is_sort_display = 'none'
	
	else:
		is_start_display = 'none'
	
	logger.info('sort', is_sort_display)
	logger.info('start', is_start_display)
	
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


def getfulltree(request):
	data = cm.get_full_tree()
	logger.info(len(data))
	
	return JsonResponse(pkg(data=data))


def testaddtask(request):
	from .cron import Cron
	
	# scheduler.add_job(test, 'interval', seconds=3)
	username = request.session.get('username', None)
	Cron._addcrontab(runplans, 'interval', seconds=15, args=['tester', gettaskid(), ['1'], '定时'], id='')
	Cron._addcrontab(runplans, args=[username, crontaskid, [plan.id], '定时'], taskid=crontaskid, **cfg)
	# scheduler.add_job(runplans, 'interval', seconds=15,args=['tester',gettaskid(),['1'],'定时'],id='')
	
	return JsonResponse(simplejson(code=0, msg="fda", yy='dd'), safe=False)




@csrf_exempt
def queryUser(request):
	name = request.session.get('username')
	user = list(User.objects.values('id', 'name').exclude(name=name))
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
		planbinds = json.loads(Tag.objects.values('planids').get(var=Variable.objects.get(id=request.POST.get('id'))).get('planids'))
		plans=[]
		for i in planbinds:
			plans.append({'label':i,'value':'"%s":%s'%(i,json.dumps(planbinds[i]).replace(' ',''))})
		if not plans:
			plans.append({'label':'全局','value':'{}'})
	except:
		print(traceback.format_exc())
		code = 1
		msg = '这个变量可能有些问题'
		planbinds={}
	if len(dbs) == 0:
		code = 1
		msg = '@的库名没有在任何方案下找到'
	return JsonResponse({'code':code,'msg':msg,'data':dbs,'plans':plans})
	


@csrf_exempt
def getParamfromFetchData(request):
	text = request.POST.get('fetchtest')
	step_des=request.POST.get('description')
	pid = request.POST.get('pid').split('_')[1] if request.POST.get('pid') !='false' else 'false'
	uid = request.POST.get('uid').split('_')[1] if request.POST.get('uid') !='false' else 'false'
	bussiness_des = request.POST.get('bussiness_des')
	code=0
	data = ''
	rq = '{%s}' % text.split('fetch(')[1].rstrip(');').replace('\n', '').replace(',', ':', 1)
	try:
		x = json.loads(rq)
		for (k, v) in x.items():
			print('url', k)
			print('content-type', v.get('headers', '').get('Content-Type', ''))
			headers = v.get('headers', {})
			headers['Referer'] = v.get('referrer', '')
			print('headers', headers)
			print('method', v.get('method'))
			contenttype = v.get('headers', '').get('Content-Type', '')
			if contenttype == '':
				contenttype = v.get('headers','').get('content-type','')
			if 'urlencoded' in contenttype:
				contenttype = 'urlencode'
				parsed_result = {}
				pairs = parse.parse_qsl(v.get('body'))
				for name, value in pairs:
					parsed_result[name] = value
				print('body', parsed_result)
			elif 'json' in contenttype:
				contenttype = 'json'
				parsed_result=v.get('body')
				print(parsed_result)
			else:
				return JsonResponse({'code': 1, 'data': '只支持urlencode/json'})
	except:
		print(traceback.format_exc())
		return JsonResponse({'code': 1,'data': '解析失败，检查内容'})
		
	if uid == 'false':
		# 增加步骤
		step = Step()
		step.step_type = 'interface'
		step.description = step_des
		step.headers = headers
		step.body = 'sleep'
		step.url = k
		step.method = v.get('method').lower()
		step.content_type = contenttype
		step.temp = ''
		step.count = '1'
		step.author = User.objects.get(name=request.session.get('username'))
		step.db_id = ''
		step.save()
		addrelation('case_step', request.session.get('username'), pid, step.id)
		b = BusinessData()
		b.businessname = bussiness_des
		b.itf_check = ''
		b.db_check = ''
		b.params = parsed_result
		b.parser_check = ''
		b.parser_id = ''
		b.description = ''
		b.postposition = ''
		b.preposition = ''
		b.count = 1
		b.save()
		addrelation('step_business', request.session.get('username'), step.id, b.id)
		returndata= {
				'id': 'step_%s' % step.id,
				'pid': 'case_%s' % pid,
				'name': step_des,
				'type': 'step',
				'textIcon': 'fa icon-fa-file-o',
		}
		
	if pid == 'false':
		try:
			step = Step.objects.get(id=uid)
			if int(difflib.SequenceMatcher(None, step.url.split('/')[-1], k.split('/')[-1]).ratio()) < 0.9:
				return JsonResponse({'code': 1, 'data': '两个接口可能不一样，请检查'})
			b = BusinessData()
			b.businessname = bussiness_des
			b.itf_check = ''
			b.db_check = ''
			b.params = parsed_result
			b.parser_check = ''
			b.parser_id = ''
			b.description = ''
			b.postposition = ''
			b.preposition = ''
			b.count = 1
			b.save()
			addrelation('step_business', request.session.get('username'), uid, b.id)
			returndata= {
				'id': 'business_%s' % b.id,
				'pId': 'step_%s' % uid,
				'name': bussiness_des,
				'type': 'business',
				'textIcon': 'fa icon-fa-leaf',
			}
		except:
			print(traceback.format_exc())
			
	return JsonResponse({'code': code,'data': returndata})




'''
个人空间管理
'''


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


# 获取文件大小
def _getDocSize(path):
	try:
		size = os.path.getsize(path)
		return _formatSize(size)
	except Exception as err:
		logger.info(err)


# 获取文件夹大小
def _getFileSize(path):
	sumsize = 0
	try:
		filename = os.walk(path)
		for root, dirs, files in filename:
			for fle in files:
				size = os.path.getsize(path + fle)
				sumsize += size
		return _formatSize(sumsize)
	except Exception as err:
		logger.info(err)


@csrf_exempt
def queryuserfile(request):
	'''
	返回个人文件列表
	'''
	searchvalue = request.GET.get('searchvalue')
	mfiles = list()
	username = request.session.get('username')
	userdir = os.path.join(os.path.dirname(__file__), 'storage', 'private', 'File', username)
	if not os.path.exists(userdir):
		os.makedirs(userdir)
	files = os.listdir(userdir)
	logger.info('files=>', files)
	for f in files:
		if searchvalue and not f.__contains__(searchvalue):
			continue;
		mfiles.append({
			'filename': f,
			'size': _getDocSize(os.path.join(userdir, f)),
			'createtime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getctime(os.path.join(userdir, f))))
		})
	
	mfiles.sort(key=lambda e: e.get('createtime'), reverse=True)
	
	return JsonResponse({'code': 0, 'data': mfiles}, safe=False)


@csrf_exempt
def delfiles(request):
	block_files = []
	filenames = request.POST.get('filenames', '')
	logger.info('filenames=>', filenames)
	filenamelist = filenames.split(',')
	for filename in filenamelist:
		filepath = os.path.join(os.path.dirname(__file__), 'storage', 'private', 'File',
		                        request.session.get('username'), filename)
		try:
			os.remove(filepath)
		except:
			block_files.append(filename)
			logger.info(traceback.format_exc())
	
	if len(block_files) == 0:
		return JsonResponse(pkg(code=0, msg='删除成功.'), safe=False)
	else:
		return JsonResponse(pkg(code=4, msg='删除失败[%s].' % (',').join(block_files)), safe=False)


@csrf_exempt
def edit_file_name(request):
	pass


'''
权限控制相关
'''
@csrf_exempt
def authcontrol(request):
	return render(request, 'manager/authcontrol.html', locals())


@csrf_exempt
def queryuicontrol(request):
	res = Grant.query_ui_grant_table(request.GET.get('searchvalue'))
	logger.info('获得UI权限表:',res)
	return JsonResponse(res, safe=False)

@csrf_exempt
def queryoneuicontrol(request):
	return JsonResponse(Grant.query_one_ui_control(request.POST.get('uid')),safe=False)

@csrf_exempt
def queryalluicontrolusers(request):
	return JsonResponse(Grant.queryalluicontrolusers(),safe=False)

@csrf_exempt
def adduicontrol(request):
	return JsonResponse(Grant.add_ui_control(**get_params(request)),safe=False)

@csrf_exempt
def deluicontrol(request):
	res=Grant.del_ui_control(**get_params(request))
	return JsonResponse(res,safe=False)

@csrf_exempt
def updateuicontrol(request):
	return JsonResponse(Grant.edit_ui_control(**get_params(request)),safe=False)
	
@csrf_exempt
def updateuicontrolstatus(request):
	return JsonResponse(Grant. updateuicontrolstatus(**get_params(request)),safe=False)


@csrf_exempt
def queryrole(request):
	searchvalue = request.GET.get('searchvalue')
	logger.info("searchvalue=>", searchvalue)
	res = []
	if searchvalue:
		res = list(Role.objects.filter(Q(name__icontains=searchvalue.strip())))
	else:
		res = list(Role.objects.all())
	
	limit = request.GET.get('limit')
	page = request.GET.get('page')
	res, total = getpagedata(res, page, limit)
	jsonstr = json.dumps(res, cls=RoleEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)

@csrf_exempt
def query_transfer_data(request):
	lfdata=[]
	rgdata=[]
	try:
		roleid=request.POST.get('roleid')
		if roleid:
			olddata=User.objects.all().values('id','name')
			role=Role.objects.get(id=roleid)

			#lfdata=[x for x in olddata if x['id'] not in[user['id'] for user in role.users]]
			lfdata=list(olddata)
			rgdata=[user.id for user in role.users]


		else:

			lfdata=list(User.objects.all().values('id','name'))

		logger.info(type(lfdata))

		return JsonResponse(pkg(code=0,
			msg='计算穿梭框数据成功',
			data=[lfdata,rgdata]
			),safe=False)

	except:
		logger.error(traceback.format_exc())

		return JsonResponse(pkg(code=0,
			msg='计算穿梭框异常',
			),safe=False)

@csrf_exempt
def addrole(request):
	return JsonResponse(RoleData.addrole(**get_params(request)),safe=False)

@csrf_exempt
def delrole(request):
	return JsonResponse(RoleData.delrole(**get_params(request)),safe=False)

@csrf_exempt
def updaterole(request):
	return JsonResponse(RoleData.updaterole(**get_params(request)),safe=False)
	
@csrf_exempt
def queryonerole(request):
	res=RoleData.queryonerole(**get_params(request))
	logger.info('角色明细结果:',res)
	return JsonResponse(res,safe=False)



'''
开发模式切换
'''
@csrf_exempt
def changemode(request):
	dirname=os.path.dirname(os.path.dirname(__file__))
	configpath=os.path.join(dirname,'ME2','settings.py')
	print(configpath)
	lineindex=-1
	lines=[]
	msg = ''
	with open(configpath,encoding='utf-8') as f:
		lines=f.readlines()
	if request.POST.get('action')=='debug':
		for line in lines:
			lineindex=lineindex+1
			if line.strip().replace(' ', '') == 'DEBUG=True':
				lines[lineindex] = 'DEBUG = False\n'
				msg = '调试模式关'
				break
			elif line.strip().replace(' ', '') == 'DEBUG=False':
				lines[lineindex] = 'DEBUG = True\n'
				msg = '调试模式开'
				break
		
		with open(configpath,'w',encoding='utf-8') as f:
			f.write(''.join(lines))
	else :
		for line in lines:
			lineindex = lineindex + 1
			if line.strip().replace(' ', '') == 'DEBUG_TOOLS_ON=True' :
				lines[lineindex] = 'DEBUG_TOOLS_ON = False\n'
				msg = '调试工具关'
				break
			elif line.strip().replace(' ', '') == 'DEBUG_TOOLS_ON=False' :
				lines[lineindex] = 'DEBUG_TOOLS_ON = True\n'
				msg = '调试工具开'
				break
		with open(configpath, 'w', encoding='utf-8') as f:
			f.write(''.join(lines))
	
	return JsonResponse(pkg(code=0,msg=msg),safe=False)


@csrf_exempt
def varSqltest(request):
	print(request.POST)
	scheme = request.POST.get('scheme')
	scheme = '全局' if scheme=='' else scheme
	sql = request.POST.get('sql')
	plan = request.POST.get('plan')
	if plan == '' or plan is None:
		plan = '{}'
	state, data,msg = simple_compute(sql,plan,scheme)
	code = 1 if state != 'success' else 0
	return JsonResponse({'code': code,'msg':msg})


def simple_replace_var(str_,plan,scheme):
	print('替换',str_,plan,scheme)
	try:
		old = str_
		varnames = re.findall('{{(.*?)}}', str_)
		for varname in varnames:
			try:
				with connection.cursor() as cursor:
					sql = '''SELECT v.gain,v.`value` FROM `manager_tag` t , manager_variable v
					where  v.`key`='%s' and v.id = t.var_id  and planids like '%s' '''%(varname,'%{}%'.format(plan))
					logger.info('变量查询sql=>',sql)
					cursor.execute(sql)
					rows = cursor.fetchall()
					if len(rows)>1:
						raise Exception('变量[%s]替换异常,可能该计划下有多个相同的变量键名，请检查' % varname)
					elif len(rows)==0:
						raise Exception('该计划下没有匹配到变量[%s],请检查'%varname)
					else:
						gain = rows[0][0]
						value = rows[0][1]
						print(value, gain)
						if len(gain) == 0:
							info = '变量{},{}'.format(varname,value)
							state, res = simple_replace_var(value, plan, scheme)
						elif len(value) == 0:
							state, res, msg = simple_compute(gain, plan, scheme)
						if state != 'success':
							return state, msg
			except Exception as e:
				logger.error(e)
				state = 'fail'
				return 'fail',str(e)
			old = old.replace('{{%s}}' % varname, str(res), 1)
		return ('success', old)
	except Exception as e:
		logger.info(traceback.format_exc())
		return ('error', '字符串[%s]变量替换异常[%s] 请检查包含变量是否已配置' % (str_, traceback.format_exc()))


def simple_compute(gain, plan, scheme):
	if _is_function_call(gain):
		return 'fail','','变量获取暂时支持sql方式'
		# flag = Fu.tzm_compute(gain, '(.*?)\((.*?)\)')
		# ms = list(Function.objects.filter(flag=flag))
		# functionid = None
		# if len(ms) == 0:
		# 	pass
		# elif len(ms) == 1:
		# 	functionid = ms[0].id
		# else:
		# 	functionid = ms[0].id
		# a = re.findall('(.*?)\((.*?)\)', gain)
		# methodname = a[0][0]
		# call_method_params = a[0][1].split(',')
		# if functionid is None:
		# 	state = 'fail'
		# 	msg = '没查到匹配函数请先定义[%s,%s]' % (gain, flag)
		# else:
		# 	f = None
		# 	builtinmethods = [x.name for x in getbuiltin()]
		# 	builtin = (methodname in builtinmethods)
		#
		# 	try:
		# 		f = Function.objects.get(id=functionid)
		# 	except:
		# 		pass
		# 	call_method_params = [x for x in call_method_params if x]
		# 	call_str = '%s(%s)' % (methodname, ','.join(call_method_params))
		# 	state, res = simple_replace_var(call_str,plan,scheme)
		# 	if state is not 'success':
		# 		return state,'',res
		# 	state,res =Fu.call(f, call_str, builtin=builtin)
		# 	return state,res,'' if state == 'success' else state,'',res
	else:
		state, gain = simple_replace_var(gain, plan,scheme)
		if state != 'success':
			return state, '',gain
		op = Mysqloper()
		return op.db_exec_test(gain, scheme)
