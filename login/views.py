import threading

import redis
from django.shortcuts import render, redirect, render_to_response
from django.conf import settings
from ME2 import configs
from ME2.settings import logme
from manager.models import *
from login.models import *
from manager import models as mm
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from manager.core import *
from django.db.models import Q
from manager.ar import Grant


# Create your views here
from manager.operate.redisUtils import RedisUtils


def global_setting(request):
	content = {
		'BASE_URL': settings.BASE_URL
	}
	return content


def page_not_found(request, exception, **kwargs):
	return render_to_response('manager/404.html')


def page_error(rquest):
	return render_to_response('manager/500.html')


def index(request):
	if request.session.get('is_login', None):
		username = request.session.get("username", None)
		return redirect('/manager/index/')
	
	else:
		return redirect("/account/login/")


def initDataupdate():
	print('开始更新旧的数据')
	variables = Variable.objects.all()
	for var in variables:
		if not Tag.objects.filter(var=var).exists():
			tag = Tag()
			tag.var = var
			tag.customize = ''
			tag.planids = '{}'
			tag.isglobal = 1
			tag.save()
			time.sleep(0.001)
			print('变量' + str(var.id) + '更新成功')
	print('变量tag更新完成')
	dbcons = DBCon.objects.all()
	for dbcon in dbcons:
		if dbcon.scheme is None or dbcon.scheme == '':
			dbcon.scheme = '全局'
			dbcon.save()
			time.sleep(0.001)
			print('数据连接' + str(dbcon.id) + '更新成功')
	print('数据连接更新完成')
	plans = Plan.objects.all()
	for plan in plans:
		try:
			if plan.schemename is None or plan.schemename == '':
				if plan.db_id is not None and plan.db_id != '' and plan.db_id.isdigit():
					description = DBCon.objects.get(id=plan.db_id).description
					plan.db_id = description if description is not None else ''
					plan.schemename = '全局'
					plan.save()
					print('计划' + str(plan.id) + '更新成功')
				else:
					plan.db_id = ''
					plan.schemename = '全局'
					plan.save()
				print('计划' + str(plan.id) + '更新成功')
		except:
			print(traceback.format_exc())
	print('计划更新完成')
	cases = mm.Case.objects.all()
	for case in cases:
		try:
			dbid = case.db_id
			if dbid.isdigit():
				case.db_id = DBCon.objects.get(id=dbid).description
				case.save()
				print('用例' + str(case.id) + '更新成功')
		except:
			if dbid is None:
				case.db_id = ''
				case.save()
				print('用例' + str(case.id) + '更新成功')
			else:
				print(traceback.format_exc())
				print('用例' + str(case.id) + '更新失败')
	steps = Step.objects.all()
	for step in steps:
		try:
			if step.db_id.isdigit():
				step.db_id = DBCon.objects.get(id=step.db_id).description
				step.save()
				print('步骤' + str(step.id) + '更新成功')
		except:
			if step.db_id is None:
				step.db_id = ''
				step.save()
				print('步骤' + str(step.id) + '更新成功')
			else:
				print(traceback.format_exc())
				print('步骤' + str(step.id) + '更新失败')
	print('步骤的dbid更新完成')
	print('旧数据更新结束')

def clearRedisforUser(username):
	con = RedisUtils()
	try:
		keys = con.keys("console.msg::%s::*" % (username))
		print('清理用户【{}】redis缓存'.format(username))
		for elem in con.keys():
			con.delete(elem)
			con.close()
	except:
		print('redis没有正常连接')



