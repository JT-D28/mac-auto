import threading

import redis
from django.conf import settings
from django.core import serializers
from django.shortcuts import render
from django.utils.encoding import escape_uri_path

from ME2 import configs
from ME2.settings import logme
from manager.context import get_space_dir
from manager.models import *
from login.models import *
from manager import models as mm
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from manager.core import *
from django.db.models import Q

# Create your views here
from manager.operate.redisUtils import RedisUtils



@csrf_exempt
def login(request):
	if request.method=='GET':
		return render(request, 'login/login.html', locals())
	if configs.IS_CREATE_SUPERUSER:
		User.create_superuser(EncryptUtils.md5_encrypt(configs.SUPERUSER_PWD))
	
	username = request.POST.get('username')
	password = request.POST.get('password')
	try:
		user = User.objects.get(name=username)
		if EncryptUtils.md5_encrypt(password) == user.password:
			request.session.set_expiry(14400)
			request.session['is_login'] = True
			request.session['username'] = username
			# 初始化权限
			init_permission(request, user)
			return JsonResponse({'code': 0, 'msg': '登录成功'})
		else:
			message = '密码错误'
	except:
		print(traceback.format_exc())
		message = '用户不存在'
	return JsonResponse({'code': 1, 'msg': message})


def init_permission(request, user_obj):
	"""
	初始化用户权限, 写入session
	:param request:
	:param user_obj:
	:return:
	"""
	permission_item_list = user_obj.roles.values('permissions__id', 'permissions__url',
	                                             'permissions__title',
	                                             'permissions__menu_id',
	                                             'permissions__type').distinct()
	# print(permission_menu_list)
	permission_url_list = []  # 用户权限url列表，--> 用于中间件验证用户权限
	permission_menu_list = []  # 用户权限url所属菜单列表 [{"title":xxx, "url":xxx, "menu_id": xxx},{},]
	
	for item in permission_item_list:
		if item['permissions__url']:
			permission_url_list.append(item['permissions__url'])
		if item['permissions__menu_id']:
			temp = {"id": item['permissions__id'], "title": item['permissions__title'],
			        "url": item["permissions__url"],
			        "menu_id": item["permissions__menu_id"], 'type': item['permissions__type']}
			permission_menu_list.append(temp)
	
	permission_list = list(Permission.objects.values_list('url',flat=True).exclude(url=''))
	
	from django.conf import settings
	
	# 保存 权限菜单 和所有 菜单
	request.session[settings.SESSION_MENU_KEY] = {
		settings.ALL_PERMISSION_KEY: permission_list,
		settings.PERMISSION_MENU_KEY: permission_menu_list,
	}
	# 保存用户允许的接口权限列表
	request.session[settings.SESSION_PERMISSION_URL_KEY] = permission_url_list
	
	print('permission_url_list ------------------- ', permission_url_list)
	print('permission_menu_list ------------------- ', permission_menu_list)
	print('permission_list ------------------- ', permission_list)


def logout(request):
	username = request.session.get('username', '')
	print('用户【{}】退出登录'.format(username))
	clearRedisforUser(username)
	request.session.flush()
	return JsonResponse({'code': 0, 'msg': '退出成功'})


def clearRedisforUser(key):
	try:
		con = RedisUtils()
		con.delete(key)
		con.close()
	except:
		print('redis没有正常连接')


def queryaccount(request):
	searchvalue = request.GET.get('searchvalue')
	limit = int(request.GET.get('limit'))
	page = int(request.GET.get('page'))
	start = limit * (page - 1)
	end = limit * page - 1
	
	if searchvalue:
		users = User.objects.filter(Q(name__icontains=searchvalue) & ~Q(name__in=['定时任务', 'system']))
		total = users.count()
	else:
		users = User.objects.filter(~Q(name__in=['定时任务', 'system']))
		total = users.count()
	# print(total)
	usersList = users[start:end+1] if end < total else users[start:total+1]
	userSerializer = serializers.serialize('json', usersList)
	usersList = []
	for user in json.loads(userSerializer):
		one = user['fields']
		one['id'] = user['pk']
		roles = []
		for roleId in user['fields']['roles']:
			role = Role.objects.get(id=roleId)
			roles.append({'id': role.id, 'title': role.title})
		one['roles'] = roles
		usersList.append(one)
	return JsonResponse({'code': 0, 'data': usersList, 'total': total})


@csrf_exempt
def addaccount(request):
	code, msg = (0, '')
	name = request.POST.get('name')
	password = EncryptUtils.md5_encrypt(request.POST.get('password'))
	roles = request.POST.get('roles').split(',')
	try:
		has = User.objects.filter(name=name)
		if has:
			code, msg = (1, '存在该名称的用户，请更换')
		else:
			user = User(name=name, password=password)
			user.save()
			for roleId in roles:
				user.roles.add(roleId)
			msg = "用户%s新增成功" % name
			logme.info("用户【{}】新增成功".format(user.name))
	except:
		logme.error(traceback.format_exc())
		code, msg = (1, "添加异常%s" % traceback.format_exc())
	
	return JsonResponse({'code': code, 'msg': msg})


