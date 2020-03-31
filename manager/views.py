from django.db import connection
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import HttpResponse, JsonResponse

from django.db.models import Q
from manager.models import *

from django.conf import settings
from login.models import *
from .core import *
from .invoker import *
from . import cm
from .context import querytestdata, gettestdatastep, mounttestdata, gettestdataparams, queryafteradd as qa,queryafterdel as qd, queryafteredit as qe, queryaftercopy as qc
import json ,operator, xlrd, base64, traceback
from .pa import MessageParser

# # Create your views here.

@csrf_exempt
def index(request):
	if request.session.get('is_login', None):
		return render(request, 'manager/start.html', locals())
	
	else:
		return redirect("/account/login/")


def help(request):
	# return render(request, 'manager/help.html')
	return redirect(settings.HELP_DOC_URL)


@csrf_exempt
def testjson(request):
	return HttpResponse("{'a':1}")


@csrf_exempt
def recvdata(request):
	data = request.POST
	print(data)
	# case=json.loads(jsonstr)
	# proxy.Q.push(case)
	print('入队列=>')
	print(data)
	print("*" * 100)


"""
数据迁移
"""


@csrf_exempt
def datamove(request):
	kind='datamovein'
	return render(request, 'manager/datamove.html',locals())


@csrf_exempt
def uploadfile(request):
	kind='persionfile'
	return render(request, 'manager/myspace.html',locals())


@csrf_exempt
def upload(request):

	filemap=dict()
	filenames=[]
	content_list = []
	
	files = request.FILES.getlist('file_data')
	for file in files:
		for chunk in file.chunks():
			print('上传文件名称=>',file.name)
			#content_list.append(chunk)
			filemap[file.name]=chunk
	
	callername = request.session.get('username')
	kind = request.POST.get('kind')

	print('kind=>',kind)
	content_type = request.POST.get('content_type')
	
	if kind == 'datamovein':
		
		taskid = EncryptUtils.md5_encrypt(str(datetime.datetime.now()))
		
		t = Transformer(callername, filemap.values(), content_type, taskid)
		
		res = t.transform()
		# print('res=>',res)
		
		if res[0] == 'success':
			# print('flag1_1')
			return JsonResponse(simplejson(code=0, msg='excel数据迁移完成 迁移ID=%s' % taskid), safe=False)
		else:
			# print('flag1_2')
			return JsonResponse(simplejson(code=2, msg='excel数据迁移失败[%s] 迁移ID=%s' % (res[1], taskid)), safe=False)
	
	elif kind == 'dataimport':
		d = DataMove()
		productid = request.POST.get('productid').split('_')[1]
		
		res = d.import_plan(productid, filemap.values(), request.session.get('username'))
		if res[0] == 'success':
			return JsonResponse(simplejson(code=0, msg='数据导入完成'), safe=False)
		else:
			return JsonResponse(simplejson(code=2, msg='数据导入失败[%s]' % res[1]), safe=False)
	elif kind=='personfile':
		status,msg=upload_personal_file(filemap, request.session.get('username'))
		if status is 'success':
			return JsonResponse(simplejson(code=0, msg='文件上传完成'), safe=False)
		else:
			return JsonResponse(simplejson(code=3, msg='文件上传异常'), safe=False)


		return JsonResponse(simplejson(code=0,msg='文件上传成功'),safe=False)
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
	# print('res[0]=>',res[0])
	if res[0] is 'success':
		# print('equals')
		
		response = HttpResponse(str(res[1]))
		response['content-type'] = 'application/json'
		response['Content-Disposition'] = 'attachment;filename=plan_%s.ME2' % flag
		# response.write(str(res[1]))
		# response=FileResponse(res[1],as_attachment=True,filename='plan_%s.json'%flag)
		return response
	else:
		print('导出失败:', res[1])
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
	print("searchvalue=>", searchvalue)
	queryschemevalue = request.GET.get('querySchemeValue')
	queryschemevalue = queryschemevalue if queryschemevalue not in [None, ''] else ''
	print("SchemeValue=>", queryschemevalue)
	res = None
	# if searchvalue:
	# 	print("变量查询条件=>")
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
		print(traceback.format_exc())
		code = 1
		msg = '添加异常'
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def delcon(request):
	id_ = request.POST.get('ids')
	# print('ids=>',id_)
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
		print("id=>", id_)
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
		code = 1
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


def getplan(id, kind):
	print('get', id, kind)
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
			print(traceback.format_exc())
			code = 4
			msg = '查询数据库列表信息异常'
			return JsonResponse(simplejson(code=code, msg=msg), safe=False)
	else:
		try:
			if scheme != '':
				res = list(DBCon.objects.filter(scheme=scheme).annotate(name=F('description')).values('name'))
				print(res)
			elif id != '' and id is not None:
				dbscheme = getplan(id.split('_')[1], id.split('_')[0])
				res = list(
					DBCon.objects.filter(scheme=dbscheme).annotate(name=F('description')).values('name'))
				print('...', res)
		except:
			print(traceback.format_exc())
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
		print(error)
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
			print(s)
	return JsonResponse({'code': code, 'msg': s})


def dbconRepeatCheck(dbids, copyschemevalue, action):
	print(dbids, copyschemevalue, action)
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
	return render(request, 'manager/varbak.html')


@csrf_exempt
def queryonevar(request):
	code = 0
	msg = ''
	res = None
	try:
		res = Variable.objects.get(id=request.POST.get('id'))
		tag = Tag.objects.values('planids', 'customize').get(var=res)
		print(tag['customize'])
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
		print(traceback.format_exc())
		code = 1
		msg = '查询异常[%s]' % traceback.format_exc()
		return JsonResponse({'code': code, 'msg': msg})


@csrf_exempt
def queryvar(request):
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
	print(strtag)
	
	bindplan = request.POST.get('bindplan') if request.POST.get('bindplan') != '' else ''
	bindstr = '%","' + bindplan + '"]%' if bindplan != '' else '%%'
	userid = userid if userid != '0' else str(User.objects.values('id').get(name=request.session.get('username'))['id'])
	print("searchvalue=>", searchvalue)
	
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


# searchvalue = request.POST.get('searchvalue')
# userid = request.POST.get('userid')
# tags= request.POST.get('tags')
# tags = tags if tags!='0' else ''
# userid = userid if userid != '0' else str(User.objects.values('id').get(name=request.session.get('username'))['id'])
# print("searchvalue=>", searchvalue)
# if (len(searchvalue) | len(userid)) and userid != '-1':
# 	print("变量查询条件=>")
# 	res = list(Variable.objects.filter(Q(author_id=userid) & (
# 			Q(description__icontains=searchvalue) | Q(key__icontains=searchvalue) | Q(
# 		value__icontains=searchvalue) | Q(
# 		gain__icontains=searchvalue)) & Q(tag__contains=tags)))
# else:
# 	res = list(Variable.objects.all())
# print(res)
# limit = request.POST.get('limit')
# page = request.POST.get('page')
# # print("res old size=>",len(res))
# res, total = getpagedata(res, page, limit)
# jsonstr = json.dumps(res, cls=VarEncoder, total=total)
# return JsonResponse(jsonstr, safe=False)