@csrf_exempt
def login(request):
	# threading.Thread(target=initDataupdate, args=()).start()
	if configs.IS_CREATE_SUPERUSER:
		User.create_superuser(EncryptUtils.md5_encrypt(configs.SUPERUSER_PWD))
	if request.method == 'POST':
		message = ''
		username = request.POST.get('username')
		password = request.POST.get('password')
		try:
			user = User.objects.get(name=username)
			if EncryptUtils.md5_encrypt(password) == user.password:
				request.session.set_expiry(14400)
				request.session['is_login'] = True
				request.session['username'] = username
				print('用户登录成功：{}\t{}'.format(user.name, user.password))
				clearRedisforUser(username)
				return JsonResponse({'code':0,'msg':'登录成功'})
			else:
				message = '密码错误'
				print('用户密码错误：{}\t{}'.format(user.name, user.password))
		except:
			message = '用户不存在'
			print(message)
		return JsonResponse({'code':1,'msg':message})

	if request.session.get('is_login', None):
		logme.info('用户已登录，跳转到登录页面')
		username = request.session.get("username", None)
		return redirect('/manager/index/')
	logme.info('用户未登录，展示登录页面')
	return render(request, 'login/login.html', locals())


def logout(request):
	print('用户【{}】退出登录'.format(request.session.get('username', None)))
	request.session.flush()
	return redirect("/account/login/")


@csrf_exempt
def account(request):

	UI_MENU_YHGL_BUTTON_SCYH=Grant.is_ui_display('UI_MENU_YHGL_BUTTON_SCYH', request.session.get('username'))
	return render(request, 'login/account.html',locals())

@csrf_exempt
def role(request):
	return render(request, 'login/role.html')

def queryaccount(request):
	searchvalue = request.GET.get('searchvalue')
	res = None
	if searchvalue:
		print("变量查询条件=>"+searchvalue)
		res = list(User.objects.filter(Q(name__icontains=searchvalue) & ~Q(name__in=['定时任务','system'])))
	else:
		res = list(User.objects.filter(~Q(name__in=['定时任务','system'])))
	
	limit = request.GET.get('limit')
	page = request.GET.get('page')
	res, total = getpagedata(res, page, limit)
	
	jsonstr = json.dumps(res, cls=UserEncoder, total=total)
	return JsonResponse(jsonstr, safe=False)


@csrf_exempt
def addaccount(request):
	code, msg = 0, ''
	try:
		user = User()
		user.name = request.POST.get('username')
		user.password = EncryptUtils.md5_encrypt(request.POST.get('password'))
		user.save()
		logme.error("用户【{}】新增成功".format(user.name))
		msg = '操作成功'
	except:
		logme.error(traceback.format_exc())
		code = 1
		msg = '操作失败'
	
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


@csrf_exempt
def delaccount(request):
	code, msg = 0, ''
	try:
		ids = request.POST.get('ids').split(',')
		for id_ in ids:
			user = User.objects.get(id=id_)
			user.delete()
		msg = '操作成功'
		logme.error("用户【{}】删除成功".format(user.name))
	except:
		error = traceback.format_exc()
		code = 4
		msg = '操作异常[%s]' % error
		logme.error(msg)
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


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
	code, msg = 0, ''
	id = request.POST.get('uid')
	name = request.POST.get('username')
	password = request.POST.get('password')
	try:
		num_of_name=len(list(User.objects.exclude(id=id).filter(name=name)))
		if num_of_name!=0:
			raise Exception('已存在相同用户名')
		user = User.objects.get(id=id)
		user.name = name
		user.password = password
		user.save()
		msg = '操作成功'
		logme.error("用户【{}】账号信息修改成功".format(user.name,user.password))
	except Exception as e:
		code = 4
		msg = '操作异常[%s]' % e
		logme.error(msg)
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)


##测试接口
'''
测试表达式
'''


@csrf_exempt
def testexpress(request):
	return JsonResponse({'code': 1, 'bool': True, 'str': 'hhh', 'nullstr': None, 'spacestr': '', 'array': [],
	                     'data': [{'token': 'tokenyyeyye'}], 'qibastr': '10,203.30'}, safe=False)


@csrf_exempt
def testexpress1(request):
	return JsonResponse([{'width': 95, 'name': '节点名称'}, {'width': 98, 'name': '节点名称:一审'}], safe=False)


@csrf_exempt
def testexpress2(request):
	return JsonResponse(False, safe=False)


@csrf_exempt
def testxml(request):
	return render(request, 'manager/test.xml', content_type="application/xml")

@csrf_exempt
def mocktimeout(request):
	time.sleep(20)
	return JsonResponse(True,safe=False)
	