@csrf_exempt
def delaccount(request):
	code, msg = (0, '')
	try:
		ids = request.POST.get('ids').split(',')
		for id_ in ids:
			user = User.objects.get(id=id_)
			logme.error("用户【{}】删除成功".format(user.name))
			user.delete()
		msg = '操作成功'
	except:
		error = traceback.format_exc()
		code = 4
		msg = '操作异常[%s]' % error
		logme.error(msg)
	return JsonResponse({'code': code, 'msg': msg})


@csrf_exempt
def queryoneaccount(request):
	code, msg = 0, ''
	try:
		id_ = request.POST.get('uid')
		user = User.objects.get(id=id_)
		jsonstr = json.dumps(user, cls=UserEncoder)
		return JsonResponse(jsonstr, safe=False)
	except:
		msg = '操作异常[%s]' % traceback.format_exc()
		logme.error(msg)
		return JsonResponse(simplejson(code=4, msg=msg), safe=False)


@csrf_exempt
def editaccount(request):
	code, msg = (0, '')
	id = request.POST.get('id')
	name = request.POST.get('name')
	password = "".join(request.POST.get('password'))
	roles = request.POST.get('roles').split(',')
	
	try:
		has = User.objects.exclude(id=id).filter(name=name)
		if has:
			code, msg = (1, '存在该名称的用户，请更换')
		else:
			user = User.objects.get(id=id)
			user.name = name
			user.password = EncryptUtils.md5_encrypt(password) if password else user.password
			user.save()
			user.roles.clear()
			for roleId in roles:
				user.roles.add(roleId)
			msg = "用户%s修改成功" % name
			logme.info("用户【{}】s修改成功".format(user.name))
	except:
		logme.error(traceback.format_exc())
		code, msg = (1, "修改异常%s" % traceback.format_exc())
	
	return JsonResponse({'code': code, 'msg': msg})


@csrf_exempt
def getfile(request, filename):
	#  /file/<dir>/<file>?name=<downloadname>
	upload_dir = get_space_dir()
	filepath = os.path.join(upload_dir, filename)
	downloadname = request.GET.get('name')
	
	if os.path.exists(filepath):
		with open(filepath, 'rb') as f:
			response = HttpResponse(f)
			response['Content-Type'] = 'application/octet-stream'
			if downloadname is None:
				response["Content-Disposition"] = "attachment;"
			else:
				response["Content-Disposition"] = "attachment; filename*=UTF-8''{}".format(
					escape_uri_path(downloadname))
			return response
	return JsonResponse({})


@csrf_exempt
def getbusinessnum(request, id, total):
	cases = Order.objects.filter(kind__contains='plan_', main_id=id, isdelete=0)
	steplist = []
	builist = []
	for o in cases:
		case = mm.Case.objects.values('count').get(id=o.follow_id)
		if total == '0' and case['count'] not in ['1', 1]:
			continue
		getstep(steplist, o.follow_id, total)
	for i in steplist:
		bui = Order.objects.filter(kind__contains='step_bu', main_id=i, isdelete=0)
		for b in bui:
			BusinessData = mm.BusinessData.objects.values('count').get(id=b.follow_id)
			if total == '0' and BusinessData['count'] not in ['1', 1]:
				continue
			builist.append(b)
	# print("总数：%s" % (len(builist)))
	return JsonResponse({'num': len(builist)})


def getstep(steplist, id, total):
	orders = Order.objects.filter(kind__contains='case_', main_id=id, isdelete=0)
	for o in orders:
		if o.kind == 'case_case':
			case = mm.Case.objects.values('count').get(id=o.follow_id)
			if total == '0' and case['count'] not in ['1', 1]:
				continue
			getstep(steplist, o.follow_id, total)
		elif o.kind == 'case_step':
			step = mm.Step.objects.values('count').get(id=o.follow_id)
			if total == '0' and step['count'] not in ['1', 1]:
				continue
			steplist.append(o.follow_id)


def getCsrfToken(request):
	from django.middleware.csrf import get_token
	token = get_token(request)
	return JsonResponse({'code': 0, 'data': {'csrf_token': token}})