@csrf_exempt
def delvar(request):
	id_ = request.POST.get('ids')
	# print('ids=>',id_)
	ids = id_.split(',')
	code = 0
	msg = ''
	try:
		for i in ids:
			Variable.objects.get(id=i).delete()
		msg = '删除成功'
	except:
		code = 1
		msg = "删除失败[%s]" % traceback.format_exc()
	
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def editvar(request):
	print("===============editvar=========================================================")
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
		print(traceback.format_exc())
		code = 1
		msg = "编辑失败[%s]" % traceback.format_exc()
	
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


def varRepeatCheck(key, bindplans, editid=0):
	# 校验重复：同一个key只能最多只能有一个全局变量：isglobal=1;可以有多个绑定了计划的变量，其中绑定的计划不能有重复项
	print(key, bindplans)
	bindplans = json.loads(bindplans)
	state = '变量重复校验出错！'
	try:
		if editid != 0:
			vars = Variable.objects.filter(key=key).exclude(id=editid)
		else:
			vars = Variable.objects.filter(key=key)
		print(vars)
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
							print('没有绑定计划的变量,有全局变量;')
							state = ''
				state = "变量已经绑定过计划：<br>%s" % (str) if str != '' else ''
		
		else:
			state = ''
	except:
		print(traceback.format_exc())
		state = traceback.format_exc()
	finally:
		print(state)
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
		print(traceback.format_exc())
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
	print(varids, bindplans)
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
				tag.customize = Tag.objects.get(var=var).customize
				tag.planids = bindplans
				tag.save()
			except:
				msg = traceback.format_exc()
				print(traceback.format_exc())
	elif action == '0':
		for varid in varids:
			key = Variable.objects.get(id=varid).key
			state = varRepeatCheck(key, bindplans, varid)
			if state != '':
				return JsonResponse({'code': 1, 'msg': state})
			try:
				tag = Tag.objects.get(var=Variable.objects.get(id=varid))
				tag.planids = bindplans
				tag.save()
			except:
				msg = traceback.format_exc()
				print(traceback.format_exc())
	print(msg)
	return JsonResponse({'code': code, 'msg': msg})


"""
接口相关
"""


@csrf_exempt
def itf(request):
	return render(request, 'manager/interface.html')


@csrf_exempt
def queryitf(request):
	searchvalue = request.GET.get('searchvalue')
	print("searchvalue=>", searchvalue)
	res = None
	if searchvalue:
		print("变量查询条件=>")
		res = list(Interface.objects.filter(
			Q(description__icontains=searchvalue) | Q(key__icontains=searchvalue) | Q(value__icontains=searchvalue)))
	else:
		res = list(Interface.objects.all())
	
	limit = request.GET.get('limit')
	page = request.GET.get('page')
	res, total = getpagedata(res, page, limit)
	jsonstr = json.dumps(res, cls=ItfEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)


@csrf_exempt
def delitf(request):
	id_ = request.POST.get('id')
	code = 0
	msg = ''
	try:
		Interface.objects.get(id=id_).delete()
	except:
		code = 1
		msg = "删除失败"
	
	finally:
		return JsonResponse(simplejson(code=code, msg=""))


@csrf_exempt
def edititf(request):
	id_ = request.POST.get('id')
	code = 0
	msg = ''
	try:
		Interface.objects.get(id=id_).update()
	except:
		code = 1
		msg = "编辑失败"
	
	finally:
		return JsonResponse(simplejson(code=code, msg=""))


@csrf_exempt
def additf(request):
	code = 0
	msg = ''
	try:
		itf = Interface()
		itf.author = request.POST.get('author')
		itf.name = request.POST.get('name')
		itf.headers = request.POST.get('headers')
		itf.url = request.POST.get("url")
		itf.method = request.POST.get("method")
		itf.content_type = request.POST.get("content_type")
		itf.version = request.POST.get("version")
		itf.body = request.POST.get("body")
		
		itf.save()
	except:
		code = 1
		msg = '新增失败'
	return JsonResponse(simplejson(code=code, msg=""))


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


@csrf_exempt
def querycase(request):
	searchvalue = request.GET.get('searchvalue')
	print("searchvalue=>", searchvalue)
	res = None
	if searchvalue:
		print("变量查询条件=>")
		res = list(Case.objects.filter(description__icontains=searchvalue))
	else:
		res = list(Case.objects.all())
	
	limit = request.GET.get('limit')
	page = request.GET.get('page')
	res, total = getpagedata(res, page, limit)
	
	jsonstr = json.dumps(res, cls=CaseEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)


@csrf_exempt
def delcase(request):
	id_ = request.POST.get('ids')
	code = 0
	msg = ''
	ids = id_.split(',')
	try:
		for i in ids:
			case = Case.objects.get(id=i)
			if len(list(case.steps.all())) > 0:
				return JsonResponse(pkg(code=2, msg='已挂载测试步骤'), safe=False)
			case.delete()
		return JsonResponse(pkg(code=0, msg='删除成功'), safe=False)
	except:
		return JsonResponse(pkg(code=4, msg='删除异常[%s]' % traceback.format_exc()), safe=False)


@csrf_exempt
def editcase(request):
	id_ = request.POST.get('id')
	code = 0
	msg = ''
	try:
		case = Case.objects.get(id=id_)
		case.description = request.POST.get('description')
		case.db_id = request.POST.get('dbid')
		case.save()
		msg = '编辑成功'
	except:
		code = 1
		msg = "编辑失败[%s]" % traceback.format_exc()
	
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def addcase(request):
	code = 0
	msg = ''
	try:
		case = Case()
		case.author = User.objects.get(name=request.session.get('username', None))
		case.description = request.POST.get('description')
		case.db_id = request.POST.get('dbid')
		
		case.save()
		msg = '新增成功'
	except Exception as e:
		code = 1
		msg = '新增失败:' + str(e)
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


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
			
			print('接收文件=>', myFile.name)
			# print('tmp=>',myFile.temporary_file_path())
			if myFile.name.__contains__('Config'):
				print('包含=>', myFile.name)
				FILE_CHECK = True
				config_wb = xlrd.open_workbook(filename=None, file_contents=myFile.read())
			else:
				print('部包含=>', myFile.name)
				data_wb = xlrd.open_workbook(filename=None, file_contents=myFile.read())
		
		print('file_check=>%s file_count=>%s' % (FILE_CHECK, FILE_COUNT))
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
	
	if getRunningInfo(callername, planid, 'isrunning') == '1':
		return JsonResponse(simplejson(code=1, msg="调用失败，任务正在运行中，稍后再试！"), safe=False)
	
	print('调用方=>', callername)
	print('调用计划=>', planid)
	print('调用数据连接方案=>',dbscheme)
	runplans(callername, taskid, [planid], is_verify,None,dbscheme)
	return JsonResponse(simplejson(code=0, msg="调用成功,使用DB配置:[%s]"%dbscheme, taskid=taskid), safe=False)


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
		print(traceback.format_exc())
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
def queryplan(request):
	searchvalue = request.GET.get('searchvalue')
	print("searchvalue=>", searchvalue)
	res = None
	if searchvalue:
		print("变量查询条件=>")
		res = list(Plan.objects.filter(Q(description__icontains=searchvalue) | Q(run_type__icontains=searchvalue)))
	else:
		username = request.session.get('username', None)
		print(username)
		author = User.objects.get(name=username)
		
		res = list(Plan.objects.filter(author=author))
	
	limit = request.GET.get('limit')
	page = request.GET.get('page')
	res, total = getpagedata(res, page, limit)
	
	jsonstr = json.dumps(res, cls=PlanEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)