@csrf_exempt
def updateroledata(request):
	#添加system角色和system用户
	if not User.objects.filter(name='system').exists():
		u=User()
		u.name='system'
		u.password='54b53072540eeeb8f8e9343e71f28176'#system
		u.description=''
		u.save()

	if not Role.objects.filter(name='系统管理员').exists():
		r=Role()
		r.author=User.objects.get(name='system')
		r.name='系统管理员'
		r.description='系统管理员'
		r.save()
		r.users.add(User.objects.get(name='system'))

	##添加超级管理员
	if not Role.objects.filter(name='超级管理员').exists():
		r=Role()
		r.author=User.objects.get(name='system')
		r.name='超级管理员'
		r.description='超级管理员'
		r.save()	
		r.users.add(User.objects.get(name='admin'))	

	###
	###添加一般用户角色
	if not Role.objects.filter(name='一般用户').exists():
		r=Role()
		r.author=User.objects.get(name='system')
		r.name='一般用户'
		r.description='一般用户'
		r.save()
	r=Role.objects.get(name='一般用户')
	all_user=User.objects.all()
	for user in all_user:
		if user.name in('admin','system'):
			continue;
		if user not in r.users.all():
			r.users.add(user)

	##添加不可见菜单
	ui_data={
		'UI_MENU_YHGL':'用户管理菜单',
		'UI_MENU_JSGL':'角色管理菜单',
		'UI_MENU_QXGL':'权限管理菜单',
		'UI_CONFIG_GLOBAL_SET':'全局配置',
		'UI_MENU_YHGL_BUTTON_SCYH':'用户管理菜单删除用户按钮'
	}

	for code,description in ui_data.items():
		uc=UIControl()
		uc.author=User.objects.get(name='system')
		uc.code=code
		uc.description=description
		if Grant.isconfig(uc.code):
			#uc.is_open=1
			pass
		uc.save()
	#添加组件默认权限
	uuc=User_UIControl()
	uuc.kind='ROLE'
	uuc.user_id=Role.objects.get(name='一般用户').id
	uuc.uc_id=UIControl.objects.get(code='UI_MENU_YHGL').id
	uuc.save()

	uuc=User_UIControl()
	uuc.kind='ROLE'
	uuc.user_id=Role.objects.get(name='一般用户').id
	uuc.uc_id=UIControl.objects.get(code='UI_CONFIG_GLOBAL_SET').id
	uuc.save()

	uuc=User_UIControl()
	uuc.kind='ROLE'
	uuc.user_id=Role.objects.get(name='一般用户').id
	uuc.uc_id=UIControl.objects.get(code='UI_MENU_YHGL_BUTTON_SCYH').id
	uuc.save()

	uuc=User_UIControl()
	uuc.kind='ROLE'
	uuc.user_id=Role.objects.get(name='超级管理员').id
	uuc.uc_id=UIControl.objects.get(code='UI_MENU_YHGL_BUTTON_SCYH').id
	uuc.save()

	uuc=User_UIControl()
	uuc.kind='ROLE'
	uuc.user_id=Role.objects.get(name='一般用户').id
	uuc.uc_id=UIControl.objects.get(code='UI_MENU_JSGL').id
	uuc.save()

	uuc=User_UIControl()
	uuc.kind='ROLE'
	uuc.user_id=Role.objects.get(name='超级管理员').id
	uuc.uc_id=UIControl.objects.get(code='UI_MENU_JSGL').id
	uuc.save()

	uuc=User_UIControl()
	uuc.kind='ROLE'
	uuc.user_id=Role.objects.get(name='一般用户').id
	uuc.uc_id=UIControl.objects.get(code='UI_MENU_QXGL').id
	uuc.save()

	uuc=User_UIControl()
	uuc.kind='ROLE'
	uuc.user_id=Role.objects.get(name='超级管理员').id
	uuc.uc_id=UIControl.objects.get(code='UI_MENU_QXGL').id
	uuc.save()


	########
	return JsonResponse({'code':0,'msg':'update finish..'},safe=False)