def queryRoles(request):
	searchvalue = request.GET.get('searchvalue')
	limit = int(request.GET.get('limit', 0))
	page = int(request.GET.get('page', 0))
	start = limit * (page - 1)
	end = limit * page - 1
	
	if searchvalue:
		roles = Role.objects.filter(Q(title__icontains=searchvalue))
	else:
		roles = Role.objects.all()
	
	total = roles.count()
	rolesList = roles[start:end] if end < total and start * end != 0 else roles[start:total]
	
	rolesSerializer = serializers.serialize('json', rolesList)
	rolesList = []
	
	permissionmap = {}
	permission = Permission.objects.all()
	for i in permission:
		permissionmap[i.id] = i.title
	
	for role in json.loads(rolesSerializer):
		one = role['fields']
		one['id'] = role['pk']
		permissions = []
		for permissionId in role['fields']['permissions']:
			permissions.append({'id':permissionId,'title':permissionmap[permissionId]})
		one['permissions'] = permissions
		rolesList.append(one)
	return JsonResponse({'code': 0, 'data': rolesList, 'total': total})


def queryOneRole(request):
	code, msg = (0, "查询成功")
	id = request.POST.get('id')
	role = Role.objects.get(id=id)
	data = []
	try:
		permissions = role.permissions.all()
		for p in permissions:
			node = p.menu.getId()
			node.append(p.id)
			data.append(node)
	except:
		code, msg = (1, "查询失败%s" % traceback.format_exc())
	return JsonResponse({'code': code, 'data': {'id': id, 'title': role.title, 'Permissions': data}, 'msg': msg})


def addRole(request):
	code, msg = (0, '新增角色成功')
	title = request.POST.get('title').strip()
	permissionsIds = request.POST.get('Permissions').split(',')
	try:
		role = Role(title=title)
		role.save()
		for id in permissionsIds:
			role.permissions.add(id)
	except Exception as e:
		if "Duplicate entry '%s' for key 'title'" % title in e.__str__():
			code, msg = (1, '角色名称[%s]重复' % title)
		else:
			code, msg = (1, '新增角色失败%s' % traceback.format_exc())
	return JsonResponse({'code': 0, 'msg': msg})


def editRole(request):
	code, msg = (0, '')
	id = request.POST.get('id')
	title = request.POST.get('title')
	Permissions = request.POST.get('Permissions').split(',')
	try:
		has = Role.objects.exclude(id=id).filter(title=title)
		if has:
			code, msg = (1, '存在该名称的角色，请更换')
		else:
			role = Role.objects.get(id=id)
			role.title = title
			role.save()
			role.permissions.clear()
			for id in Permissions:
				role.permissions.add(id)
			msg = "角色%s修改成功,重新登录后生效" % title
	except:
		logme.error(traceback.format_exc())
		code, msg = (1, "修改异常%s" % traceback.format_exc())
	return JsonResponse({'code': code, 'msg': msg})


def delRoles(request):
	code, msg = (0, '操作成功')
	try:
		ids = request.POST.get('ids').split(',')
		for id in ids:
			role = Role.objects.get(id=id)
			logme.error("角色【{}】删除成功".format(role.title))
			role.delete()
	except:
		error = traceback.format_exc()
		code, msg = (1, '操作异常[%s]' % error)
		logme.error(msg)
	return JsonResponse({'code': code, 'msg': msg})


def queryPermissions(request):
	PermissionsList = []
	if request.GET.get('kind') == 'list':
		searchvalue = request.GET.get('searchvalue')
		limit = int(request.GET.get('limit'))
		page = int(request.GET.get('page'))
		start = limit * (page - 1)
		end = limit * page - 1
		menuId = request.GET.get('id')
		if searchvalue:
			permissions = Permission.objects.filter(Q(title__icontains=searchvalue) & Q(menu__id=menuId))
			total = permissions.count()
		else:
			permissions = Permission.objects.filter(menu__id=menuId)
			total = permissions.count()
		# print(permissions.query)
		
		for p in permissions:
			PermissionsList.append({'id': p.id, 'title': p.title, 'url': p.url, 'type': p.type})
		return JsonResponse({'code': 0, 'data': PermissionsList, 'total': total})
	
	else:
		menus = Menu.objects.filter(parent=None)
		
		for menu in menus:
			node = {'id': menu.id, 'title': menu.title, 'children': []}
			child = Menu.objects.filter(parent=menu)
			if child:
				for i in child:
					permissions = []
					for permission in Permission.objects.filter(menu=i):
						permissions.append({'id': permission.id,
						                    'title': permission.title + '——' + permission.url if permission.url else permission.title})
					node['children'].append({'id': i.id, 'title': i.title, 'children': permissions})
				PermissionsList.append(node)
			else:
				for permission in Permission.objects.filter(menu=menu):
					node['children'].append({'id': permission.id,
					                         'title': permission.title + '——' + permission.url if permission.url else permission.title})
				PermissionsList.append(node)
		# print(PermissionsList)
		
		return JsonResponse({'code': 0, 'data': PermissionsList})