@csrf_exempt
def delplan(request):
	id_ = request.POST.get('ids')
	code = 0
	msg = ''
	ids = id_.split(',')
	try:
		for i in ids:
			i = int(i)
			plan = Plan.objects.get(id=i)
			if len(list(plan.cases.all())) > 0:
				return JsonResponse(pkg(code=2, msg='已挂载测试用例'), safe=False)
			plan.delete()
	
	except:
		print(traceback.format_exc())
		code = 1
		return JsonResponse(pkg(code=code, msg=msg), safe=False)
	
	finally:
		return JsonResponse(pkg(code=code, msg=msg), safe=False)


@csrf_exempt
def editplan(request):
	id_ = request.POST.get('id')
	code = 0
	msg = ''
	try:
		plan = Plan.objects.get(id=id_)
		plan.description = request.POST.get('description')
		plan.db_id = request.POST.get('dbid')
		print('description=>', plan.description)
		plan.run_type = request.POST.get('run_type')
		plan.save()
		msg = '编辑成功'
	except:
		code = 1
		msg = "编辑失败[%s]" % traceback.format_exc()
	
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def addplan(request):
	code = 0
	msg = ''
	try:
		plan = Plan()
		plan.description = request.POST.get('description')
		plan.db_id = request.POST.get('dbid')
		plan.author = User.objects.get(name=request.session.get('username', None))
		plan.run_type = request.POST.get('run_type')
		
		plan.save()
		
		if plan.run_type == '定时运行':
			config = request.POST.get('config')
			crontab = Crontab()
			crontab.taskid = gettaskid(plan.__str__())
			crontab.value = config
			# crontab.status='close'
			crontab.author = plan.author
			crontab.plan = plan
			crontab.save()
		
		msg = '添加[%s]成功' % plan.description
	except Exception as e:
		code = 1
		msg = '新增失败[%s]' % str(e)
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


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
	
	# print(detail)
	
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
		if getRunningInfo(username, planid, 'isrunning') == '1':
			return JsonResponse(simplejson(code=1, msg="任务已在运行，请稍后！"), safe=False)
		
		taskid = gettaskid(plan.__str__())
		is_verify = request.POST.get('is_verify')
		runplans(username, taskid, list_, is_verify)
	return JsonResponse(simplejson(code=0, msg="你的任务正在运行中", taskid=taskid), safe=False)


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


"""
运行计划结果相关接口
"""


# def result(request):
# 	return render(request, 'manager/result.html')

# def queryresult(request):
# 	searchvalue=request.GET.get('searchvalue')
# 	print("searchvalue=>",searchvalue)
# 	res=None
# 	if searchvalue:
# 		print("变量查询条件=>")
# 		res=list(Result.objects.filter(Q(description=searchvalue)|Q(key=searchvalue)|Q(value=searchvalue)))
# 	else:
# 		res=list(Result.objects.all())

# 	jsonstr=json.dumps(res,cls=ResultEncoder)
# 	return JsonResponse(jsonstr,safe=False)


# def delresult(request):
# 	id_=request.POST.get('id')
# 	code=0
# 	msg=''
# 	try:
# 		Result.objects.get(id=id_).delete()
# 	except:
# 		code=1
# 		msg="删除失败"

# 	finally:
# 		return JsonResponse(simplejson(code=code,msg=""))


@csrf_exempt
def resultdetail(request):
	return render(request, 'manager/resultdetail.html')


@csrf_exempt
def queryresultdetail(request):
	searchvalue = request.GET.get('searchvalue')
	print("searchvalue=>", searchvalue)
	res = None
	if searchvalue:
		print("变量查询条件=>")
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
	print("searchvalue=>", searchvalue)
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
		print(traceback.format_exc())
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
		# print("函数名称=>",f.name)
		# print("tbody=>",tbody)
		f.body = base64.b64encode(tbody.encode('utf-8')).decode()
		# f.flag=Fu.flag(f.body)
		f.flag = Fu.tzm_compute(tbody, "def\s+(.*?)\((.*?)\):")
		f.save()
		msg = '添加成功'
	except Exception as e:
		print(e)
		code = 1
		msg = '添加失败'
	# traceback.print_exc(e)
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
		
		print('查函数下拉信息=>', data)
		
		return JsonResponse(simplejson(code=0, msg='操作成功', data=data), safe=False)
	
	except:
		print(traceback.format_exc())
		code = 4
		msg = '查询函数下拉框信息异常'
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


"""
测试步骤相关
"""


def step(request):
	return render(request, 'manager/step.html')


