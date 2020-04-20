#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-11-19 09:51:22
# @Author  : Blackstone
# @to      :
import time, traceback, redis, datetime, requests, copy, os
from django.conf import settings
from manager import models
from hashlib import md5
from ME2.settings import logme, BASE_DIR

'''
日志打印
'''
class Me2Log(object):

	@classmethod
	def debug(cls,*msg):
		logme.debug(' '.join([str(x) for x in msg]))

	@classmethod
	def info(cls,*msg):
		logme.info(' '.join([str(x) for x in msg]))

	@classmethod
	def warn(cls,*msg):
		logme.warn(' '.join([str(x) for x in msg]))

	@classmethod
	def error(cls,*msg):
		logme.error(' '.join([str(x) for x in msg]))


'''
用户操作记录
'''
_OPERATION = {
	'symbol': {
		'add': '增加',
		'del': '删除',
		'delete': '删除',
		'update': '更新',
		'edit': '编辑',
		'query': '查询',
	},
	'entity': {
		'plan': '计划',
		'case': '用例',
		'step': '步骤',
		'business': '测试点',
		'businessdata': '测试点',
		'var': '变量',
		'variable': '变量',
		'con': '数据连接',
		'dbcon': '数据连接',
		'template': '模板',
		'templatefield': '模板字段',
		'tag': '标签',
	}
}


def get_symbol_name(key):
	return _OPERATION['symbol'].get(key, '[%s]未定义' % key)


def get_entity_name(key):
	return _OPERATION['entity'].get(key, '[%s]未定义' % key)


def get_operate_name(interfacename):
	'''
	获取操作名字

	'''
	interfacename = interfacename.split('/')[-1]
	print('interfacename=>', interfacename)
	a = ''
	b = ''
	for _ in _OPERATION['symbol']:
		if _ in interfacename:
			a = _OPERATION['symbol'][_]
			break;
	
	for _ in _OPERATION['entity']:
		if _ in interfacename:
			b = _OPERATION['entity'][_]
			break;
	
	# print('a=>',a)
	# print('b=>',b)
	return ''.join([a, b])


'''
提示语优化

'''

_friendly_map = {
	'db': {
		'ORA-01017': '[oracle]账号密码错误',
		'DPI-1047': '[oracle]没装instantclient工具,请联系开发',
		'ORA-12505': '[oracle]SID无法识别',
		'RA-12545': '[oracle]host错误',
		'RA-12541': '[oracle]端口号错误',
		'psycopg2.OperationalError': '[pqsql]连接配置错误,请自检字段',
		'pymysql.err.OperationalError: (1044': '[mysql]库名错误',
		'pymysql.err.OperationalError: (2003': '[mysql]host/port错误',
		'pymysql.err.OperationalError: (1045': '[mysql]账号密码错误',
	}
}


def get_friendly_msg(msg0, kind='all'):
	'''
	'''
	if 'all' == kind:
		for k1, v1 in _friendly_map.items():
			for k2, v2 in v1.items():
				print('msg0=>', msg0)
				if msg0.__contains__(k2):
					return v2
		return msg0
	else:
		for k1, v1 in _friendly_map.items():
			if kind == k1:
				for k2, v2 in v1.items():
					if msg0.__contains__(k2):
						return v2
				return msg0


'''
请求session保持
'''
_session_context_manager = dict()


def get_task_session(key):
	s = _session_context_manager.get(key, requests.session())
	_session_context_manager[key] = s
	# print('session=>',s)
	return s


def clear_task_session(key):
	try:
		del _session_context_manager[key]
	except:
		pass


'''通用配置查询
'''

_task_context_manager = dict()


def get_top_common_config(taskid, kind='db'):
	cache = _task_context_manager.get(taskid, {})
	dbcache = cache.get(kind, None)
	Me2Log.warn('===获得缓存通用配置 %s->%s=>%s' % (taskid, kind, dbcache))
	return dbcache


