#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-11-19 09:51:22
# @Author  : Blackstone
# @to      :
import time,traceback,redis,datetime,requests
from django.conf import settings
from manager import models
from hashlib import md5

'''
请求session保持
'''
_session_context_manager=dict()

def get_task_session(key):
	s=_session_context_manager.get(key, requests.session())
	_session_context_manager[key]=s
	# print('session=>',s)
	return s
	

def clear_task_session(key):
	try:
		del _session_context_manager[key]
	except:
		pass

'''通用配置查询
'''

_task_context_manager=dict()

def get_top_common_config(taskid,kind='db'):
	cache=_task_context_manager.get(taskid,{})
	dbcache=cache.get(kind,None)
	print('===获得缓存通用配置 %s->%s=>%s'%(taskid,kind,dbcache))
	return dbcache

def set_top_common_config(taskid,value,kind='db',src=None):
	print('===[%s]设置缓存通用配置%s->%s=>%s'%(src,taskid,kind,value))
	cache=_task_context_manager.get(taskid,{})
	dbcache=cache.get(kind,None)
	if dbcache is None:
		cache[kind]=value
		_task_context_manager[taskid]=cache

	print(_task_context_manager.get(taskid))

'''
测试数据缓存

'''
_user_step_testdata_manager=dict()

def _getvid():
	str_=str(datetime.datetime.now())
	return 'vid_'+md5(str_.encode('utf-8')).hexdigest()

def _addtestdata(callername,stepid,adddata):
	# print('alt=>',adddata)
	vid=_getvid()
	testdata=models.BusinessData()
	testdata.id=vid
	testdata.businessname=adddata.get('businessname','')
	testdata.itf_check=adddata.get('itf_check','')
	testdata.db_check=adddata.get('db_check','')
	testdata.params=adddata.get('params','')
	print('参数信息=>',testdata.params)

	cur=querytestdata(callername, stepid,trigger='add')
	cur.append(testdata)
	_settestdata(callername, stepid, cur)

	res=querytestdata(callername, stepid,trigger='www')
	print('res=>',[x.params for x in res])


def _settestdata(callername,stepid,setdata):
	try:
		key="%s_%s"%(callername,stepid)
		_user_step_testdata_manager[key]=setdata
		print("[设置缓存]key=%s value=%s"%(key,str(setdata)))

	except:
		print("[设置缓存]异常")
		print(traceback.format_exc())

def _deltestdata(callername,stepid,vids):
	cur=querytestdata(callername, stepid,trigger='del')
	for x in cur:
		if str(x.id) in vids:
			cur.remove(x)

	_settestdata(callername, stepid,cur)


def _edittestdata(callername,stepid,editdata):
	cur=querytestdata(callername, stepid,trigger='edit')
	vid=editdata.get('id')
	for x in cur:
		if str(x.id)==str(vid):
			print('编辑中...')
			x.businessname=editdata.get('businessname')
			x.itf_check=editdata.get('itf_check')
			x.db_check=editdata.get('db_check')
			x.params=editdata.get('params')
			print('x=>',x.itf_check)
			break;

	print('编辑后数据=>',cur)

	_settestdata(callername, stepid, cur)


def _cleartestdata(callername,stepid):
	key="%s_%s"%(callername,stepid)
	try:
		
		del _user_step_testdata_manager[key]
		print('[清除缓存]key=%s'%key)
	except:
		print('[清除缓存异常]key=%s'%key)
		#print(traceback.format_exc())


def querytestdata(callername,stepid,trigger='query'):

	res=[]
	if trigger=='query':
		try:
			_cleartestdata(callername, stepid)
			step=models.Step.objects.get(id=stepid)
			res=list(step.businessdatainfo.all())
			#缓存数据
			_settestdata(callername, stepid,res)
		except:
			print('[新增步骤异常]')
			error=traceback.format_exc()
			print(error)

	else:
		key="%s_%s"%(callername,stepid)
		res=_user_step_testdata_manager.get(key,[])
	return res