@csrf_exempt
def addstep(request):
	# print("addstepd")
	code = 0
	msg = ''
	try:
		step_type = request.POST.get('step_type')
		description = request.POST.get('description')
		headers = request.POST.get('headers')
		body = request.POST.get("body")
		url = request.POST.get('url')
		method = request.POST.get('method')
		content_type = request.POST.get('content_type')
		db_check = request.POST.get('db_check')
		itf_check = request.POST.get('itf_check')
		print('itf_check=>', itf_check)
		tmp = request.POST.get('tmp')
		author = request.session.get('username')
		print("author=>", author)
		# tagname=request.POST.get('tag')
		# print("tag=>",tagname)
		
		businessdata = request.POST.get('business_data')
		
		print('businessdata=>', type(businessdata), businessdata)
		dbid = request.POST.get('dbid')
		# businsesstitle=getbusinesstitle(eval(businessdata))
		
		step = Step()
		step.step_type = step_type
		step.description = description
		step.headers = headers
		# step.body=body
		step.url = url
		step.method = method
		step.content_type = content_type
		step.db_check = db_check
		step.itf_check = itf_check
		step.temp = tmp
		step.author = User.objects.get(name=author)
		step.db_id = dbid
		# step.businesstitle=businsesstitle
		step.save()
		mounttestdata(author, step.id)
		
		# if tagname is not None and len(tagname.strip())>0:
		# 	step.tag_id=Tag.objects.get(name=tagname).id
		
		if 'function' == step.step_type:
			step.body = body
			
			# funcname=re.findall("(.*?)\(.*?\)", step.body)[0]
			funcname = step.body.strip()
			builtinmethods = [x.name for x in getbuiltin()]
			builtin = (funcname in builtinmethods)
			
			if builtin is False:
				# flag=Fu.tzm_compute(step.body,'(.*?)\((.*?)\)')
				businessdatainst = None
				businessinfo = list(step.businessdatainfo.all())
				if len(businessinfo) > 0:
					businessdatainst = businessinfo[0]
				
				status, res = gettestdataparams(businessdatainst.id)
				print('gettestdataparams=>%s' % res)
				if status is not 'success':
					return JsonResponse(simplejson(code=3, msg=str(res)))
				
				params = ','.join(res)
				
				call_str = '%s(%s)' % (funcname, params)
				flag = Fu.tzm_compute(call_str, '(.*?)\((.*?)\)')
				funcs = list(Function.objects.filter(flag=flag))
				if len(funcs) > 1:
					return JsonResponse(simplejson(code=44, msg='找到多个匹配的自定义函数 请检查'))
				
				related_id = funcs[0].id
				step.related_id = related_id
		
		step.save()
		msg = '添加测试步骤成功'
	# print('flag2')
	except Exception as e:
		print(traceback.format_exc())
		code = 2
		msg = "添加失败:" + str(e)
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def delstep(request):
	'''
	'''
	id_ = request.POST.get('ids')
	code = 0
	msg = ''
	ids = id_.split(',')
	try:
		for i in ids:
			step = Step.objects.get(id=i)
			case_list = list(Case.objects.all())
			businessdatainfo = list(step.businessdatainfo.all())
			related_case_list = []
			for case in case_list:
				related_case_list = [case for sb in businessdatainfo if sb in [case.businessdatainfo.all()]]
			size = len(related_case_list)
			print('已关联用例数：', size)
			if size > 0:
				code = 2
				msg = '用例[%s]已关联该步骤 请先消除引用' % related_case_list[0].description
				break;
			else:
				##
				step.delete()
				msg = '删除成功'
	
	except Exception as e:
		print(traceback.print_exc(e))
		code = 1
		msg = "删除失败[%s]" % traceback.format_exc()
	
	finally:
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def editstep(request):
	id_ = request.POST.get('id')
	code = 0
	msg = ''
	try:
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
		author = User.objects.get(name=username)
		
		step = Step.objects.get(id=id_)
		
		step.step_type = step_type
		if step_type is None:
			step.step_type = 'function'
		step.description = description
		step.headers = headers
		step.body = body
		step.url = url
		step.method = method
		step.content_type = content_type
		
		step.temp = tmp
		step.db_id = dbid
		
		step.save()
		mounttestdata(username, step.id, trigger='edit')
		
		if 'function' == step.step_type:
			
			# funcname=re.findall("(.*?)\(.*?\)", step.body)[0]
			funcname = step.body.strip()
			builtinmethods = [x.name for x in getbuiltin()]
			builtin = (funcname in builtinmethods)
			
			if builtin is False:
				businessdatainst = None
				businessinfo = list(step.businessdatainfo.all())
				if len(businessinfo) > 0:
					businessdatainst = businessinfo[0]
				
				status, res = gettestdataparams(businessdatainst.id)
				if status is not 'success':
					return JsonResponse(simplejson(code=3, msg=str(res)))
				
				params = ','.join(res)
				calll_str = '%s(%s)' % (step.body.strip(), params)
				# print('callerstr=>',calll_str)
				# flag=Fu.tzm_compute(step.body,'(.*?)\((.*?)\)')
				flag = Fu.tzm_compute(calll_str, '(.*?)\((.*?)\)')
				funcs = list(Function.objects.filter(flag=flag))
				if len(funcs) > 1:
					return JsonResponse(simplejson(code=44, msg='找到多个匹配的自定义函数 请检查'))
				
				# print('fsize=>',len(funcs))
				related_id = funcs[0].id
				step.related_id = related_id
		
		step.save()
		msg = '编辑成功'
	
	except Exception as e:
		code = 4
		print(traceback.format_exc())
		msg = "编辑失败[%s]" % traceback.format_exc()
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


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
		print(traceback.format_exc())
		return JsonResponse(simplejson(code=3, msg='查询异常'), safe=False)


@csrf_exempt
def querystep(request):
	limit = request.GET.get('limit')
	page = request.GET.get('page')
	searchvalue = request.GET.get('searchvalue')
	main_id = request.POST.get("mainid")
	print("searchvalue=>", searchvalue)
	print("mainid=>", main_id)
	
	res = []
	# 1.有searchvalue 无mainid的查询
	
	# 2.有mainid 无searchvalue的子步骤查询
	
	# 3.searchvalue&mianid都没 返回all step
	
	# if searchvalue&len(searchvalue.strip())==0:
	# 	searchvalue=None
	
	if searchvalue and main_id is None:
		print("querystep 查询情况1")
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
		print("querystep 查询情况2")
		res = list(Case.objects.get(id=main_id).steps.all())
	
	
	
	elif main_id is None and not searchvalue:
		print("querystep 查询情况3")
		res = list(Step.objects.all())
	# res=list(BusinessData.objects.all())
	# res,total=getpagedata(res, page, limit)
	# jsonstr=json.dumps(res,cls=BusinessDataEncoder,total=total)
	# return JsonResponse(jsonstr,safe=False)
	else:
		# warnings.warn("querystep不支持这种情况..")
		pass
	
	print("查询结果：", res)
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
		
		print('获取计划[%s]邮件配置=>%s' % (plan.description, mail_config_id))
		
		if mail_config_id:
			config = MailConfig.objects.get(id=mail_config_id)
			jsonstr = json.dumps(config, cls=MailConfigEncoder)
			return JsonResponse(jsonstr, safe=True)
		else:
			jsonstr = json.dumps('', cls=MailConfigEncoder)
			return JsonResponse(jsonstr, safe=True)
	# return JsonResponse(simplejson(code=1,msg='计划[%s]还未关联邮件'%plan.description),safe=False)
	except:
		print(traceback.format_exc())
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
		print(traceback.format_exc())
		code = 1
		msg = '操作异常[%s]' % traceback.format_exc()
	
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def querymailconfig(request):
	searchvalue = request.GET.get('searchvalue')
	# print("searchvalue=>",searchvalue)
	res = None
	if searchvalue:
		print("变量查询条件=>")
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
		print(e)
		traceback.print_exc(e)
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
def queryafteradd(requests):
	"""
	返回添加step|case后的已选信息 如果follow_id无效则忽略
	"""
	
	try:
		res0 = {
			"code": 0,
			"msg": '',
			"data": None
		}
		main_id = int(requests.POST.get("main_id"))
		follow_ids = [int(x) for x in (requests.POST.get("follow_ids").split(','))]
		kind = requests.POST.get("kind")
		username = requests.session.get('username', None)
		print('follow_ids=>', follow_ids, type(follow_ids))
		
		# print("="*40,"调用queryafteradd接口======\nmain_id=%s\nfollow_ids=%s\nkind=%s"%(main_id,follow_ids,kind))
		if operator.eq(follow_ids, [-1]):
			print('只查询')
		
		else:
			# 做数据插入
			
			for follow_id in follow_ids:
				# print(main_id,follow_id,kind,username)f
				# 建立对应关系manager_plan_case&&manager_case_step&&order表  忽略重复添加
				
				_list = list(Order.objects.filter(main_id=main_id, follow_id=follow_id, kind=kind))
				if len(_list) > 0:
					warnmsg = "数据插入忽略 已存在main_id=%s follow_id=%s" % (main_id, follow_id)
					print(warnmsg)
					continue;
				else:
					
					# 验证follow_id
					if kind == 'step' and len(list(BusinessData.objects.filter(id=follow_id))) == 1:
						
						order = Order()
						order.main_id = main_id
						order.follow_id = follow_id
						order.kind = kind
						order.author = User.objects.get(name=username)
						order.save()
						
						case = Case.objects.get(id=main_id)
						step = BusinessData.objects.get(id=follow_id)
						# case.steps.add(step)
						case.businessdatainfo.add(step)
						case.save()
					
					elif kind == 'case' and len(list(Case.objects.filter(id=follow_id))) == 1:
						order = Order()
						order.main_id = main_id
						order.follow_id = follow_id
						order.kind = kind
						order.author = User.objects.get(name=username)
						order.save()
						
						plan = Plan.objects.get(id=main_id)
						case = Case.objects.get(id=follow_id)
						plan.cases.add(case)
						plan.save()
			
			##数据插入后重新生成序号
			genorder(kind, main_id)
		
		#
		_main_order = ordered(list(Order.objects.filter(main_id=main_id, kind=kind)))
		# print(_main_order)
		res = []
		for item in _main_order:
			# print("follow_id=>",item.follow_id)
			# desp=Step.objects.get(id=item.follow_id).description if kind=="step" else Case.objects.get(id=item.follow_id).description
			desp = None
			if kind == 'step':
				print('fff=>', item.follow_id)
				business = BusinessData.objects.get(id=item.follow_id)
				status, stepinst = gettestdatastep(item.follow_id)
				if status is not 'success':
					return JsonResponse(simplejson(code=3, msg=stepinst), safe=False)
				desp = "%s_%s" % (stepinst.description, business.businessname)
			
			else:
				desp = Case.objects.get(id=item.follow_id).description
			
			obj = {
				"id": item.follow_id,
				"description": desp,
				"order": Order.objects.get(main_id=main_id, follow_id=item.follow_id, kind=kind).value
			}
			res.append(obj)
		
		res0["data"] = res
		
		# print("="*40,"调用queryafteradd结束==")
		
		return JsonResponse(json.dumps(res0), safe=False)
	except Exception as e:
		print(traceback.format_exc())
		return JsonResponse(simplejson(code=4, msg='操作异常[%s]' % traceback.format_exc()), safe=False)


