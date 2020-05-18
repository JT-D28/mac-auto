#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-10-12 09:42:34
# @Author  : Blackstone
# @to      :定时任务调度
import traceback

from .models import Crontab, Plan
from .invoker import runplan
from .core import gettaskid
import threading


def cronRun(planid):
    plan = Plan.objects.get(id=planid)
    taskid = gettaskid(plan.__str__())
    threading.Thread(target=runplan, args=('定时任务', taskid, planid, 1, '定时任务', 'plan_' + str(planid))).start()


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
        if times[2] != '*' and times[3] == '*':
            times[3] = '0'
        if times[1] != '*' and times[2] == '*':
            times[2] = '0'
            times[3] = '0'
        if times[0] != '*' and times[1] == '*':
            times[1] = '0'
            times[2] = '0'
            times[3] = '0'
        return {
            'month': times[0],
            'day': times[1],
            'hour': times[2],
            'minute': times[3]
        }

    @classmethod
    def addcrontab(cls,planid):
        cronid = Plan.objects.get(id=planid).__str__()
        existJobs=cls.querytask()
        cron = Crontab.objects.get(plan_id=planid)
        for job in existJobs:
            if cronid == job.id:
                cls._removecrontab(cronid)
                break
        cls._addcrontab(cronRun, args=[planid], id=cronid, **cls.getcron(cron.value))
        cron.status='open'
        cron.save()
        for i in cls.querytask():
            print(i)


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
            cls._addcrontab(cronRun, args=[planid], id=cronid, **cfg)
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
        except:
            print("添加定时任务[id=%s]失败" % traceback.format_exc())
            pass

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