def set_top_common_config(taskid, value, kind='db', src=None):
	Me2Log.warn('===[%s]设置缓存通用配置%s->%s=>%s' % (src, taskid, kind, value))
	cache = _task_context_manager.get(taskid, {})
	dbcache = cache.get(kind, None)
	# if dbcache is None:  加上以后优先级变成 计划>用例。。。
	cache[kind] = value
	_task_context_manager[taskid] = cache


'''
测试数据缓存

'''
_user_step_testdata_manager = dict()


def _getvid():
	str_ = str(datetime.datetime.now())
	return 'vid_' + md5(str_.encode('utf-8')).hexdigest()


# def _addtestdata(callername, stepid, adddata):
# 	# print('alt=>',adddata)
# 	vid = _getvid()
# 	testdata = models.BusinessData()
# 	testdata.id = vid
# 	testdata.businessname = adddata.get('businessname', '')
# 	testdata.itf_check = adddata.get('itf_check', '')
# 	testdata.db_check = adddata.get('db_check', '')
# 	testdata.params = adddata.get('params', '')
# 	print('参数信息=>', testdata.params)

# 	cur = querytestdata(callername, stepid, trigger='add')
# 	cur.append(testdata)
# 	_settestdata(callername, stepid, cur)

# 	res = querytestdata(callername, stepid, trigger='www')
# 	print('res=>', [x.params for x in res])


# def _copytestdata(callername, stepid, vid):
# 	key = "%s_%s" % (callername, stepid)
# 	cur = querytestdata(callername, stepid, trigger='copy')

# 	copyit = None
# 	for business in cur:
# 		print('curbit=>', business.id)
# 		if str(business.id) == str(vid):
# 			copyit = models.BusinessData()
# 			copyit.id = _getvid()
# 			copyit.businessname = '%s_%s' % (business.businessname, str(datetime.datetime.now()))
# 			copyit.itf_check = business.itf_check
# 			copyit.db_check = business.db_check
# 			copyit.params = business.params
# 			cur.append(copyit)
# 			print('[复制测试数据]vid=%s' % vid)
# 			_settestdata(callername, stepid, cur)
# 			return

# 	print('[复制测试数据]没发现指定复制对象 vid=%s' % vid)


# def _settestdata(callername, stepid, setdata):
# 	try:
# 		key = "%s_%s" % (callername, stepid)
# 		_user_step_testdata_manager[key] = setdata
# 		print("[设置缓存]key=%s value=%s" % (key, str(setdata)))

# 	except:
# 		print("[设置缓存]异常")
# 		print(traceback.format_exc())


# def _deltestdata(callername, stepid, vids):
# 	cur = querytestdata(callername, stepid, trigger='del')
# 	curtmp = copy.deepcopy(cur)
# 	print('删除前缓存=>', cur, len(cur))
# 	print('需要删除的业务id=>', vids)
# 	for x in cur:
# 		# print('id=>',str(x.id))
# 		if str(x.id) in vids:
# 			print('移除id=>', str(x.id))
# 			curtmp.remove(x)
# 	# else:
# 	# 	print('忽略id=>',str(x.id),len(str(x.id)))
# 	print('删除后缓存=>', curtmp)

# 	_settestdata(callername, stepid, curtmp)


# def _edittestdata(callername, stepid, editdata):
# 	cur = querytestdata(callername, stepid, trigger='edit')
# 	vid = editdata.get('id')
# 	for x in cur:
# 		if str(x.id) == str(vid):
# 			print('编辑中...')
# 			x.businessname = editdata.get('businessname')
# 			x.itf_check = editdata.get('itf_check')
# 			x.db_check = editdata.get('db_check')
# 			x.params = editdata.get('params')
# 			print('x=>', x.itf_check)
# 			break;

# 	print('编辑后数据=>', cur)

# 	_settestdata(callername, stepid, cur)


# def _cleartestdata(callername, stepid):
# 	key = "%s_%s" % (callername, stepid)
# 	try:

# 		del _user_step_testdata_manager[key]
# 		print('[清除缓存]key=%s' % key)
# 	except:
# 		print('[清除缓存异常]key=%s' % key)


# print(traceback.format_exc())