@csrf_exempt
def queryafterdel(requests):
	"""
	返回删除step|case后的已选信息 如果follow_id无效则忽略
	"""
	res0 = {
		"code": 0,
		"msg": '',
		"data": None
	}
	main_id = int(requests.POST.get("main_id"))
	follow_ids = [int(x) for x in requests.POST.get("follow_ids").split(',')]
	kind = requests.POST.get("kind")
	username = requests.session.get('username', None)
	author = User.objects.get(name=username)
	for follow_id in follow_ids:
		
		# print(main_id,follow_id,kind,username)
		# 消除对应关系manager_plan_case&&manager_case_step&&order表  忽略重复添加
		
		_list = list(Order.objects.filter(main_id=main_id, follow_id=follow_id, kind=kind))
		
		if len(_list) == 0:
			warnmsg = "order表数据不存在忽略操作 main_id=%s follow_id=%s" % (main_id, follow_id)
			print(warnmsg)
			continue
		
		else:
			
			if kind == 'step':
				if len(list(BusinessData.objects.filter(id=follow_id))) == 1:
					Order.objects.get(kind=kind, main_id=main_id, follow_id=follow_id).delete()
					case = Case.objects.get(id=main_id)
					step = BusinessData.objects.get(id=follow_id)
					case.businessdatainfo.remove(step)
					case.save()
				
				else:
					warnmsg = "step表数据不存在或多条忽略操作 main_id=%s follow_id=%s" % (main_id, follow_id)
					print(warnmsg)
					continue
			
			elif kind == 'case':
				if len(list(Case.objects.filter(id=follow_id))) == 1:
					Order.objects.get(kind=kind, main_id=main_id, follow_id=follow_id).delete()
					plan = Plan.objects.get(id=main_id)
					case = Case.objects.get(id=follow_id)
					plan.cases.remove(case)
					plan.save()
				else:
					warnmsg = "case表数据不存在或多条忽略操作 main_id=%s follow_id=%s" % (main_id, follow_id)
					print(warnmsg)
					continue
			
			##case 或plan重新生成执行序号
			genorder(kind, main_id)
	
	#
	_main_order = ordered(list(Order.objects.filter(main_id=main_id, kind=kind)))
	# print(_main_order)
	res = []
	for item in _main_order:
		# print("follow_id=>",item.follow_id)
		desp = None
		
		if kind == 'step':
			business = BusinessData.objects.get(id=item.follow_id)
			status, stepinst = gettestdatastep(business.id)
			if status is not 'success':
				return JsonResponse(simplejson(code=3, msg=stepinst), safe=False)
			
			desp = "%s_%s" % (stepinst.description, business.businessname)
		else:
			desp = Case.objects.get(id=item.follow_id).description
		
		obj = {
			"id": item.follow_id,
			"description": desp,
			"order": Order.objects.get(main_id=main_id, follow_id=item.follow_id, kind=kind).value
		}
		res.append(obj)
	
	res0["data"] = res
	
	return JsonResponse(json.dumps(res0), safe=False)


@csrf_exempt
def queryoneproduct(request):
	code = 0
	msg = ''
	res = None
	try:
		res = Product.objects.get(id=request.POST.get('id').split('_')[1])
		print('product=>', res)
	
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
		# print('loadpage')
		try:
			return render(request, "cm/%s.html" % page)
		except:
			print(traceback.format_exc())
			return JsonResponse(pkg(code=4, msg='%s' % traceback.format_exc()), safe=False)
	
	else:
		
		callstr = "cm.%s(request)" % (request.POST.get('action') or request.GET.get('action'))
		status = v = None
		try:
			# print('callstr=>',callstr)
			k = eval(callstr)
			print('k=>', k)
			status, v, data = k.get('status'), k.get('msg'), k.get('data')
			
			if status is not 'success':
				return JsonResponse(pkg(code=2, msg=str(v)), safe=False)
			else:
				
				if action == 'export':
					print('export %s' % v)
					flag = str(datetime.datetime.now()).split('.')[0]
					response = HttpResponse(str(v))
					response['content-type'] = 'application/json'
					response['Content-Disposition'] = 'attachment;filename=plan.ME2'
					return response
				
				return JsonResponse(pkg(code=0, msg=str(v), data=data), safe=False)
		
		except:
			print(traceback.format_exc())
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


@csrf_exempt
def changepos(requests):
	res0 = {
		"code": 0,
		"msg": '',
		"data": None
	}
	try:
		
		# print('KK'*100)
		
		move_kind = requests.POST.get('move_kind')
		main_id = requests.POST.get("main_id")
		follow_id = requests.POST.get("follow_id")
		kind = requests.POST.get("kind")
		username = requests.session.get('username', None)
		move = requests.POST.get("move")
		aid = requests.POST.get('aid')
		bid = requests.POST.get('bid')
		
		if 'swap' == move_kind:
			res = swap(kind, main_id, aid, bid)
			# print('swap结果=>',res)
			if res[0] is not 'success':
				raise RuntimeError(res[1])
		else:
			changepostion(kind, main_id, follow_id, move)
		
		_main_order = ordered(list(Order.objects.filter(main_id=main_id, kind=kind)))
		# print(_main_order)
		res = []
		for item in _main_order:
			# desp=BusinessData.objects.get(id=item.follow_id).businessname if kind=="step" else Case.objects.get(id=item.follow_id).description
			desp = None
			
			if kind == 'step':
				business = BusinessData.objects.get(id=item.follow_id)
				status, stepinst = gettestdatastep(business.id)
				if status is not 'success':
					return JsonResponse(simplejson(code=3, msg=stepinst), safe=False)
				
				desp = "%s_%s" % (stepinst.description, business.businessname)
			else:
				desp = Case.objects.get(id=item.follow_id).description
			
			obj = {
				"id": item.follow_id,
				"description": desp,
				"order": Order.objects.get(main_id=main_id, follow_id=item.follow_id, kind=kind).value
			}
			res.append(obj)
		
		res0["data"] = res
		res0['msg'] = '操作成功'
		
		return JsonResponse(json.dumps(res0), safe=False)
	except:
		error = traceback.format_exc()
		return JsonResponse(simplejson(code=4, msg='交换异常[%s]' % error), safe=False)