def queryafteradd(callername,stepid,adddata):
	_addtestdata(callername,stepid,adddata)
	return querytestdata(callername, stepid,trigger='add')

def queryafteredit(callername,stepid,editdata):
	_edittestdata(callername, stepid, editdata)
	return querytestdata(callername, stepid,trigger='edit')

def queryafterdel(callername,stepid,vids):
	_deltestdata(callername, stepid, vids)
	return querytestdata(callername, stepid,trigger='del')

def mounttestdata(callername,stepid,trigger='add'):
	try:
		key="%s_%s"%(callername,stepid)
		bids=[]
		cache=None
		if trigger=='add':
			cache=querytestdata(callername, None,trigger='mount')
		else:
			cache=querytestdata(callername, stepid,trigger='mount')
		# print('cache=>',cache)
		for x in cache:
			if str(x.id).startswith('vid_'):
				bd=models.BusinessData()
				bd.businessname=x.businessname
				bd.itf_check=x.itf_check
				bd.db_check=x.db_check
				bd.params=x.params
				#bd.params=x.params.replace('true','True').replace('false','False').replace('null','None')
				bd.save()

				bids.append(bd.id)
				step=models.Step.objects.get(id=stepid)
				step.businessdatainfo.add(bd)
			else:
				bid=int(x.id)
				bids.append(bid)
				bd=models.BusinessData.objects.get(id=bid)
				bd.businessname=x.businessname
				bd.itf_check=x.itf_check
				bd.db_check=x.db_check
				bd.params=x.params

				print('保存业务数据长度=>',len(bd.params))
				#bd.params=x.params.replace('true','True').replace('false','False').replace('null','None')
				bd.save()



		print('[挂载测试数据]成功 stepid=%s 测试数据id=%s'%(stepid,bids))

		# _cleartestdata(callername, stepid)


	except:
		err=traceback.format_exc()
		print('[挂载测试数据]异常')
		print(err)


def gettestdataparams(businessdata_id):
	try:
		businessdatainst=models.BusinessData.objects.get(id=businessdata_id)
		msg,step=gettestdatastep(businessdata_id)
		if msg is not 'success':
			return (msg,step)

		businessdatainst.params=businessdatainst.params.replace('null','None').replace('false','False').replace('true','True')

		if step.step_type=='interface':
			if step.content_type=='xml':
				return ('success',businessdatainst.params)
			else:
				return ('success',eval(businessdatainst.params))


		elif step.step_type=='function':
			return ('success',businessdatainst.params.split(','))
	except:
		error='获取测试数据传参信息异常[%s]'%traceback.format_exc()
		print(error)
		return ('error',error)


def gettestdatastep(businessdata_id):

	# print('aa=>',businessdata_id)
	try:
		businessdatainst=models.BusinessData.objects.get(id=businessdata_id)
		steps=models.Step.objects.all()
		step=[step for step in steps if businessdatainst in list(step.businessdatainfo.all())][0]
		return ('success',step)
	except:
		print(traceback.format_exc())
		return ('error','获取业务数据所属步骤异常 业务ID=%s'%businessdatainst.id)

"""
控制台输出
redis key格式=>console.msg::username::taskid
"""
def viewcache(taskid,username,kind=None,*msg):

	taskmsg=""

	if kind is not None:
		##定时任务不加入redis队列
		return
	try:
		what="".join((msg))
		# print(username)
		what="%s        %s"%(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),what)
		# print("console:",what)
		print(what)
		con=redis.Redis(host = settings.REDIS_HOST,port =settings.REDIS_PORT)
		key="console.msg::%s::%s"%(username,taskid)
		# data={}
		# data['msg']=what
		# data['time']
		con.lpush(key,what)
		con.close()
	except Exception as e:
		print("viewcache异常")
		print(traceback.format_exc())

def remotecache(key,linemsg):
		con=redis.Redis(host = settings.REDIS_HOST,port =settings.REDIS_PORT)
		con.lpush(key,linemsg)
		con.close()