def addPermission(request):
	code, msg = (0, "新增成功")
	try:
		title = request.POST.get('title')
		url = request.POST.get('url')
		menuID = request.POST.get('menu')
		per = Permission()
		per.title = title
		per.url = url
		per.type = 'api'
		per.menu = Menu.objects.get(id=menuID)
		per.save()
	except:
		code = 1
		msg = traceback.format_exc()
	return JsonResponse({'code': code, 'msg': msg})


def editPermission(request):
	code, msg = (0, '')
	id = request.POST.get('id')
	title = request.POST.get('Ptitle')
	url = request.POST.get('url')
	try:
		has = Permission.objects.exclude(id=id).filter(title=title)
		if has:
			code, msg = (1, '存在该名称的权限，请更换')
		else:
			permission = Permission.objects.get(id=id)
			if permission.type == 'view':
				return JsonResponse({'code': 0, 'msg': '视图权限不允许修改'})
			permission.title = title
			permission.url = url
			permission.save()
			msg = "权限%s修改成功" % title
	except:
		logme.error(traceback.format_exc())
		code, msg = (1, "修改异常%s" % traceback.format_exc())
	return JsonResponse({'code': code, 'msg': msg})


def delPermissions(request):
	code, msg = (0, '删除成功')
	try:
		ids = request.POST.get('ids').split(',')
		for i in ids:
			Permission.objects.get(id=i).delete()
	except:
		code, msg = (1, '删除失败%s' % traceback.format_exc())
	return JsonResponse({'code': code, 'msg': msg})


def queryMenus(request):
	menus = Menu.objects.filter(parent=None)
	menuList = []
	for menu in menus:
		node = {'id': menu.id, 'title': menu.title, 'children': []}
		child = Menu.objects.filter(parent=menu)
		if child:
			for i in child:
				node['children'].append({'id': i.id, 'title': i.title, 'type': 'last'})
			menuList.append(node)
		else:
			menuList.append(node)
	# print(menuList)
	
	return JsonResponse({'code': 0, 'data': menuList})


def addMenu(request):
	code, msg = (0, '操作成功')
	title = request.POST.get('title')
	try:
		menu = Menu()
		menu.title = title
		parentId = request.POST.get('parent', None)
		menu.parent = Menu.objects.get(id=parentId) if parentId else None
		menu.save()
		# 新增菜单绑定新增一个页面权限
		Permission(title=title, url='', type='view', menu=menu).save()
	
	except Exception as e:
		logme.warn(e)
		if "Duplicate entry '%s' for key 'title'" % title in e.__str__():
			code, msg = (1, '菜单名称[%s]重复' % title)
		else:
			code, msg = (1, '操作失败：' + traceback.format_exc())
	return JsonResponse({'code': code, 'msg': msg})


def editMenu(request):
	code, msg = (0, '')
	id = request.POST.get('id')
	title = request.POST.get('title')
	parentId = request.POST.get('parent', None)
	try:
		has = Menu.objects.exclude(id=id).filter(title=title)
		if has:
			code, msg = (1, '存在该名称的菜单，请更换')
		else:
			menu = Menu.objects.get(id=id)
			per = Permission.objects.get(title=menu.title, url='', type='view', menu=menu)
			per.title = title
			menu.title = title
			menu.parent = Menu.objects.get(id=parentId) if parentId else None
			menu.save()
			per.save()
			msg = "菜单%s修改成功" % title
	except:
		logme.error(traceback.format_exc())
		code, msg = (1, "修改异常%s" % traceback.format_exc())
	return JsonResponse({'code': code, 'msg': msg})


def delMenu(request):
	code, msg = (0, "删除成功")
	id = request.POST.get('id')
	
	try:
		parmenu = Menu.objects.filter(parent_id=id)
		for i in parmenu:
			Permission.objects.filter(menu_id=i.id).delete()
			Menu.objects.get(id=i.id).delete()
		Permission.objects.filter(menu_id=id).delete()
		Menu.objects.get(id=id).delete()
	except:
		logme.error(traceback.format_exc())
		code, msg = (1, "删除失败:" + traceback.format_exc())
	return JsonResponse({'code': code, 'msg': msg})


def userRoute(request):
	if request.session.get('username','')=='admin':
		menus = list(Menu.objects.all())
		lists = []
		for i in menus:
			lists.append({'id':i.id,'title':i.title})
		return JsonResponse({'code': 0, 'menus': lists})
	permission_menu_list = request.session[settings.SESSION_MENU_KEY][settings.PERMISSION_MENU_KEY]
	Permissionids = [x['id'] for x in permission_menu_list if x['type'] == 'view']
	route = []
	for id in Permissionids:
		p = Permission.objects.get(id=id)
		route.append({'id': p.id, 'title': p.title})
		if p.menu.parent:
			route.append({'id': p.menu.parent.id, 'title': p.menu.parent.title})
	
	print("前端路由\n", json.dumps(route, ensure_ascii=False))
	return JsonResponse({'code': 0, 'menus': route})