@csrf_exempt
def aftergroup(request):
	res0 = {
		"code": 0,
		"msg": '',
		"data": None
	}
	
	main_id = request.POST.get("main_id")
	follow_id = request.POST.get("follow_id")
	kind = request.POST.get("kind")
	
	genorder(kind, main_id, follow_id)
	
	_main_order = ordered(list(Order.objects.filter(main_id=main_id, kind=kind)))
	# print(_main_order)
	res = []
	for item in _main_order:
		# desp=BusinessData.objects.get(id=item.follow_id).businessdata if kind=="step" else Case.objects.get(id=item.follow_id).description
		desp = None
		
		if kind == 'step':
			business = BusinessData.objects.get(id=item.follow_id)
			status, stepinst = gettestdatastep(business.id)
			if status is not 'success':
				return JsonResponse(simplejson(code=3, msg=stepinst), safe=False)
			desp = "%s_%s" % (stepinst.description, business.businessname)
		else:
			desp = Case.objects.get(id=item.follow_id).description
		
		obj = {
			"id": item.follow_id,
			"description": desp,
			"order": Order.objects.get(main_id=main_id, follow_id=item.follow_id, kind=kind).value
		}
		res.append(obj)
	
	res0["data"] = res
	
	return JsonResponse(json.dumps(res0), safe=False)


'''
业务数据相关
'''


