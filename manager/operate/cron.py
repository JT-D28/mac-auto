#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-10-12 09:42:34
# @Author  : Blackstone
# @to      :定时任务调度
import traceback

from manager.StartPlan import RunPlan
from manager.models import Crontab, Plan
from manager.invoker import runplan
from manager.core import gettaskid
import threading


def cronRun(planid):
    taskid = gettaskid(planid)
    x = RunPlan(taskid,planid,'3','定时任务',startNodeId='plan_' + str(planid))
    threading.Thread(target=x.start).start()

class Cron(object):
    __cronmanager = None
    __lock = threading.Lock()

    @classmethod
    def querytask(cls):
        try:
            jobs = cls._getcronmanager().get_jobs()
            return jobs
        except:
            return ("定时任务查询error")
    @classmethod
    def getcron(self, value):
        times = value.split(' ')
        try:
            if times[2] != '*' and times[3] == '*':
                times[3] = '0'
            if times[1] != '*' and times[2] == '*':
                times[2] = '0'
                times[3] = '0'
            if times[0] != '*' and times[1] == '*':
                times[1] = '1'
                times[2] = '0'
                times[3] = '0'
            return {
                'month': times[0],
                'day': times[1],
                'hour': times[2],
                'minute': times[3]
            }
        except:
            return value


    @classmethod
    def addcrontab(cls,planid):
        cronid = Plan.objects.get(id=planid).__str__()
        existJobs=cls.querytask()
        cron = Crontab.objects.get(plan_id=planid)
        for job in existJobs:
            if cronid == job.id:
                cls._removecrontab(cronid)
                break
        msg = cls._addcrontab(cronRun, args=[planid], id=cronid, **cls.getcron(cron.value))
        if msg !='':
            return "<br>定时时间异常%s" % msg
        else:
            cron.status = 'open'
            cron.save()
            return "<br>下次运行时间:"+str(cls._getcronmanager().get_job(cronid).next_run_time).split('+')[0]






    @classmethod
    def delcrontab(cls,planid):
        cronid = Plan.objects.get(id=planid).__str__()
        try:
            cron = Crontab.objects.get(plan_id=planid)
            cron.status='close'
            cron.save()
            cls._removecrontab(cronid)
            for i in cls.querytask():
                print(i)
        except:
            pass

    @classmethod
    def recovertask(cls):
        """
        服务重启时 如有开启定时任务自动加入 与表Crontab状态一致
        """
        print("定时任务开始重新装载...")
        opentasks = list(Crontab.objects.filter(status='open'))
        for task in opentasks:
            planid = task.plan_id
            cronid = Plan.objects.get(id=planid).__str__()
            cfg = cls.getcron(task.value)
            try:
                cls._addcrontab(cronRun, args=[planid], id=cronid, **cfg)
            except:
                pass
        print("定时任务重新装载完成...")
        for i in cls.querytask():
            print(i)

    @classmethod
    def _getcronmanager(cls):
        # cls.__lock.locked()
        from apscheduler.schedulers.background import BackgroundScheduler
        if cls.__cronmanager is None:
            if cls.__cronmanager is None:
                cls.__cronmanager = BackgroundScheduler()
                cls.__cronmanager.start()
                print("新建任务调度器并开启..")

        # cls.__lock.release()

        return cls.__cronmanager

    @classmethod
    def _addcrontab(cls, func, args=None, id='', **kw):
        try:
            cls._getcronmanager().add_job(
                func,
                args=args,
                id=id,
                trigger='cron',
                # year=kw.get('year', '*'),
                month=kw.get('month', '*'),
                day=kw.get('day', '*'),
                hour=kw.get('hour', '*'),
                minute=kw.get('minute', '*'),
                coalesce=True
            )
            msg=''
        except:
            msg = traceback.format_exc()
            print("添加定时任务失败%s" % traceback.format_exc())
        return msg


    @classmethod
    def _removecrontab(cls, cronid):
        try:
            cls._getcronmanager().remove_job(cronid)
            print("移除定时任务[%s]" % cronid)
        except:
            print(traceback.format_exc())
            print("移除定时任务[%s]失败！" % cronid)

    @classmethod
    def _stopcronmanager(cls, wait=False):
        try:
            cls._getcronmanager().shutdown(wait=wait)
            print("关闭定时调度器")
        except:
            raise RuntimeError("关闭定时任务调度器error")