# def querytestdata(callername, stepid, trigger='query'):
# 	res = []
# 	if trigger == 'query':
# 		try:
# 			_cleartestdata(callername, stepid)
# 			step = models.Step.objects.get(id=stepid)
# 			res = list(step.businessdatainfo.all())
# 			# 缓存数据
# 			_settestdata(callername, stepid, res)
# 		except:
# 			print('[新增步骤异常]')
# 			error = traceback.format_exc()
# 			print(error)

# 	else:
# 		key = "%s_%s" % (callername, stepid)
# 		res = _user_step_testdata_manager.get(key, [])
# 	return res


# def queryafteradd(callername, stepid, adddata):
# 	_addtestdata(callername, stepid, adddata)
# 	return querytestdata(callername, stepid, trigger='add')


# def queryaftercopy(callername, stepid, vid):
# 	_copytestdata(callername, stepid, vid)
# 	return querytestdata(callername, stepid, trigger='copy')


# def queryafteredit(callername, stepid, editdata):
# 	_edittestdata(callername, stepid, editdata)
# 	return querytestdata(callername, stepid, trigger='edit')


# def queryafterdel(callername, stepid, vids):
# 	_deltestdata(callername, stepid, vids)
# 	return querytestdata(callername, stepid, trigger='del')


# def mounttestdata(callername, stepid, trigger='add'):
# 	try:
# 		key = "%s_%s" % (callername, stepid)
# 		bids = []
# 		cache = None
# 		if trigger == 'add':
# 			cache = querytestdata(callername, None, trigger='mount')
# 		else:
# 			cache = querytestdata(callername, stepid, trigger='mount')
# 			##清除step之前关联的 不在缓存中的业务数据
# 			step = models.Step.objects.get(id=stepid)
# 			allids = [x.id for x in list(step.businessdatainfo.all())]
# 			cacheids = [x.id for x in cache]
# 			todelids = [x for x in allids if x not in cacheids]
# 			print('删除不在缓存中的业务数据id=>', todelids)
# 			for x in todelids:
# 				step.businessdatainfo.remove(x)

# 		# print('cache=>',cache)
# 		for x in cache:
# 			if str(x.id).startswith('vid_'):
# 				bd = models.BusinessData()
# 				bd.businessname = x.businessname
# 				bd.itf_check = x.itf_check
# 				bd.db_check = x.db_check
# 				bd.params = x.params
# 				# bd.params=x.params.replace('true','True').replace('false','False').replace('null','None')
# 				bd.save()

# 				bids.append(bd.id)
# 				step = models.Step.objects.get(id=stepid)
# 				step.businessdatainfo.add(bd)
# 			else:
# 				bid = int(x.id)
# 				print('修改业务数据id=%s' % bid)
# 				bids.append(bid)
# 				bd = models.BusinessData.objects.get(id=bid)
# 				bd.businessname = x.businessname
# 				bd.itf_check = x.itf_check
# 				bd.db_check = x.db_check
# 				bd.params = x.params

# 				print('params=>', bd.params)

# 				print('保存业务数据长度=>', len(bd.params))
# 				# bd.params=x.params.replace('true','True').replace('false','False').replace('null','None')
# 				bd.save()

# 		print('[挂载测试数据]成功 stepid=%s 测试数据id=%s' % (stepid, bids))

# 	# _cleartestdata(callername, stepid)

# 	except:
# 		err = traceback.format_exc()
# 		print('[挂载测试数据]异常')
# 		print(err)


# def gettestdataparams(businessdata_id):
# 	try:
# 		businessdatainst = models.BusinessData.objects.get(id=businessdata_id)
# 		msg, step = gettestdatastep(businessdata_id)
# 		if msg is not 'success':
# 			return (msg, step)

# 		data = businessdatainst.params

# 		if step.step_type == 'interface':
# 			if step.content_type in ['xml','urlencode']:
# 				return ('success', data)
# 			else:
# 				data = data.replace('null', 'None').replace('true','True').replace('false','False')
# 				return ('success', eval(data))

# 		elif step.step_type == 'function':
# 			return ('success', businessdatainst.params.split(','))
# 	except:
# 		error = '获取测试数据传参信息异常[%s]' % traceback.format_exc()
# 		print(error)
# 		return ('error', error)