@csrf_exempt
def querybusinessdata(request):
	code, msg = 0, ''
	res = []
	try:
		
		callername = request.session.get('username')
		stepid = request.POST.get('stepid')
		flag = request.POST.get('flag')
		vids_ = request.POST.get('vids')
		vid = request.POST.get('vid')
		vids = []
		if vids_:
			vids = vids_.split(',')
		
		extdata = {
			'id': request.POST.get('id'),
			'businessname': request.POST.get('businessname'),
			'itf_check': request.POST.get('itf_check'),
			'db_check': request.POST.get('db_check'),
			'params': request.POST.get('params')
		}
		
		if flag == '0':
			res = querytestdata(callername, stepid)
		elif flag == '1':
			res = qa(callername, stepid, extdata)
		elif flag == '2':
			res = qe(callername, stepid, extdata)
		elif flag == '3':
			res = qd(callername, stepid, vids)
		elif flag == '4':
			res = qc(callername, stepid, vid)
		
		jsonstr = json.dumps(res, cls=BusinessDataEncoder)
		return JsonResponse(jsonstr, safe=False)
	except:
		error = traceback.format_exc()
		print(error)
		code = 4
		msg = '操作异常[%s]' % error
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def queryonebusiness(request):
	code = 0
	msg = ''
	try:
		callername = request.session.get('username')
		# vid = request.POST.get('vid').split('_')[1]
		# business = BusinessData.objects.get(id=vid)
		# print('business=>', business)
		# jsonstr = json.dumps(business, cls=BusinessDataEncoder)
		sql = '''
		SELECT b.id,count,businessname,itf_check,db_check,params,preposition,postposition,value as weight,parser_id,parser_check
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


@csrf_exempt
def queryonebusinessdata(request):
	code = 0
	msg = ''
	res = None
	try:
		callername = request.session.get('username')
		stepid = request.POST.get('stepid')
		vid = request.POST.get('vid')
		res = querytestdata(callername, stepid, trigger='detail')
		t = [r for r in res if str(r.id) == str(vid)]
		if len(t) > 0:
			t = t[0]
		else:
			return JsonResponse(simplejson(code=3, msg='查询失败 缓存里没找到id=%s对应测试数据' % vid), safe=False)
		
		jsonstr = json.dumps(t, cls=BusinessDataEncoder)
		return JsonResponse(jsonstr, safe=False)
	except:
		code = 1
		msg = '查询异常[%s]' % traceback.format_exc()
		return JsonResponse(simplejson(code=4, msg=msg), safe=False)


@csrf_exempt
def querybusinessdatalist(request):
	code, msg = 0, ''
	try:
		res = list(BusinessData.objects.all())
		
		jsonstr = json.dumps(res, cls=BusinessDataEncoder)
		# print('json=>',jsonstr)
		return JsonResponse(jsonstr, safe=False)
	except:
		err = (traceback.format_exc())
		print(err)
		return JsonResponse(simplejson(code=4, msg='查询异常[%s]' % err))


@csrf_exempt
def querytreelist(request):
	from .cm import getchild, get_search_match
	datanode = []
	
	def _get_pid_data(idx, type, data):
		
		if type == 'product':
			
			product = Product.objects.get(id=idx)
			print('product=>', product)
			plans = cm.getchild('product_plan', idx)
			print('plans=>', plans)
			for plan in plans:
				data.append({
					
					'id': 'plan_%s' % plan.id,
					'pId': 'product_%s' % product.id,
					'name': plan.description,
					'type': 'plan',
					'textIcon': 'fa fa-product-hunt',
					# 'open':True
				})
			
			return data
		
		elif type == 'plan':
			plan = Plan.objects.get(id=idx)
			cases = cm.getchild('plan_case', idx)
			print('cases=>', cases)
			for case in cases:
				print('case=>', case)
				casename = case.description
				if case.count in (0, '0'):
					casename = '<s>%s</s>' % casename
				data.append({
					'id': 'case_%s' % case.id,
					'pId': 'plan_%s' % plan.id,
					'name': casename,
					'type': 'case',
					'textIcon': 'fa fa-folder',
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
					'textIcon': 'fa fa-file-o',
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
					'textIcon': 'fa fa-folder',
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
					'textIcon': 'fa fa-leaf',
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
		print('cur d=>', datanode)
	elif searchvalue:
		datanode = get_search_match(searchvalue)
	
	else:
		print('query id is None')
		
		datanode.append({'id': -1, 'name': '产品池', 'type': 'root', 'textIcon': 'fa fa-pinterest-p', 'open': True})
		productlist = list(Product.objects.all())
		for product in productlist:
			datanode.append({
				'id': 'product_%s' % product.id,
				'pId': -1,
				'name': product.description,
				'type': 'product',
				'textIcon': 'fa fa-home'
			})
	
	##
	
	print('query tree result=>%s' % datanode)
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
	data=[]
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
		print('tag列表：', namelist)
		data = [{'id': 0, 'name': '全部标记'}]
		for m, n in enumerate(namelist):
			data.append({'id': str(m + 1) + '_' + n, 'name': n})
	except:
		print(traceback.format_exc())
		print('==获取标签列表异常')
	finally:
		return JsonResponse(pkg(code=0, data=data))


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
	print(ids)
	print(tags)
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
	p=MessageParser.query_template_common(request.POST.get('tid'))
	return JsonResponse(p,safe=False)


	
@csrf_exempt
def querytemplatelist(request):
	return JsonResponse(MessageParser.query_template_name_list(),safe=False)


@csrf_exempt
def addtemplate(request):
	pa=get_params(request)
	pa['author']=User.objects.get(name=request.session.get('username'))
	p=MessageParser.add_template(**pa)
	return JsonResponse(p,safe=False)


@csrf_exempt

def deltemplate(request):
	return JsonResponse(MessageParser.del_template(request.POST.get('ids')),safe=False)


@csrf_exempt
def edittemplate(request):
	return JsonResponse(MessageParser.edit_template(**get_params(request)),safe=False)

@csrf_exempt
def querytemplate(request):
	searchvalue = request.GET.get('searchvalue')
	print("searchvalue=>", searchvalue)

	if searchvalue:
		print("变量查询条件=>")
		res = list(Template.objects.filter(name__icontains=searchvalue))
	else:
		res = list(Template.objects.all())

	limit = request.GET.get('limit')
	page = request.GET.get('page')
	# print("res old size=>",len(res))
	res, total = getpagedata(res, page, limit)
	jsonstr = json.dumps(res, cls=TemplateEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)

def templatefield(request):
	tid=request.GET.get('tid')
	is_sort_display=''
	is_start_display=''
	kind=Template.objects.get(id=tid).kind
	if kind=='length':
		is_sort_display='none'

	else:
		is_start_display='none'

	print('sort',is_sort_display)
	print('start',is_start_display)

	return render(request, 'manager/templatefield.html',locals())


@csrf_exempt
def querytemplatefield(request):
	return JsonResponse(MessageParser.query_template_field(**get_params(request)),safe=False)


@csrf_exempt
def addtemplatefield(request):
	return JsonResponse(MessageParser.add_field(**get_params(request)),safe=False)

@csrf_exempt
def deltemplatefield(request):
	return JsonResponse(MessageParser.del_field(request.POST.get('ids')),safe=False)


@csrf_exempt
def edittemplatefield(request):
	return JsonResponse(MessageParser.edit_field(**get_params(request)),safe=False)

@csrf_exempt
def queryfielddetail(request):
	return JsonResponse(MessageParser.query_field_detail(request.POST.get('tid')),safe=False)


"""
测试接口
"""


def addsteprelation(request):
	cases = list(Case.objects.all())
	for case in cases:
		
		businesses = list(case.businessdatainfo.all())
		for business in businesses:
			status, step = gettestdatastep(business.id)
			if status is not 'success':
				continue;
			else:
				print('case_%s=>step_%s' % (case.id, step.id))
				case.steps.add(step)
	
	return JsonResponse(simplejson(code=0, msg='关联case&step ok.'), safe=False)


# def update(request):
# 	from .cm import getnextvalue
# 	##
# 	product=Product()
# 	product.description='默认产品'
# 	product.author=User.objects.get(name='admin')
# 	product.save()

# 	product_plan=[]
# 	plan_case=[]
# 	case_step=[]
# 	step_business=[]
# 	##
# 	print('==开始记录数据并删除老数据')
# 	lista=list(Order.objects.filter(kind='case'))
# 	listb=list(Order.objects.filter(kind='step'))
# 	for order in lista:
# 		plan_case.append((order.main_id,order.follow_id,order.value))
# 		product_plan.append((product.id,order.main_id,''))
# 		order.delete()

# 	for order in listb:
# 		steps=list(Step.objects.all())
# 		step=None
# 		for step0 in steps:
# 			bs=list(step0.businessdatainfo.all())
# 			for b in bs:
# 				if b.id==order.follow_id:
# 					step=step0
# 		if step is None:
# 			print('bussines->step异常 略过')
# 			continue;

# 		stepid=step.id
# 		case_step.append((order.main_id,stepid,''))
# 		step_business.append((stepid,order.follow_id,''))

# 		order.delete()

# 	print('==记录数据结束')

# 	###
# 	print('==开始构造新关联')
# 	for o in list(set(product_plan)):
# 		order=Order()
# 		order.main_id=o[0]
# 		order.follow_id=o[1]
# 		order.kind='product_plan'
# 		if o[2]=='':
# 			order.value=getnextvalue('product_plan', o[0])
# 		else:
# 			order.value=o[2]

# 		order.author=User.objects.get(name='admin')
# 		order.save()

# 	for o in list(set(plan_case)):
# 		order=Order()
# 		order.main_id=o[0]
# 		order.follow_id=o[1]
# 		order.kind='plan_case'
# 		if o[2]=='':
# 			order.value=getnextvalue('plan_case', o[0])
# 		else:
# 			order.value=o[2]

# 		order.author=User.objects.get(name='admin')
# 		order.save()


# 	for o in list(set(case_step)):
# 		order=Order()
# 		order.main_id=o[0]
# 		order.follow_id=o[1]
# 		order.kind='case_step'
# 		if o[2]=='':
# 			order.value=getnextvalue('case_step', o[0])
# 		else:
# 			order.value=o[2]

# 		order.author=User.objects.get(name='admin')
# 		order.save()


# 	for o in list(set(step_business)):
# 		order=Order()
# 		order.main_id=o[0]
# 		order.follow_id=o[1]
# 		order.kind='step_business'
# 		if o[2]=='':
# 			order.value=getnextvalue('step_business', o[0])
# 		else:
# 			order.value=o[2]

# 		order.author=User.objects.get(name='admin')
# 		order.save()


# 	print('==order表修改完成.')
# 	return JsonResponse(pkg(code=0))

def update(request):
	from .cm import getnextvalue
	import copy
	print('==开始更新==')
	planids = []
	delete = []
	cache = {}
	
	product_plan = {}
	plan_case = {}
	case_step = {}
	step_business = {}
	business_step = {}
	author = User.objects.get(name='admin')
	##
	product = Product()
	product.description = '默认产品'
	product.author = User.objects.get(name='admin')
	product.save()
	productid = product.id
	##
	lista = list(Order.objects.filter(kind='case'))
	listb = list(Order.objects.filter(kind='step'))
	for order in lista:
		##
		plist = list(Plan.objects.filter(id=order.main_id))
		alist = list(Case.objects.filter(id=order.follow_id))
		
		if len(plist) == 0 or len(alist) == 0:
			print('计划和用例检查失败 略过.[%s-%s]' % (order.main_id, order.follow_id))
			continue;
		
		##
		planid = order.main_id
		caseid = order.follow_id
		
		##复制实体数据
		plan = None
		try:
			plan = product_plan.get('%s_%s' % (productid, planid), None)
			if plan is None:
				plan = Plan.objects.get(id=planid)
				delete.append(copy.deepcopy(plan))
				
				plan.id = None
				plan.save()
				product_plan['%s_%s' % (productid, planid)] = plan
				
				order1 = Order()
				order1.kind = 'product_plan'
				order1.main_id = productid
				order1.follow_id = plan.id
				order1.author = author
				order1.value = getnextvalue('product_plan', order1.main_id)
				order1.save()
		# print('新建产品计划关联=>',order1)
		except:
			print('查询失败 略过 planid=>', order.main_id)
			continue;
		
		case = None
		case = plan_case.get('%s_%s' % (planid, caseid), None)
		
		if case is None:
			case = Case.objects.get(id=caseid)
			delete.append(copy.deepcopy(case))
			case.id = None
			case.save()
			plan_case['%s_%s' % (planid, caseid)] = case
			
			# 新建新的order关系
			order2 = Order()
			order2.main_id = plan.id
			order2.follow_id = case.id
			order2.kind = 'plan_case'
			order2.author = author
			order2.value = getnextvalue('plan_case', order2.main_id)
			order2.save()
	# print('建立计划用例关联=>',order2)
	###
	
	for order in listb:
		flag1 = 0
		flag2 = 0
		
		caseid = order.main_id
		businessid = order.follow_id
		stepid = None
		
		steps = list(Step.objects.all())
		for step0 in steps:
			buslist = list(step0.businessdatainfo.all())
			for business0 in buslist:
				if business0.id == businessid:
					stepid = step0.id
					break;
		##
		if stepid is None:
			print('不正确的order关系step[%s_%s] 略过' % (caseid, businessid))
			continue;
		
		# step=case_step.get('%s_%s'%(caseid,stepid),None)
		# if step is None:
		step = Step.objects.get(id=stepid)
		# print('获得老的step=>',step)
		delete.append(copy.deepcopy(step))
		step.id = None
		step.save()
		# print('获得新的step=>',step)
		print("新建步骤%s 来源=>[%s,%s]" % (step, order.main_id, order.follow_id))
		# case_step['%s_%s'%(case.id,stepid)]=step
		
		case_new_id = None
		
		for key in plan_case:
			if '_%s' % caseid in key:
				case_new_id = plan_case[key].id
		
		if case_new_id is None:
			print('case_new_id不合理 略过[%s->%s]' % (order.main_id, order.follow_id))
			continue;
		
		order3 = Order()
		order3.kind = 'case_step'
		order3.main_id = case_new_id
		order3.follow_id = step.id
		order3.author = author
		order3.value = getnextvalue('case_step', order3.main_id)
		order3.save()
		# print('建立用例步骤关联=>',order3)
		
		step_new_id = step.id
		# business=step_business.get('%s_%s'%(stepid,businessid), None)
		# if business is None:
		business = BusinessData.objects.get(id=businessid)
		
		business.id = None
		business.save()
		# print('新建测试点=>',business)
		step_business['%s_%s' % (stepid, businessid)] = business
		
		order4 = Order()
		order4.kind = 'step_business'
		order4.main_id = step_new_id
		order4.follow_id = business.id
		order4.author = author
		order4.value = getnextvalue('step_business', order4.main_id)
		order4.save()
	
	# print('建立步骤测试点关联=>',order4)
	
	##删除老的order关系
	print('==清除老的order关系')
	orderlist = list(Order.objects.filter(Q(kind='case') | Q(kind='step')))
	print('待删除数据=>', orderlist)
	for order in orderlist:
		order.delete()
	
	print('==清除完成.')
	
	##删除报告表
	reportlist = list(ResultDetail.objects.all())
	for report in reportlist:
		report.delete()
	print('==清除报告表')
	
	##删除包含关系
	print('==删除包含关系')
	planlist = list(Plan.objects.all())
	for plan in list(set(planlist)):
		plan.cases.clear()
	
	caselist = list(Case.objects.all())
	for case in list(set(caselist)):
		case.businessdatainfo.clear()
	
	steplist = list(Step.objects.all())
	for step in list(set(steplist)):
		step.businessdatainfo.clear()
	
	# 删除老的实体数据
	print('==清除老的实体数据')
	print('待删除数据=>', delete)
	for i in delete:
		try:
			i.delete()
		except:
			# print(traceback.format_exc())
			print('删除异常=>', i)
	
	print('==清除完成')
	
	print('==结束更新==')
	
	return JsonResponse(pkg(code=0))


def getfulltree(request):
	data = cm.get_full_tree()
	print(len(data))
	
	return JsonResponse(pkg(data=data))


def testgenorder(request):
	code = 0
	msg = ''
	
	genorder("case", 1, 1)
	return JsonResponse(simplejson(code=code, msg=""), safe=False)


def testaddtask(request):
	from .cron import Cron
	
	# scheduler.add_job(test, 'interval', seconds=3)
	username = request.session.get('username', None)
	Cron._addcrontab(runplans, 'interval', seconds=15, args=['tester', gettaskid(), ['1'], '定时'], id='')
	Cron._addcrontab(runplans, args=[username, crontaskid, [plan.id], '定时'], taskid=crontaskid, **cfg)
	# scheduler.add_job(runplans, 'interval', seconds=15,args=['tester',gettaskid(),['1'],'定时'],id='')
	
	return JsonResponse(simplejson(code=0, msg="fda", yy='dd'), safe=False)



def testtable(request):
	return render(request, 'manager/test-table.html')


def querytesttable(request):
	data = {}
	data['code'] = 0
	data['msg'] = ''
	# data['count']=5
	data['data'] = [{
		'id': 1,
		'businessname': '业务名称_1',
		'itf_check': '',
		'db_check': '',
		
	}]
	
	title = []
	title_map = {
		'itf_check': '接口校验',
		'db_check': '数据校验',
		'businessname': '业务名称'}
	
	findex = {}
	# findex['fixed']='left'
	findex['templet'] = '#index'
	findex['title'] = '序号'
	
	title.append(findex)
	
	for x in data.get('data')[0]:
		fobj = {}
		
		if x == 'id':
			fobj['hide'] = True
		fobj['field'] = x
		fobj['title'] = x
		fobj['edit'] = True
		
		if title_map.get(x):
			fobj['title'] = title_map.get(x)
		# fobj['width']='50px'
		title.append(fobj)
	
	fop = {}
	fop['fixed'] = 'right'
	fop['toolbar'] = '#business-toolbar'
	fop['title'] = '操作'
	title.append(fop)
	
	data['title'] = title
	return JsonResponse(data, safe=False)


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

'''
个人空间管理
'''
def _formatSize(bytes):
    try:
        bytes = float(bytes)
        kb = bytes / 1024
    except:
        print("传入的字节格式不对")
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
        print(err)


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
        print(err)
@csrf_exempt
def queryuserfile(request):
	'''
	返回个人文件列表
	'''
	searchvalue = request.GET.get('searchvalue')
	mfiles=list()
	username=request.session.get('username')
	userdir=os.path.join(os.path.dirname(__file__),'storage','private','File',username)
	if not os.path.exists(userdir):
		os.makedirs(userdir)
	files=os.listdir(userdir)
	print('files=>',files)
	for f in files:
		if searchvalue and not f.__contains__(searchvalue):
			continue;
		mfiles.append({
			'filename':f,
			'size':_getDocSize(os.path.join(userdir,f)),
			'createtime':time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(os.path.getctime(os.path.join(userdir,f))))
			})

	mfiles.sort(key=lambda e:e.get('createtime'),reverse=True)

	return JsonResponse({'code':0,'data':mfiles},safe=False)

@csrf_exempt
def delfiles(request):
	block_files=[]
	filenames=request.POST.get('filenames','')
	print('filenames=>',filenames)
	filenamelist=filenames.split(',')
	for filename in filenamelist:
		filepath=os.path.join(os.path.dirname(__file__),'storage','private','File',request.session.get('username'),filename)
		try:
			os.remove(filepath)
		except:
			block_files.append(filename)
			print(traceback.format_exc())

	if len(block_files)==0:
		return JsonResponse(pkg(code=0,msg='删除成功.'),safe=False)
	else:
		return JsonResponse(pkg(code=4,msg='删除失败[%s].'%(',').join(block_files)),safe=False)



@csrf_exempt
def edit_file_name(request):
	pass

