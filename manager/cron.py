#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-10-12 09:42:34
# @Author  : Blackstone
# @to      :定时任务调度

from .models import Crontab,Plan
from .invoker import runplans
from .core import gettaskid
import threading
class Cron(object):

	__cronmanager=None
	__lock=threading.Lock()

	"""
	public api
	"""
	@classmethod
	def querytask(cls):
		try:
			return (cls._getcronmanager().get_jobs())
		except:
			return ("定时任务查询error")

	# @classmethod
	# def tocrontab(cls,username,planid):
	#     pass

	# @classmethod
	# def tonormal(cls,username,planid):
	#     pass


	@classmethod
	def opencrontab(cls,username,planid):
		"""
		开启定时任务
		"""
		try:
			plan=Plan.objects.get(id=planid)
			run_type=plan.run_type
			if run_type.strip()=='点击运行':
				return ("计划[%s]非定时任务 开启失败."%planid)


			config=Crontab.objects.get(plan=plan)
			status=config.status
			if status=='open':
				return
			else:
				crontaskid=config.taskid
				cfg=eval(config.value)
				cls._addcrontab(runplans,args=[username,crontaskid,[plan.id],'1','定时'],taskid=crontaskid,**cfg)

				config.status='open'
				config.save()
			return True

		except:
			return ("用户[%s]对计划[%s]开启定时任务失败 未知异常"%(username,planid))

	@classmethod
	def closecrontab(cls,username,planid):
		"""
		关闭定时任务
		"""

		try:
			plan=Plan.objects.get(id=planid)
			config=Crontab.objects.get(plan=plan)
			if config.status=='close':
				return
			crontaskid=config.taskid
			cls._removecrontab(crontaskid)

			config.status='close'
			config.save()

			return True

		except:

			return ("用户[%s]对计划[%s]开启定时任务失败"%(username,planid))

	def recovertask(cls):
		"""
		服务重启时 如有开启定时任务自动加入 与表Crontab状态一致
		"""
		opentasks=list(Crontab.objects.filter(status='open'))
		for task in opentasks:
			planid=task.plan.id
			crontaskid=task.taskid
			cfg=eval(task.value)
			username=task.author.name
			cls._addcrontab(runplans,args=[username,crontaskid,[planid],'1','定时'],taskid=crontaskid,**cfg)

		print("定时任务重新装载完成...")

	"""
	私有API


	"""

	@classmethod
	def _getcronmanager(cls):
		__lock.acquire()
		from apscheduler.schedulers.background import BackgroundScheduler

		if cls.__cronmanager is None:
			if cls.__cronmanager is None:
				cls.__cronmanager=BackgroundScheduler()
				cls.__cronmanager.start()
				print("新建任务调度器并开启..")


		__lock.release()

		return cls.__cronmanager

	@classmethod
	def _addcrontab(cls,func,args=None,kind='cron',taskid=None,**kw):
		keys=['year','month','day','hour','minute','second']

		try:
			##参数校验
			if args is None:
				args=[]

			if not isinstance(args, (list)):
				raise ValueError('args应传入列表')

			for k in kw:
				if k not in keys:
					raise KeyError("key错误 正确：{'year','month','day','hour','minute','second'}")
				v=kw.get(k, None)
				if v is None:
					kw[k]="*"

			##add tsak
			cls._getcronmanager().add_job(
				func,
				'cron',
				args=args,
				year=keys['year'],
				month=keys['month'],
				day=keys['day'],
				hour=keys['hour'],
				minute=keys['minute'],
				second=keys['second'],
				id=taskid
			)

			print('添加定时任务[id=%s fun=%s]'%(id_,func.__name__))
		except:
			print("添加定时任务[id=%s]失败"%id_)


	@classmethod
	def _removecrontab(cls,crontaskid):
		try:
			cls._getcronmanager().remove_job(crontaskid)
			print("移除定时任务[%s]"%crontaskid)
		except:
			print("移除定时任务[%s]失败！"%crontaskid)

	@classmethod
	def _stopcronmanager(cls,wait=False):
		try:
			cls._getcronmanager().shutdown(wait=wait)
			print("关闭定时调度器")
		except:
			raise RuntimeError("关闭定时任务调度器error")