# def gettestdatastep(businessdata_id):
# 	# print('aa=>',businessdata_id)
# 	try:
# 		businessdatainst = models.BusinessData.objects.get(id=businessdata_id)
# 		# steps=models.Step.objects.all()
# 		# step=[step for step in steps if businessdatainst in list(step.businessdatainfo.all())][0]
# 		# return ('success',step)
# 		stepid = models.Order.objects.get(follow_id=businessdata_id, kind='step_business').main_id
# 		step = models.Step.objects.get(id=stepid)
# 		return ('success', step)

# 	except:
# 		print(traceback.format_exc())
# 		return ('error', '获取业务数据所属步骤异常 业务ID=%s' % businessdata_id)


"""
控制台输出
redis key格式=>console.msg::username::taskid
"""


def viewcache(taskid, username, kind=None, *msg):
	taskmsg = ""
	if kind is not None:
		##定时任务不加入redis队列
		return
	try:
		logname = BASE_DIR + "/logs/" + taskid + ".log"
		what = "".join((msg))
		# print(username)
		what = "%s        %s" % (time.strftime("[%m-%d %H:%M:%S]", time.localtime()), what)
		# print("console:",what)
		# print('redis=>', what)
		# f = open(logname, "a")
		# f.write(what + "<br>\n")
		# f.close
		with open(logname, 'a', encoding='UTF-8') as f:
			f.write(what + '<br>\n')
		
		# print(what)
		con = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
		key = "console.msg::%s::%s" % (username, taskid)
		# data={}
		# data['msg']=what
		# data['time']
		con.lpush(key, what)
		con.close()
	except Exception as e:
		Me2Log.error("viewcache异常")
		Me2Log.error(traceback.format_exc())


def remotecache(key, linemsg):
	con = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
	con.lpush(key, linemsg)
	con.close()


# 运行中的任务 以及taskid
_runninginfo = dict()


def setRunningInfo(username, planid, taskid, isrunning, dbscheme='全局',is_verify='1'):
	if 'lastest_taskid' not in _runninginfo:
		_runninginfo['lastest_taskid'] = {}
	lastest_taskid = _runninginfo.get('lastest_taskid', {})
	lastest_taskid[username] = taskid
	if str(planid) not in _runninginfo:
		_runninginfo[str(planid)] = {}
	planinfo = _runninginfo.get(str(planid), {})
	if isrunning == 1:
		planinfo['isrunning'] = 'verify' if is_verify == '1' else 'debug'
	else:
		planinfo['isrunning'] = '0'
	planinfo['dbscheme'] = dbscheme
	if 'verify' not in planinfo:
		planinfo['verify']={}
	if 'debug' not in planinfo:
		planinfo['debug']={}
	verify = planinfo.get('verify', {})
	debug = planinfo.get('debug', {})
	if str(is_verify) == '1':
		verify['taskid']=taskid
	elif str(is_verify) == '0':
		debug['taskid'] = taskid
	print("储存运行信息", _runninginfo)


def getRunningInfo(username='', planid='', type='lastest_taskid'):
	# print('getinfo:', username, planid, type)
	if type == 'lastest_taskid':
		latest_taskids = _runninginfo.get('lastest_taskid', {})
		latest_taskid = latest_taskids.get(username, None)
		return latest_taskid
	elif type == 'debug_taskid':
		planinfo = _runninginfo.get(str(planid), {})
		debug = planinfo.get('debug', {})
		debug_taskid = debug.get('taskid', None)
		return debug_taskid
	elif type == 'verify_taskid':
		planinfo = _runninginfo.get(str(planid), {})
		verify = planinfo.get('verify', {})
		verify_taskid = verify.get('taskid', None)
		return verify_taskid
	elif type == 'isrunning':
		planinfo = _runninginfo.get(str(planid), {})
		isrunning = planinfo.get('isrunning', 0)
		return str(isrunning)
	elif type == 'dbscheme':
		planinfo = _runninginfo.get(str(planid), {})
		dbscheme = planinfo.get('dbscheme', '全局')
		return dbscheme
