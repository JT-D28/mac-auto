#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-09-27 14:45:12
# @Author  : Blackstone
# @to      :
import ast, threading
import asyncio
from itertools import chain
from urllib import parse
from bson.objectid import ObjectId
from django.conf import settings
from django.db import connection
from django.db.models import Q
from django.http import JsonResponse

from ME2 import configs, urlmap

from manager.context import Me2Log as logger
from manager.context import add_mock as mock,clear_mock
from ME2.settings import logme, BASE_DIR

from login.models import *
from manager.models import *

from .core import ordered, Fu, getbuiltin, EncryptUtils, genorder, simplejson
from .db import Mysqloper
from .context import set_top_common_config, viewcache, get_task_session, \
    clear_task_session, get_friendly_msg, setRunningInfo, getRunningInfo, get_space_dir

import re, traceback, time, threading, json, warnings, datetime, socket
import copy, base64,os

from .operate.generateReport import dealDeBuginfo, dealruninfo
from .operate.mongoUtil import Mongo
from .operate.sendMail import processSendReport

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

##支持的运算
_op = ('>=', '<=', '!=', '==', '>', '<', '$')
# 用户变量缓存 key=user.varname
__varcache = dict()

# 记录变量名的替换过程 方便追溯
# 单个表达式替换时记录 计算完成后释放
# __replace_route=dict()

# 计划运行时 用户临时变量存放 结束清除
_tempinfo = dict()

##任务集
# {{'username1':{'taskid1':['planid1','planid2']}}}
_taskmap = dict()


def db_connect(config, timeout=5):
    """
    测试数据库连接
    """
    logger.info('==测试数据库连接===')
    
    conn = None
    
    try:
        
        # logger.info(len(conname),len(conname.strip()))
        description = config['description']
        dbtype = config['dbtype']
        dbname = config['dbname']
        # oracle不需要这两项
        host = config['host']
        port = config['port']
        #
        user = config['username']
        pwd = config['password']
        
        # logger.info("=>没查到可用配置,准备新配一个")
        logger.info("数据库类型=>", dbtype)
        logger.info("数据库名(服务名|SID)=>", dbname)
        logger.info("数据库地址=>", host, port)
        logger.info("数据库账号=>", user, pwd)
        
        if dbtype.lower() == 'oracle_servicename':
            import cx_Oracle
            
            dsn = cx_Oracle.makedsn(host, int(port), service_name=dbname)
            conn = cx_Oracle.connect(user, pwd, dsn)
        
        elif dbtype.lower() == 'oracle_sid':
            import cx_Oracle
            dsn = cx_Oracle.makedsn(host, int(port), sid=dbname)
            conn = cx_Oracle.connect(user, pwd, dsn)
        
        elif dbtype.lower() == 'mysql':
            import pymysql
            conn = pymysql.connect(db=dbname, host=host, port=int(port), user=user, password=pwd, charset='utf8mb4')
        
        elif dbtype.lower() == 'pgsql':
            import psycopg2 as pg2
            conn = pg2.connect(database=dbname, user=user, password=pwd, host=host, port=int(port))
        
        
        else:
            return ('fail', '连接类型不支持')
        
        return ('success', '数据库[%s]连接成功!.' % description)
    
    
    except:
        error = traceback.format_exc()
        logger.info('error=>', error)
        return ('error', '连接异常->%s' % get_friendly_msg(error))



def check_user_task():
    def run():
        for username, tasks in _taskmap.items():
            for taskid, plans in tasks.items():
                for planid in plans:
                    runplan(planid)


def _get_down_case_leaf_id(caseids,final,cur=None,ignore=False):
  
    '''
    获取指定case节点最下游caseID
    '''
    if isinstance(caseids, (int,)):
        caseids = [caseids]
    for caseid in caseids:
        e = Order.objects.filter(kind='case_case', main_id=caseid,isdelete=0)
        if e.exists() and not ignore:
            _get_down_case_leaf_id([x.follow_id for x in e],final, cur)
        else:
            cur.add(caseid)

        for o in Order.objects.filter(kind='case_step', main_id=caseid, isdelete=0):
            for i in Order.objects.filter(kind='step_business', main_id=o.follow_id, isdelete=0):
                final.add(i.follow_id)


def _get_upper_case_leaf_id(caseid):
    '''
    获取指定case节点最上游caseID
    '''
    e = Order.objects.filter(kind='case_case', follow_id=caseid,isdelete=0)
    if not e.exists():
        return caseid
    else:
        cur = e[0].main_id
        return _get_upper_case_leaf_id(cur)


def _get_final_run_node_id(startnodeid,ignore=False):
    '''
    获取实际需要执行的测试点ID列表
    '''
    final = set()
    try:
        #logger.info('开始获取运行节点[%s]执行计划id ' % startnodeid)
        
        kind = startnodeid.split('_')[0]
        nid = startnodeid.split('_')[1]
        if kind == 'plan':
            # 获取预先执行的用例
            caseslist, des = beforePlanCases(nid)
            # logger.info('获取运行前节点[%s]' % des)
            
            ol = Order.objects.filter(kind='plan_case', main_id=nid,isdelete=0)
            ol = chain(caseslist, ol)
            for o in ol:
                caseid = o.follow_id
                down_ids = set()
                _get_down_case_leaf_id(caseid, final,down_ids)
                for cid in down_ids:
                    stepids = [x.follow_id for x in Order.objects.filter(kind='case_step', main_id=cid,isdelete=0)]
                    for stepid in stepids:
                        final = final|set([x.follow_id for x in
                                         Order.objects.filter(kind='step_business', main_id=stepid,isdelete=0)])
        
        elif kind == 'business':
            final.add(int(nid))
        elif kind == 'step':
            ob = Order.objects.filter(kind='step_business', main_id=nid,isdelete=0)
            for o in ob:
                final.add(o.follow_id)
        
        elif kind == 'case':
            # case-step
            ob = Order.objects.filter(kind='case_step', main_id=nid,isdelete=0)
            stepids = []
            for o in ob:
                stepid = o.follow_id
                os = Order.objects.filter(kind='step_business', main_id=stepid,isdelete=0)
                for o0 in os:
                    final.add(o0.follow_id)
            ##case-case
            if not ignore:
                final_leaf_case_ids = set()
                _get_down_case_leaf_id([nid],final ,final_leaf_case_ids)
                logger.info('节点[%s]获取最终case子节点待运行:'%nid, final_leaf_case_ids)
                for caseid in final_leaf_case_ids:
                    final=final|_get_final_run_node_id('case_%s'%caseid,ignore=True)


        # logger.info('获取最终执行测试点结果:', final)
    except:
        logger.error('获取最终执行测试点异常:', traceback.format_exc())
    finally:
        return final


def get_run_node_plan_id(startnodeid):
    '''
    获取运行节点归属计划ID
    '''
    logger.info('startndoe ID:', startnodeid)
    kind = startnodeid.split('_')[0]
    nid = startnodeid.split('_')[1]
    if kind == 'plan':
        return nid
    
    elif kind == 'case':
        caseid = _get_upper_case_leaf_id(nid)
        planid = Order.objects.get(kind='plan_case', follow_id=caseid,isdelete=0).main_id
        return planid
    
    elif kind == 'step':
        case_id = Order.objects.get(kind='case_step', follow_id=nid,isdelete=0).main_id
        logger.info('caseid:', case_id)
        up_case_id = _get_upper_case_leaf_id(case_id)
        logger.info('upper caseid:', up_case_id)
        planid = Order.objects.get(kind='plan_case', follow_id=up_case_id,isdelete=0).main_id
        return planid
    elif kind == 'business':
        stepid = Order.objects.get(kind='step_business', follow_id=nid,isdelete=0).main_id
        return get_run_node_plan_id('step_%s' % stepid)


def get_node_upper_case(nodeid):
    kind,id = nodeid.split("_")
    if kind == 'case':
        return id
    elif kind == 'step':
        return Order.objects.get(kind='case_step', follow_id=id,isdelete=0).main_id
    elif kind == 'business':
        stepid = Order.objects.get(kind='step_business', follow_id=id,isdelete=0).main_id
        return get_node_upper_case('step_%s' % stepid)



def _runcase(username, taskid, case0, plan, planresult, runkind, startnodeid=None, L=None,proxy={}):

    from tools.mock import TestMind
    groupskip = []
    caseresult = []
    
    dbid = getDbUse(taskid, case0.db_id)
    if dbid:
        desp = DBCon.objects.get(id=int(dbid)).description
        set_top_common_config(taskid, desp, src='case')
    
    case_run_nodes=_get_final_run_node_id('case_%s'%case0.id)
    subflag=True if set(case_run_nodes).issubset(L) else False

    logger.info('节点[%s]下有测试点ID：%s'%(case0.description,case_run_nodes))
    # logger.info('传入的最终执行测试点ID：%s'%L)
    if subflag:
        viewcache(taskid, "开始执行用例[<span id='case_%s' style='color:#FF3399'>%s</span>]" %(case0.id,case0.description))
    steporderlist = ordered(list(Order.objects.filter(Q(kind='case_step') | Q(kind='case_case'), main_id=case0.id)))

    ##case执行次数
    casecount = int(case0.count) if case0.count is not None else 1
    color_res = {
        'success': 'green',
        'fail': 'red',
        'skip': 'orange',
        'omit': 'green',
    }
    ##
    for lid in range(0, casecount):
        for o in steporderlist:
            if o.kind == 'case_case':
                case = Case.objects.get(id=o.follow_id)
                _runcase(username, taskid, case, plan, planresult, runkind, startnodeid=startnodeid, L=L,proxy=proxy)
                continue
            
            stepid = o.follow_id
            try:
                step = Step.objects.get(id=stepid)
                stepcount = step.count

                if stepcount > 0:
                    # 步骤执行次数>0
                    for ldx in range(0, stepcount):
                        businessorderlist = ordered(list(Order.objects.filter(kind='step_business', main_id=stepid,isdelete=0)))
                        # logger.info('bbb=>',businessorderlist)
                        for order in businessorderlist:
                            groupid = order.value.split(".")[0]
                            # step=Step.objects.get(id=order.follow_id)
                            start = time.time()
                            spend = 0

                            businessdata = BusinessData.objects.get(id=order.follow_id)
                            if order.follow_id not in L:
                                continue
                            if groupid not in groupskip:
                                result, error = _step_process_check(username, taskid, order ,proxy)
                                spend = int((time.time() - start) * 1000)
                                
                                if result not in ('success', 'omit'):
                                    groupskip.append(groupid)
                            else:

                                if businessdata.count == 0:
                                    result, error = 'omit', "测试点[%s]执行次数=0 略过." % businessdata.businessname
                                else:
                                    result, error = 'skip', 'skip'
                            
                            # 保存结果
                            try:
                                logger.info("准备保存结果===")
                                detail = ResultDetail(taskid=taskid, plan=plan, case=case0,
                                                      step=step,
                                                      businessdata=businessdata,
                                                      result=result,
                                                      error=error, spend=spend, loop_id=1, is_verify=runkind)

                                detail.save()
                                logger.info('保存结果=>', detail)
                            except:
                                logger.info('保存结果异常=>', traceback.format_exc())
                            caseresult.append(result)

                            result = "<span id='step_%s' class='layui-bg-%s'>%s</span>" % (stepid,color_res.get(result, 'orange'), result)

                            if 'omit' not in result:
                                stepinfo = "<span style='color:#FF3399' id='step_%s' caseid='%s' casedes='%s'>%s</span>"%(step.id,case0.id,case0.description,step.description)
                                businessinfo = "<span style='color:#FF3399' id='business_%s'>%s</span>"%(businessdata.id,businessdata.businessname)
                                error = '   原因=>%s' % error if 'success' not in result else ''
                                viewcache(taskid, "步骤[%s]=>测试点[%s]=>执行结果%s   %s" % (stepinfo,businessinfo,result,error))
            
            except:
                print(traceback.format_exc())
                continue
    
    casere = (len([x for x in caseresult if x in ('success', 'omit')]) == len([x for x in caseresult]))
    planresult.append(casere)

    if subflag:
        if casere  :
            viewcache(taskid,"结束用例[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-green'>success</span>" % case0.description)
        else:
            viewcache(taskid,"结束用例[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-red'>fail</span>" % case0.description)



def getDbUse(taskid, dbname):
    scheme = getRunningInfo(base64.b64decode(taskid).decode().split('_')[0], 'dbscheme')
    try:
        dbid = DBCon.objects.get(scheme=scheme, description=dbname).id
    except:
        try:
            dbid = DBCon.objects.get(scheme='全局', description=dbname).id
        except:
            dbid = None
    return dbid


def beforePlanCases(planid):
    caseslist = []
    before_des = ''
    before_plan = Plan.objects.get(id=planid).before_plan
    if before_plan not in [None, '']:
        before_des, before_kind, before_id = before_plan.split("@")
        before_id = base64.b64decode(before_id).decode('utf-8')
        if before_kind == 'plan':
            caseslist = Order.objects.filter(main_id=before_id, kind='plan_case',isdelete=0)
        elif before_kind == 'case':
            caseslist = Order.objects.filter(follow_id=before_id, kind='plan_case',isdelete=0)
    return caseslist, before_des


def runplan(callername, taskid, planid, runkind, startnodeid=None):
    plan = Plan.objects.get(id=planid)
    dbscheme = plan.schemename
    setRunningInfo(planid, taskid, runkind, dbscheme)
    viewcache(taskid, "=======正在初始化任务中=======")
    logger.info('开始执行计划：', plan)
    logger.info('startnodeid:', startnodeid)
    L = _get_final_run_node_id(startnodeid)
    logger.info('准备传入的L:', L)
    logger.info('runkind:',runkind)
    starttime = time.time()
    groupskip = []
    username = callername
    viewcache(taskid,"=======计划【%s】开始执行[%s任务]【<span style='color:#FF3399'>%s</span>】,使用数据连接配置【%s】====" % (
                  plan.description, {"1": "验证", "2": "调试", "3": "定时"}[runkind], taskid, dbscheme))
    if plan.proxy:
        proxy = {'http': plan.proxy}
        viewcache(taskid, "请求代理：%s" % (plan.proxy))
    else:
        proxy = {}
    try:
        dbid = getDbUse(taskid, plan.db_id)
        if dbid:
            logger.info('plan dbid=>', dbid)
            desp = DBCon.objects.get(id=int(dbid)).description
            set_top_common_config(taskid, desp, src='plan')

        if startnodeid.split('_')[0] == 'plan':
            caseslist = []
            beforeCases, before_des = beforePlanCases(planid)
            caseslist.extend(ordered(list(beforeCases)))
            viewcache(taskid, "加入前置计划/用例[<span style='color:#FF3399'>%s</span>]" % (before_des))
            caseslist.extend(ordered(list(Order.objects.filter(main_id=planid, kind='plan_case',isdelete=0))))
            cases = [Case.objects.get(id=x.follow_id) for x in caseslist]
        else:
            caseid = get_node_upper_case(startnodeid)
            cases = [Case.objects.get(id=caseid)]

        logger.info('cases=>', cases)
        planresult = []

        for case in cases:
            if case.count == 0 or case.count == '0':
                continue
            else:
                logger.info('runcount:', case.count)
                _runcase(username, taskid, case, plan, planresult, runkind, startnodeid=startnodeid, L=L,proxy=proxy)

        planre = (len([x for x in planresult]) == len([x for x in planresult if x == True]))
        if planre:
            plan.last, color = 'success', 'green'
        else:
            plan.last, color = 'fail', 'red'
        plan.save()
        viewcache(taskid,"结束计划[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-%s'>%s</span>" % (
                      plan.description, color, plan.last))
        spendtime = time.time() -starttime
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(dealruninfo(planid,taskid,{'spend':spendtime,'dbscheme':dbscheme,'planname':plan.description,
                                                           'user':username,'runkind':runkind},startnodeid))
        # 清除请求session

    except Exception as e:
        logger.error('执行计划未知异常：', traceback.format_exc())
        viewcache(taskid,'执行计划未知异常[%s]' % traceback.format_exc())

    finally:
        clear_mock(callername)
        clear_task_session('%s_%s' % (taskid, callername))

        setRunningInfo(planid, taskid, '0', dbscheme)
        processSendReport(taskid, plan.mail_config_id, callername)
        clear_data(callername, _tempinfo)


def _step_process_check(callername, taskid, order ,proxy):
    """
    return (resultflag,msg)
    order.follw_id:业务数据id
    """
    try:
        user = User.objects.get(name=callername)
        businessdata = BusinessData.objects.get(id=order.follow_id)
        timeout = 60 if not businessdata.timeout else businessdata.timeout
        
        if businessdata.count == 0:
            return ('omit', "测试点[%s]执行次数=0 略过." % businessdata.businessname)
        preplist = businessdata.preposition.split("|") if businessdata.preposition is not None else ''
        postplist = businessdata.postposition.split("|") if businessdata.postposition is not None else ''
        db_check = businessdata.db_check
        itf_check = businessdata.itf_check
        status, paraminfo = BusinessData.gettestdataparams(order.follow_id)
        
        # logger.info('bbid=>',businessdata.id)
        status1, step = BusinessData.gettestdatastep(businessdata.id)
        
        if status is not 'success':
            return (status, paraminfo)
        if status1 is not 'success':
            return (status1, step)
        
        viewcache(taskid, "--" * 100)
        viewcache(taskid,"开始执行步骤[<span style='color:#FF3399' id='step_%s'>%s</span>] 测试点[<span style='color:#FF3399' id='business_%s'>%s</span>]" % (
                      step.id,step.description,businessdata.id, businessdata.businessname))
        
        dbid = getDbUse(taskid, step.db_id)

        if dbid:
            desp = DBCon.objects.get(id=int(dbid)).description
            set_top_common_config(taskid, desp, src='step')
        
        # 前置操作
        status, res = _call_extra(user, preplist, taskid=taskid, kind='前置操作')  ###????
        if status is not 'success':
            return (status, res)
        
        if step.step_type == "interface":
            viewcache(taskid, "数据校验配置=>%s" % db_check)
            viewcache(taskid, "接口校验配置=>%s" % itf_check)
            headers = []
            
            text, statuscode, itf_msg = '', -1, ''
            
            if step.content_type == 'xml':
                if re.search('webservice', step.url):
                    headers, text, statuscode, itf_msg = _callinterface(taskid, user, step.url, str(paraminfo), 'post',
                                                                        None, 'xml', step.temp, timeout,proxy)
                    if not itf_msg:
                        text = text.replace('&lt;', '<')
                        
                        text = re.findall('(?<=\?>).*?(?=</ns1:out>)', text, re.S)[0]
                        text = '\n' + text
                    else:
                        return ('error', itf_msg)
                else:
                    text, statuscode, itf_msg = _callsocket(taskid, user, step.url, body=str(paraminfo))
            else:
                
                headers, text, statuscode, itf_msg = _callinterface(taskid, user, step.url, str(paraminfo), step.method,
                                                                    step.headers, step.content_type, step.temp,
                                                                    timeout,proxy)
            if text.lstrip().startswith('<!DOCTYPE html>'):
                viewcache(taskid,"<span style='color:#009999;'>请求响应=><xmp style='color:#009999;'>内容为HTML，不显示</xmp></span>")
            else:
                viewcache(taskid,"<span style='color:#009999;'>请求响应=><xmp style='color:#009999;'>%s</xmp></span>" % text)
            
            if len(str(statuscode)) == 0:
                return ('fail', itf_msg)
            elif statuscode == 200:
                
                ##后置操作
                status, res = _call_extra(user, postplist, taskid=taskid, kind='后置操作',response_text=text)  ###????
                if status is not 'success':
                    return (status, res)
                
                if db_check:
                    res, error = _compute(taskid, user, db_check, type="db_check")
                    if res is not 'success':
                        logger.info('################db_check###############' * 20)
                        return ('fail', error)
                
                if itf_check:
                    if step.content_type in ('json', 'urlencode','formdata'):
                        res, error = _compute(taskid, user, itf_check, type='itf_check', target=text,
                                              parse_type='json', rps_header=headers)
                    else:
                        res, error = _compute(taskid, user, itf_check, type='itf_check', target=text,
                                              parse_type='xml', rps_header=headers)
                    
                    if res is not 'success':
                        return ('fail', error)
                
                return ('success', '')
            else:
                return ('fail', 'statuscode=%s' % statuscode)
            

        elif step.step_type == "function":
            viewcache(taskid, "数据校验配置=>%s" % db_check)

            viewcache(taskid, "调用函数=>%s" % step.body)
            
            logger.info('关联id=>', step.related_id)
            res, msg = _callfunction(user, step.related_id, step.body, paraminfo, taskid=taskid)
            viewcache(taskid, "函数执行结果=>%s" %res)
            
            if res is not 'success':
                viewcache(taskid, "函数执行报错信息:%s" %msg)
                return res, msg
            
            status, res = _call_extra(user, postplist, taskid=taskid, kind='后置操作')
            if status is not 'success':
                return (status, res)
            
            if db_check:
                res, error = _compute(taskid, user, db_check, type='db_check')
                if res is not 'success':
                    return ('fail', error)
                else:
                    return ('success', '')
            else:
                return ('success', '')
    
    except Exception as e:
        # traceback.logger.info_exc()
        logger.info(traceback.format_exc())
        return ("error", "执行任务[%s] 未处理的异常[%s]" % (taskid, traceback.format_exc()))






def _callsocket(taskid, user, url, body=None, timeout=1024):
    """
    xml报文请求
    """
    
    def _getback(sock):
        recvdata = ''
        # sock.setblocking(0)
        sock.settimeout(timeout)
        try:
            lenstr = sock.recv(25)
            recvdata += lenstr.decode('GBK')
            data = sock.recv(int(lenstr[15:23]))
            data = data.decode('GBK')
            recvdata += data
        except:
            logger.info(traceback.format_exc())
        
        finally:
            sock.close()
            return recvdata
    
    cs = None
    try:
        
        url_rv = _replace_variable(user, url, taskid=taskid)
        if url_rv[0] is not 'success':
            return ('', '', url_rv[1])
        url_rp = _replace_property(user, url_rv[1], taskid=taskid)
        if url_rp[0] is not 'success':
            return ('', '', url_rp[1])
        
        url = url_rp[1]
        
        ##
        body_rv = _replace_variable(user, body, taskid=taskid);
        if body_rv[0] is not 'success':
            return ('', '', body_rv[1])
        body_rp = _replace_property(user, body_rv[1], taskid=taskid)
        if body_rp[0] is not 'success':
            return ('', '', body_rp[1])
        
        body = body_rp[1]
        
        cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # cs.setblocking(False)
        # socket.setdefaulttimeout(30)
        cs.settimeout(timeout)
        url = url.replace('http://', '')
        host = url.split(':')[0].strip()
        port = url.split(':')[1].strip()
        time.sleep(2)
        cs.connect((str(host), int(port)))
        # ms=re.findall('\<\/.*?\>', body)
        # for m in ms:
        #   body=body.replace(m, m+'\n')
        
        length = str(len(body.encode('GBK'))).rjust(8)
        logger.info('Content-Length=>', length)
        sendmsg = 'Content-Length:' + str(length) + '\r\n' + body
        
        viewcache(taskid, '执行socket请求')
        viewcache(taskid, "<span style='color:#009999;'>请求IP=>%s</span>" % host)
        viewcache(taskid, "<span style='color:#009999;'>请求端口=>%s</span>" % port)
        viewcache(taskid,
                  "<span style='color:#009999;'>发送报文=><xmp style='color:#009999;'>%s</xmp></span>" % sendmsg)

        cs.sendall(bytes(sendmsg, encoding='GBK'))

        # recv_bytes=cs.recv(1024)
        # responsexml=b''

        # while True:
        #   recv_bytes =cs.recv(1024)
        #   logger.info(2222)
        #   responsexml+=recv_bytes
        #   if not len(recv_bytes):
        #       break;

        return _getback(cs), 200, ''
    except:
        if cs:
            cs.close()
        err = traceback.format_exc()
        logger.info(err)
        return ('', '', err)


def _getfiledict(paraminfo):
    pdict = dict()
    for k, v in eval(paraminfo).items():
        if not k.__contains__('file'):
            pdict[k] = (None, v)
        else:
            if isinstance(v, (str,)):
                filepath = os.path.join(get_space_dir(), v)
                if os.path.exists(filepath):
                    pdict[k] = (v, open(filepath, 'rb'))
                elif os.path.exists(os.path.join(get_space_dir(), '默认', v)):
                    pdict[k] = (v, open(os.path.join(get_space_dir(), '默认', v),'rb'))
                else:
                    return 'fail', ''
    return 'success', pdict


def _callinterface(taskid, user, url, body=None, method=None, headers=None, content_type=None, props=None,
                   timeout=None,proxy={}):
    """
    返回(rps.text,rps.status_code,msg)
    """

    # url data headers过滤
    viewcache(taskid, "执行[%s]请求=>"%method)

    viewcache(taskid, "<span style='color:#009999;'>content_type=>%s</span>" % content_type)
    viewcache(taskid, "<span style='color:#009999;'>原始url=>%s</span>" % url)


    url_rp = _replace_property(user, url)
    if url_rp[0] is not 'success':
        return ('', '', '', url_rp[1])
    url_rv = _replace_variable(user, url_rp[1], taskid=taskid)
    if url_rv[0] is not 'success':
        return ('', '', '', url_rv[1])

    url_rf = ''
    if len(url_rv[1].split('?')) > 1:
        # logger.info('$' * 1000)
        url_params = url_rv[1].split('?')[1]
        logger.info('url_params=>', url_params)
        sep = _replace_function(user, url_params, taskid=taskid)
        if sep[0] is not 'success':
            return ('', '', '', sep[1])

        url_rf = ('success', url_rv[1].split('?')[0] + '?' + sep[1])



    else:
        url_rf = _replace_function(user, url_rv[1], taskid=taskid)
    if url_rf[0] is not 'success':
        return ('', '', '', url_rf[1])

    url = url_rf[1]
    url = urlmap.getmenhu(url, taskid, user.name)
    viewcache(taskid, "<span style='color:#009999;'>url=>%s</span>" % url)

    viewcache(taskid,
              "<span style='color:#009999;'>原始参数=><xmp style='color:#009999;'>%s</xmp></span>" % body)
    data_rp = _replace_property(user, body)
    if data_rp[0] is not 'success':
        return ('', '', '', data_rp[1])
    data_rv = _replace_variable(user, data_rp[1], taskid=taskid)
    if data_rv[0] is not 'success':
        return ('', '', '', data_rv[1])

    data_rf = _replace_function(user, data_rv[1], taskid=taskid)
    if data_rf[0] is not 'success':
        return ('', '', '', data_rf[1])

    body = data_rf[1]

    viewcache(taskid,
              "<span style='color:#009999;'>变量替换后参数=><xmp style='color:#009999;'>%s</xmp></span>" % body)

    # body=json.loads(body)

    # logger.info(type(headers))
    viewcache(taskid, "<span style='color:#009999;'>用户定义请求头=>%s</span>" % (headers))
    if headers is None or len(headers.strip()) == 0:
        headers = {}

    headers_rp = _replace_property(user, str(headers))

    if headers_rp[0] is not 'success':
        return ('', '', '', headers_rp[1])
    headers_rv = _replace_variable(user, headers_rp[1], taskid=taskid)
    if headers_rv[0] is not 'success':
        return ('', '', '', headers_rv[1])

    try:
        headers = eval(headers_rv[1])
    except:
        return ('', '', '', '接口请求头格式不对 请检查')

    ##
    default = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36"}
    viewcache(taskid, "<span style='color:#009999;'>headers=>%s</span>" % {**default, **headers})
    viewcache(taskid, "<span style='color:#009999;'>method=>%s</span>" % method)

    if content_type == 'json':

        default["Content-Type"] = 'application/json;charset=UTF-8'
        body=body.replace("'null'",'null').replace('"null"','null')
        body = body.encode('utf-8')
    # body = json.dumps(eval(body))

    elif content_type == 'xml':
        default["Content-Type"] = 'application/xml'
        body = body.encode('utf-8')
    elif content_type == 'urlencode':
        default["Content-Type"] = 'application/x-www-form-urlencoded;charset=UTF-8'
        try:
            if body.startswith("{") and not body.startswith("{{"):
                body = body.replace('\r', '').replace('\n', '').replace('\t', '')
                # old=old.replace('"null"','null').replace("'null'",'null')
                print('vbody:',body)
                body = parse.urlencode(ast.literal_eval(body))

            body = body.encode('UTF-8')


        except:
            logger.info('参数转化异常：', traceback.format_exc())
            return ('', '', '', 'urlencode接口参数格式不对 请检查..')

    elif content_type == 'xml':
        isxml = 0
    elif content_type == 'formdata':
        state, body = _getfiledict(str(body))
        if state == 'fail':
            viewcache(taskid, "<span style='color:#009999;'>%s</span>" % "上传文件不存在，请检查")
            return ('', '', '', '上传文件不存在，请检查')
    else:
        raise NotImplementedError("content_type=%s没实现" % content_type)

    session = get_task_session('%s_%s' % (taskid, user.name))
    params = None
    data = None
    files = None

    if method == 'get':
        params = body
    elif content_type == 'formdata':
        files = body
    else:
        data = body
    try:
        rps = session.request(method, url, headers={**default, **headers}, params=params, data=data,files=files,timeout=timeout,proxies=proxy)
    except:
        err = traceback.format_exc()
        if 'requests.exceptions.ConnectTimeout' in err:
            msg = '请求超时 已设置超时时间%ss' % timeout
            return ({}, msg, 200, "")
        else:
            msg = '请求异常:%s' % err
            return ('', '', '', msg)

    status, err = _find_and_save_property(taskid,user, props, rps.text)

    if status is not 'success':
        return ('', '', '', err)

    return (rps.headers, rps.text, rps.status_code, "")



def _callfunction(user, functionid, call_method_name, call_method_params, taskid=None):
    """
    内置方法 functionid=None
    call_method_params ->tuple
    返回(调用结果,msg)
    """
    f = None
    builtin = None
    # methodname=re.findall("(.*?)\(.*?\)", call_str.strip())[0]
    methodname = call_method_name

    builtinmethods = [x.name for x in getbuiltin()]
    builtin = (methodname in builtinmethods)

    try:
        logme.warn('获取自定义函数id %s isbuiltin:%s' % (functionid,builtin))
        f = Function.objects.get(id=functionid)
        logme.warn('获取自定义函数%s' % f.__str__())
    except:
        pass

    logger.info('params:{}'.format(call_method_params))
    call_method_params.append("taskid='%s'" % taskid)
    call_method_params.append("callername='%s'" % user.name)
    # call_method_params.append("location='%s'"%get_space_dir(user.name))
    call_method_params = [x for x in call_method_params if x]

    call_str = '%s(%s)' % (call_method_name, ','.join(call_method_params))

    logger.info('测试函数调用=>', call_str)
    ok = _replace_variable(user, call_str, src=1, taskid=taskid)
    if re.search(r"\(.*?(?=,taskid)", ok[1]):
        viewcache(taskid,"替换变量后的函数参数=>%s" % re.search(r"(?<=\().*?(?=,taskid)", ok[1]).group())

    res, call_str = ok[0], ok[1]
    if res is not 'success':
        return (res, call_str)

    return Fu.call(f, call_str, builtin=builtin)


def _call_extra(user, call_strs, taskid=None, kind='前置操作',response_text=None):

    f = None
    builtinmethods = [x.name for x in getbuiltin()]
    for s in call_strs:
        if not s.strip():
            continue

        if s == 'None' or s is None:
            continue

        viewcache(taskid, "执行%s:%s" % (kind, s))
        status, s = _replace_variable(user, s, src=1, taskid=taskid,responsetext=response_text)
        logger.info('变量处理后的callstr:',s)
        if status is not 'success':
            return (status, s)

        s=s.replace('\n', '')

        methodname = ''
        try:
            methodname = re.findall('(.*?)\(', s)[0]
            argstr = re.findall('{}\((.*)\)'.format(methodname), s)[0]
            if argstr.strip():
                argstr = argstr + ','
            logger.info('拼sql:',argstr)
            argstr = argstr + "taskid='%s',callername='%s'" % (taskid,user.name)
            call_str = '%s(%s)' % (methodname, argstr)

        ##????????????????????????????
        except:
            return ('error', '解析%s[%s]失败[%s]' % (kind, s, traceback.format_exc()))

        isbuiltin = (methodname in builtinmethods)
        if isbuiltin == False:
            flag = Fu.tzm_compute(s, '(.*?)\((.*?)\)')

            al = list(Function.objects.filter(flag=flag))
            if len(al) == 0:
                flag = Fu.tzm_compute(s, '(.*?)\(.*?\)')
                try:
                    f = Function.objects.get(flag=flag)
                except:
                    return ('fail', '库中没发现可用函数[%s]' % methodname)
            elif len(al) == 1:
                f = al[0]
            else:
                f = al[0]
                viewcache(taskid, "<span style='color:#FF3333;'>函数库中发现多个匹配函数 这里使用第一个匹配项</span>")

        logger.info('invoker.py 传入的sql：',call_str)
        status, res = Fu.call(f, call_str, builtin=isbuiltin)
        if status == 'success':
            viewcache(taskid, "执行[<span style='color:#009999;'>%s</span>]%s【成功】" % (kind, s))
        else:
            viewcache(taskid, "执行[<span style='color:#009999;'>%s</span>]%s【失败】" % (kind, s))
            return (status, res)

    return ('success', '操作[%s]全部执行完毕' % call_strs)



def _compute(taskid, user, checkexpression, type=None, target=None, parse_type='json', rps_header=None):
    """
    计算各种校验表达式
    多个时 分隔符 |
    返回(success/fail,执行结果/消息)
    """
    try:
        # expectedexpression=_legal(checkexpression)
        expectedexpression = checkexpression
        checklist = [x for x in expectedexpression.strip().split("|") if len(x) > 0]
        resultlist = []
        if type == 'db_check':
            for item in checklist:
                old = item
                item = _legal(item)
                ress = _eval_expression(user, item, taskid=taskid)
                logger.info('ress1=>', ress)

                if ress[0] is 'success':
                    viewcache(taskid,
                              "校验表达式[<span style='color:#009999;'>%s</span>] 结果[<span style='color:#009999;'>%s</span>]" % (
                                  old, ress[0]))
                else:
                    viewcache(taskid,
                              "校验表达式[<span style='color:#FF6666;'>%s</span>] 结果[<span style='color:#FF6666;'>%s</span>] 原因[校验表达式[<span style='color:#FF6666;'>%s</span>]" % (
                                  old, ress[0], ress[1]))

                resultlist.append(ress)

        elif type == "itf_check":
            #
            for item in checklist:
                logger.info('check', item)
                old = item
                item = _legal(item)
                target = target.replace('null', "'None'").replace('true', "'True'").replace('false', "'False'")
                ress = _eval_expression(user, item, need_chain_handle=True, data=target, taskid=taskid,
                                        parse_type=parse_type, rps_header=rps_header)
                logger.info('ress2=>', ress)
                if ress[0] is 'success':
                    viewcache(taskid,"校验表达式[<span style='color:#009999;'>%s</span>] 结果[<span style='color:#009999;'>%s</span>]" % (
                                  old, ress[0]))
                else:
                    msg = ress[1]
                    if msg is False:
                        msg = '表达式不成立'
                    viewcache(taskid,"校验表达式[<span style='color:#FF6666;'>%s</span>] 结果[<span style='color:#FF6666;'>%s</span>] 原因[<span style='color:#FF6666;'>%s</span>]" % (
                                  old, ress[0], msg))

                resultlist.append(ress)


        else:
            return ('error', '计算表达式[%s]异常[_compute type传参错误]' % checkexpression)
        # logger.info("结果列表=>",resultlist)
        # errmsgs=[flag for flag,msg in resultlist if isinstance(x,(str))]
        failmsg = '请检查_compute函数,_eval_expression函数返回fail时没传失败消息'

        logger.info('resultlist=>', resultlist)
        notsuccessmsg = [msg for flag, msg in resultlist if flag is not 'success']
        if len(notsuccessmsg) > 0:
            failmsg = notsuccessmsg[0]

        res = len([flag for flag, msg in resultlist if flag is 'success']) == len(resultlist)
        if res is True:
            return ('success', '')
        else:
            return ('fail', failmsg)

    except Exception as e:
        return ('error', '计算表达式[%s]异常[%s]' % (checkexpression, traceback.format_exc()))


def _separate_expression(expectedexpression):
    # _op=('==','>=','<=','!=')
    for op in _op:
        if op in expectedexpression:
            k = expectedexpression.split(op)[0].strip()
            v = expectedexpression.split(op)[1].strip()
            return k, v, op

    raise RuntimeError("不能分割的表达式=>%s" % expectedexpression)



def _legal(ourexpression):
    res = None

    if "|" in ourexpression:
        res = []
        seplist = ourexpression.split("|")
        for sep in seplist:
            res.append(_replace(sep))

        return "|".join(res)


    else:
        res = _replace(ourexpression)

    return res


def _replace(expressionsep):
    try:
        logger.info('==replace=>%s' % expressionsep)
        eval(expressionsep)
    except Exception as e:
        logger.info('==_replace异常')

        # if    'true' in expressionsep:
        #   expressionsep=expressionsep.replace('true','True')
        # elif 'false' in expressionsep:
        #   expressionsep=expressionsep.replace('false','False')

        list_0 = re.findall("!=", expressionsep)
        list_1 = re.findall(">=", expressionsep)
        list_2 = re.findall("<=", expressionsep)
        list_3 = re.findall("=", expressionsep)

        if len(list_0) > 0 or len(list_1) > 0 or len(list_2) > 0:
            pass

        elif len(list_3) == 1:
            expressionsep = expressionsep.replace("=", "==")
        #兼容下面
        ##response.text$content="text/html; charset=utf-8"
        ##$[sass_check_body({{RESPONSE_TEXT}},payState=2)]=true
        elif len(list_3) >1:
            ms=re.findall('\$\[(.*)\]=(.*)', expressionsep)
            if ms:
                left='$[{}]'.format(ms[0][0])
                expressionsep='=='.join([left,ms[0][1]])
    # else:
    #   msg="不能合法化的表达式!=>%s"%expressionsep
    #   raise RuntimeError(msg)
    finally:
        return expressionsep



def _get_hearder_key(r):
    def _upper_first(w):
        if len(w) == 1:
            return w.upper()

        else:
            return w[0].upper() + w[1:]

    rs = [_upper_first(str(_)) for _ in r.split('_')]
    return '-'.join(rs)


def _eval_expression(user, ourexpression, need_chain_handle=False, data=None, direction='left', taskid=None,
                     parse_type='json', rps_header=None):
    """返回情况
    返回(success,'')
    返回(fail,failmsg)
    返回(error,errmsg)
    1.表达式校验通过放回True
    2.校验失败 返回表达式校验失败信息
    3.发生异常 返回异常简述

    执行时 先属性替换=>变量替换=>链式校验

    接口校验需要开启need_chain_handle=True
    接口验证时 direction=left ,临时变量设置时 为right
    """
    # res=None
    exp = None
    # rr=None
    try:

        # logger.info("ourexpression=>",ourexpression)
        exp_rp = _replace_property(user, ourexpression)
        # logger.info('qqqqq=>',exp_rp)

        # logger.info('exp-pr=>',exp_rp)
        if exp_rp[0] is not 'success':
            return exp_rp

        exp_rv = _replace_variable(user, exp_rp[1], taskid=taskid, responsetext=data)
        if exp_rv[0] is not 'success':
            return exp_rv
        # logger.info('exp_rv=<',exp_rv)
        exp_rf = _replace_function(user, exp_rv[1], taskid=taskid)

        if exp_rf[0] is not 'success':
            return exp_rf

        exp = exp_rf[1]

        res = None

        if need_chain_handle is True:

            k, v, op = _separate_expression(exp)
            logger.info('获取的项=>', k, v, op)
            if parse_type != 'xml':
                for badstr in ['\\n', '\\r', '\n']:
                    data = data.replace(badstr, '')
            data = data.replace('null', "'None'").replace('true', "'True'").replace("false", "'False'")
            # logger.info('data=>',data)

            if 'response.text' == k:
                if op == '$':
                    flag = str(data).__contains__(v)
                    if flag is True:
                        return ('success', '')
                    else:
                        return ('fail', '表达式%s校验失败' % ourexpression)
            elif k.startswith('response.header'):

                ak = k.split('.')[-1].lower()
                hk = _get_hearder_key(ak)
                rh = rps_header[hk]
                # logger.info('响应头=>',rh)

                if op == '$':
                    flag = rh.__contains__(v)
                elif op == '==':
                    act = rh
                    expect = str(v).strip()
                    # logger.info('act=>%s expect=>%s'%(act,expect))
                    flag = act == expect
                else:
                    return ('fail', '响应头校验暂时只支持=,$比较.')

                if flag is True:
                    return ('success', '')
                else:
                    return ('fail', '表达式%s校验失败' % ourexpression)


            else:

                p = None

                if parse_type == 'json':
                    p = JSONParser(data)
                elif parse_type == 'xml':
                    # logger.info('类型=>',type(parse_type))
                    # logger.info('data=>')
                    # logger.info(data)
                    # 消除content-type首行
                    data = '\n'.join(data.split('\n')[1:])
                    logger.info('reee', data)
                    p = XMLParser(data)

                oldk = k

                k = p.getValue(k)
            # try:
            #   if eval(str(k)) in(None,True,False):
            #       k=str(k)
            #       v=str(v)
            # except:
            #   pass

            ##处理左边普通字符串的情况

            if k is None:
                k = oldk

            if v == 'true':
                v = 'True'
            elif v == 'false':
                v = 'False'
            elif v == 'null':
                v = 'None'

            logger.info('表达式合成{%s(%s),%s(%s),%s(%s)}' % (k, type(k), op, type(op), v, type(v)))

            if type(k) == type(v):
                exp = "".join([str(k), op, str(v)])
            else:
                exp = "".join([str(k), op, str(v)])
            # return ('fail','表达式[%s]校验不通过 期望[%s]和实际类型[%s]不一致'%(ourexpression,type(v),type(k)))
            # res=eval(exp)

            rr = eval(exp)
            if isinstance(rr, (tuple,)):
                raise RuntimeError('需要特殊处理')

            logger.info("实际计算表达式[%s] 结果[%s]" % (exp, rr))

        return ('success', '') if rr is True else ('fail', '表达式%s校验失败' % ourexpression)
    except:
        logger.info(traceback.format_exc())
        logger.info('表达式等号两边加单引号后尝试判断..')
        exp = exp.replace("<br>", '')
        # return ('error','表达式[%s]计算异常[%s]'%(ourexpression,traceback.format_exc()))
        try:
            logger.info('_op=>', _op)
            logger.info('_exp=>', exp)
            for op in _op:
                if op in exp:
                    key = exp.split(op)[0]
                    value = exp.split(op)[1]
                    logger.info('key=>', key)
                    logger.info('value=>', value)
                    res = None
                    if op == '$':
                        res = eval(
                            "'%s'.__contains__('%s')" % (str(key).replace('\n', '').replace('\r', ''), str(value)))

                    elif op == '>=':
                        res = eval('''"%s"%s"%s"''' % (str(key), '>=', str(value)))
                    elif op == '<=':
                        res = eval('''"%s"%s"%s"''' % (str(key), '<=', str(value)))
                    else:
                        res = eval('''"%s"%s"%s"''' % (str(key), op, str(value)))

                    logger.info('判断结果=>', res)
                    if res is True:
                        return ('success', res)
                    else:
                        return ('fail', res)

            return ('fail', '')

        except:
            logger.info('表达式计算异常.')
            return ('error', '表达式[%s]计算异常[%s]' % (ourexpression, traceback.format_exc()))

        exp = None
        try:

            exp_rp = _replace_property(user, ourexpression)
            if exp_rp[0] is not 'success':
                return exp_rp

            exp_rv = _replace_variable(user, exp_rp[1], taskid=taskid)
            if exp_rv[0] is not 'success':
                return exp_rv

            exp = exp_rv[1]

            res = None

            if need_chain_handle is True:

                k, v, op = _separate_expression(exp)
                logger.info('获取的项=>', k, v, op)
                data = data.replace('null', "'None'").replace('true', "'True'").replace("false", "'False'")

                if 'response.text' == k:
                    if op == '$':
                        flag = str(data).__contains__(v)
                        if flag is True:
                            return ('success', '')
                        else:
                            return ('fail', '表达式%s校验失败' % ourexpression)
                elif k.startswith('response.header'):

                    ak = k.split('.')[-1].lower()
                    hk = _get_hearder_key(ak)
                    rh = rps_header[hk]
                    # logger.info('响应头=>',rh)

                    if op == '$':
                        flag = rh.__contains__(v)
                    elif op == '==':
                        act = rh
                        expect = str(v).strip()
                        # logger.info('act=>%s expect=>%s'%(act,expect))
                        flag = act == expect
                    else:
                        return ('fail', '响应头校验暂时只支持=,$比较.')

                    if flag is True:
                        return ('success', '')
                    else:
                        return ('fail', '表达式%s校验失败' % ourexpression)

                else:

                    p = None

                    if parse_type == 'json':
                        p = JSONParser(data)
                    elif parse_type == 'xml':
                        # 消除content-type首行
                        data = '\n'.join(data.split('\n')[1:])
                        logger.info('reee', data)
                        p = XMLParser(data)

                    oldk = k
                    k = p.getValue(k)

                ##处理左边普通字符串的情况

                if k is None:
                    k = oldk

                if v == 'true':
                    v = 'True'
                elif v == 'false':
                    v = 'False'
                elif v == 'null':
                    v = 'None'

                logger.info('表达式合成{%s(%s),%s(%s),%s(%s)}' % (k, type(k), op, type(op), v, type(v)))

                if type(k) == type(v):
                    exp = "".join([str(k), op, str(v)])
                else:
                    exp = "".join([str(k), op, str(v)])
                # return ('fail','表达式[%s]校验不通过 期望[%s]和实际类型[%s]不一致'%(ourexpression,type(v),type(k)))
                # res=eval(exp)

                rr = eval(exp)
                if isinstance(rr, (tuple,)):
                    raise RuntimeError('需要特殊处理')

                logger.info("实际计算表达式[%s] 结果[%s]" % (exp, rr))

            return ('success', '') if rr is True else ('fail', '表达式%s校验失败' % ourexpression)
        except:
            logger.info(traceback.format_exc())
            logger.info('表达式等号两边加单引号后尝试判断..')
            exp = exp.replace("<br>", '').replace('\n', '').replace('\r', '')
            # return ('error','表达式[%s]计算异常[%s]'%(ourexpression,traceback.format_exc()))
            try:
                logger.info('_op=>', _op)
                logger.info('_exp=>', exp)
                for op in _op:
                    if op in exp:
                        key = exp.split(op)[0]
                        value = exp.split(op)[1]
                        logger.info('key=>', key)
                        logger.info('value=>', value)
                        res = None
                        if op == '$':
                            res = eval(
                                "'%s'.__contains__('%s')" % (str(key), str(value)))

                        elif op == '>=':
                            res = eval('''"%s"%s"%s"''' % (str(key), '>=', str(value)))
                        elif op == '<=':
                            res = eval('''"%s"%s"%s"''' % (str(key), '<=', str(value)))
                        else:
                            res = eval('''"%s"%s"%s"''' % (str(key), op, str(value)))

                        logger.info('判断结果=>', res)
                        if res is True:
                            return ('success', res)
                        else:
                            return ('fail', res)

                return ('fail', '')

            except:
                logger.info('表达式计算异常.')
                return ('error', '表达式[%s]计算异常[%s]' % (ourexpression, traceback.format_exc()))

def _replace_function(user, str_, taskid=None):
    '''计算函数引用表达式
    '''
    # logger.info('--计算引用表达式=>',str_)

    resultlist = []
    builtinmethods = [x.name for x in getbuiltin()]
    str_ = str(str_)

    call_str_list = re.findall('\$\[(.*?)\((.*?)\)\]', str_)

    if len(call_str_list) == 0: return ('success', str_)

    for call_str in call_str_list:
        fname = call_str[0]
        f = None
        try:
            f = Function.objects.get(name=fname)
            logger.info('通过函数名[%s]获取函数对象'%fname)
        except:
            pass

        appendstr = "taskid='%s',callername='%s'" % (taskid, user.name)
        itlist = []
        if call_str[1]:
            itlist.append(call_str[1])
        itlist.append(appendstr)
        # 计算表达式
        invstr = '%s(%s)' % (fname, ','.join(itlist))
        logger.info('invstr=>', invstr)

        # 替换表达式
        repstr = '%s(%s)' % (fname, call_str[1])

        status, res = Fu.call(f, invstr, builtin=(lambda: True if fname in builtinmethods else False)())
        viewcache(taskid, '计算函数表达式:<br/>%s <br/>结果:<br/>%s' % (invstr, res))
        resultlist.append((status, res))

        if status is 'success':
            logger.info('\n\n')
            logger.info('替换函数引用 %s\n =>\n %s ' % ('$[%s]' % invstr, str(res)))
            str_ = str_.replace('$[%s]' % repstr, str(res))

    if len([x for x in resultlist if x[0] is 'success']) == len(resultlist):
        logger.info('--成功计算引用表达式 结果=>', str_)
        return ('success', str_)
    else:
        alist = [x[1] for x in resultlist if x[0] is not 'success']
        logger.info('--异常计算引用表达式=>', alist[0])
        return ('error', alist[0])


def _get_step_params(paraminfo, taskid, callername):
    '''
    获取内置变量STEP_PARAMS

    '''

    def _next(cur):
        # logger.info('_next')
        # logger.info('初始数据=>',cur)
        # logger.info('*'*200)

        if isinstance(cur, (dict,)):
            i = 0
            for k in list(cur.keys()):
                i = i + 1

                v = cur[k]
                try:
                    v = eval(v)
                # logger.info('类型：',type(v))
                except:
                    pass

                if isinstance(v, (str,)):
                    find_var = len(re.findall('\{\{.*?\}\}', v))
                    if find_var:
                        if v.__contains__('{{STEP_PARAMS}}'):
                            logger.info('字符串发现STEP_PARAMS', v)
                            del cur[k]
                        # cur[k]=''
                        # logger.info(cur)
                        else:
                            user = User.objects.get(name=callername)
                            cur[k] = _replace_variable(user, v, taskid=taskid)[1]

                else:
                    _next(v)

        elif isinstance(cur, (list,)):
            itemindex = -1
            for sb in cur:
                itemindex = itemindex + 1
                if isinstance(sb, (str,)):
                    find_var = len(re.findall('\{\{.*?\}\}', sb))
                    if find_var:
                        if sb.__contains__('{{STEP_PARAMS}}'):
                            # del parent[key]
                            cur.remove(sb)
                        else:
                            user = User.objects.get(name=callername)
                            cur[itemindex] = _replace_variable(user, sb, taskid=taskid)[1]



                else:
                    _next(sb)

    ########################
    ps = paraminfo
    try:
        ps = eval(paraminfo)

        if isinstance(ps, (dict,)):
            # logger.info('ps=>',ps)
            _next(ps)
            viewcache(taskid,'获取内置变量[字典模式]STEP_PARAMS=> %s ' % str(ps))
            return ps

    except:
        try:
            dl = dict()
            for s1 in ps.split('&'):
                p1 = s1.split('=')[0]
                p2 = '='.join(s1.split('=')[1:])
                if p1.__contains__('?'):
                    p1 = p1.split('?')[1]

                try:
                    import json
                    logger.info('p1=>', p1)
                    dl[p1] = eval(p2)

                # logger.info('类型：',type(dl[p1]))
                except:
                    # traceback.logger.info_exc()
                    dl[p1] = p2

            logger.info('dl=>', dl)
            _next(dl)
            viewcache(taskid,'获取内置变量[a=1&b=2模式]STEP_PARAMS=> %s ' % str(dl))
            return dl

        except:
            return ('error', 'a=1&b=2模式获取内置变量STEP_PARAMS异常')

        return ('error', traceback.format_exc())


def _replace_variable(user, str_, src=1, taskid=None, responsetext=None):
    """
    返回(success,替换后的新字符串)
    返回(fail,错误消息)
    src:同_gain_compute()
    """

    if taskid is not None:
        t = base64.b64decode(taskid).decode()
        pid = t.split('_')[0]
        pname = Plan.objects.get(id=pid).description
    try:
        old = str_
        varnames = re.findall('{{(.*?)}}', str_)
        logger.info('######################varnames:',varnames)
        for varname in varnames:
            if varname.strip() == 'STEP_PARAMS':
                dictparams = _get_step_params(str_, taskid, user.name)
                logger.info('==获取内置变量STEP_PARAMS=>\n', dictparams)
                logger.info('==STEP_PARAMS替换前=>\n', old)
                old = old.replace('{{%s}}' % varname, str(dictparams))
                logger.info('==STEP_PARAMS替换后=>\n', old)
                continue;

            elif varname.strip() == 'RESPONSE_TEXT':
                logger.info('==获取text/html响应报文用于替换 responsetext={}'.format(responsetext))
                if responsetext:
                    old = old.replace('{{RESPONSE_TEXT}}', responsetext)
                    logger.info('==RESPONSE_TEXT替换后=>\n', old)
                    continue;

            vars = Variable.objects.filter(key=varname)
            var = None
            for m in vars:
                x = json.loads(Tag.objects.get(var=m).planids)
                if pname in x and pid in x.get(pname):
                    var = m
                    viewcache(taskid, '使用局部变量 %s 描述：%s' % (varname, var.description))
                    break
            if var is None:
                for m in vars:
                    try:
                        var = Tag.objects.get(var=m, isglobal=1).var
                        viewcache(taskid, '使用全局变量 %s 描述：%s' % (varname, var.description))
                    except:
                        pass
                if var is None:
                    logger.info(traceback.format_exc())
                    return ('error', '字符串[%s]变量【%s】替换异常,未在局部变量和全局变量中找到，请检查是否已正确配置' % (str_,varname))
            
            gain_rv = _replace_variable(user, var.gain, src=src, taskid=taskid)
            if gain_rv[0] is not 'success':
                # logger.info(11)
                return gain_rv
            gain = gain_rv[1]
            
            value_rv = _replace_variable(user, var.value, src=src, taskid=taskid)
            if value_rv[0] is not 'success':
                # logger.info(1221)
                return value_rv
            value = value_rv[1]
            
            is_cache = var.is_cache
            
            if len(gain) == 0 and len(value) == 0:
                warnings.warn("变量%s的获取方式和默认值至少填一项" % varname)
            elif len(gain) > 0 and len(value) > 0:
                old = old.replace('{{%s}}' % varname, str(value), 1)
                old=old.replace('"null"','null').replace("'null'",'null')
                # __replace_route["%s.%s"%(user.name,varname)]=value
                warnings.warn('变量%s获取方式和值都设定将被当做常量，获取方式和缓存失效' % varname)
            
            
            elif len(gain) == 0 and len(value) > 0:
                
            
                old = old.replace('{{%s}}' % varname, value, 1)
                old=old.replace("'null'",'None')
                viewcache(taskid,'替换变量 {{%s}}=>%s' % (varname, value))
            # __replace_route["%s.%s"%(user.name,varname)]=value
            
            elif len(gain) > 0 and len(value) == 0:
                v = None
                if is_cache is True:
                    v = __varcache.get('%s.%s' % (user, varname))
                    if v is None:
                        v = _gain_compute(user, gain, src=src, taskid=taskid)
                        if v[0] is not 'success':
                            # logger.info(14441)
                            return v
                        else:
                            v = v[1]
                        old = old.replace('{{%s}}' % varname, str(v), 1)
                        viewcache(taskid,'替换变量 {{%s}}=>%s' % (varname, v))
                
                
                
                else:
                    v = _gain_compute(user, gain, src=src, taskid=taskid)
                    logger.info('变量获取结果：', v[1])
                    if v[0] is not 'success':
                        return v
                    else:
                        if v[1]:
                            v = v[1]
                            viewcache(taskid, '替换变量 {{%s}}=>%s' % (varname, v))
                        else:
                            v = '-9999999999'
                            viewcache(taskid, '替换变量 {{%s}}=>%s (无结果，特殊默认值)' % (varname, v))
                    old = old.replace('{{%s}}' % varname, str(v), 1)
        return ('success', old)

    except Exception as e:
        logger.info(traceback.format_exc())
        return ('error', '字符串[%s]变量替换异常[%s] 请检查包含变量是否已配置' % (str_, traceback.format_exc()))



def is_valid_where_sql(call_str):
    '''
    获取方式输入验证
    '''
    if call_str is None or len(call_str.strip()) == 0:
        return True
    
    call_str = call_str.strip()
    is_function = _is_function_call(call_str)
    logger.info('is_function=>', is_function)
    
    if is_function: return True
    if '@' not in call_str:
        return False
    
    not_expected_end_char = [';', '；']
    sql = call_str.split('@')[0]
    for ch in not_expected_end_char:
        if sql[-1] == ch:
            return False
    
    return True


def is_valid_gain_value(gain, value):
    if gain and value:
        return '获取方式和value只能选填一个'
    if not gain and not value:
        return '获取方式和value至少选填一个'
    
    if len(gain.strip()) == 0 and len(value.strip()) == 0:
        return '获取方式和value至少选填一个'
    
    return True


def _is_valid_where_symmetric(input):
    '''
    特殊字符{[('" 左右对称性验证
    '''
    _mata = ('{', '[', '(', '\'', '\"')
    m = [x for x in input if x in _mata]
    if m % 2 is not 0:
        return False
    
    size = len(m)
    for x in range(size / 2):
        if m[x] != m[size - x - 1]:
            return False
    
    return True


def _is_function_call(call_str):
    '''
    判断获取方式类别
    1.是否有空格
    2.是否带()
    '''
    res_1 = re.findall('\s+', call_str)
    # res_2=re.findall("\w{1,}\([\w,]*\)",call_str)
    res_2 = re.findall("\w{1,}\(.*?\)", call_str)
    
    return True if len(res_1) == 0 and len(res_2) > 0 else False


def _is_sql_call(call_str):
    pass


def _gain_compute(user, gain_str, src=1, taskid=None):
    """
    获取方式计算
    返回(success,计算结果)
    返回(fail,错误消息)
    src:1:from sql 2:from function call
    """
    try:
        # from builtin import *
        # res=re.findall("\w{1,}\([\w,]*\)",gain_str)
        # logger.info('匹配结果=>',res,gain_str)
        if _is_function_call(gain_str):
            ##是方法调用
            # tzm=Fu.tzm_compute(gain_str,"(.*?)\((.*?)\)")
            flag = Fu.tzm_compute(gain_str, '(.*?)\((.*?)\)')
            logger.info('flag1', flag)
            ms = list(Function.objects.filter(flag=flag))
            functionid = None
            
            if len(ms) == 0:
                # functionid=None
                # flag=Fu.tzm_compute(gain_str,'(.*?)\(.*?\)')
                # logger.info('flag2', flag)
                try:
                    functionid = Function.objects.get(flag=flag).id
                except:
                    functionid = ''
                    pass
            elif len(ms) == 1:
                functionid = ms[0].id
            else:
                functionid = ms[0].id
                viewcache(taskid, "<span style='color:#FF3333;'>函数库中发现多个匹配函数 这里使用第一个匹配项</span>")
            # warnings.warn('库中存在两个特征码相同的自定义函数')
            
            a = re.findall('(.*?)\((.*?)\)', gain_str)
            call_method_name = a[0][0]
            call_method_params = a[0][1].split(',')
            
            if functionid is None:
                return ('error', '没查到匹配函数请先定义[%s,%s]' % (gain_str, flag))
            else:
                logger.info('functionid=>', functionid)

            return _callfunction(user, functionid, call_method_name, call_method_params, taskid=taskid)
        
        
        else:
            # 是sql
            op = Mysqloper()
            gain_str_rp = _replace_property(user, gain_str)
            if gain_str_rp[0] is not 'success':
                return gain_str_rp
            
            gain_str_rv = _replace_variable(user, gain_str_rp[1], taskid=taskid)
            if gain_str_rv[0] is not 'success':
                return gain_str_rv
            
            gain_str = gain_str_rv[1]
            if src == 1:
                if ';' in gain_str:
                    return op.db_execute2(gain_str, taskid=taskid)
                else:
                    return op.db_execute(gain_str, taskid=taskid)
            else:
                return ('success', '"%s"' % gain_str.strip())
    
    
    except Exception as e:
        # traceback.logger.info_exc()
        return ('error', traceback.format_exc())


def _replace_property(user, str_, taskid=None):
    """
    属性右替换
    返回(success,替换后新值)
    返回(fail,错误消息)

    """
    cur = None
    try:
        old = str_
        username = user.name
        # username=user.name
        # a=re.findall("\$(.*)=", str_)
        
        logger.info('str_=>', str_)
        b = re.findall("\$\{(.*?)\}", str_)
        # c=a+b
        c = b
        for it in c:
            # logger.info('tmp==>',it)
            cur = it
            
            logger.info("取属性==")
            logger.info(_tempinfo, username, it)
            v = _tempinfo.get(username).get(it)
            
            if v is None:
                # raise RuntimeError('没有定义属性$%s 请先定义'%it)
                pass
            old = old.replace(r"${%s}" % it, str(v))
        
        # logger.info('属性替换=》',old)
        
        return ('success', old)
    except Exception as e:
        logger.error(traceback.format_exc())
        return ('error', '请检查是否定义属性%s 错误消息:%s' % (cur, traceback.format_exc()))





def _find_and_save_property(taskid,user, dict_str, responsetext):
    """
    接口属性字段处理  默认根据定的路径从相应中拿值 拿不到路劲当普通字符串处理

    """
    cur = None
    # logger.info(type(dict_str),len(dict_str))
    try:
        if dict_str is None or len(dict_str.strip()) == 0:
            return ('success', '')

        ##增加对变量的处理
        status,res=_replace_variable(user, dict_str,responsetext=responsetext,taskid=taskid)
        if status is 'success':
            dict_str=res
        else:
            return ('error','处理属性异常')

        d = eval(dict_str)

        for k, v in d.items():
            cur = k
            p = JSONParser(responsetext)
            logger.info('================_find_and_save_property==========')

            v1 = p.getValue(v)
            
            if not v1:
                # return ('fail','通过[%s]获取属性值失败,请检查'%v)
                v1 = v

            save_data(user.name, _tempinfo, k, v1)
        return ('success', '')
    
    except Exception as e:
        logger.info(traceback.format_exc())
        return ('error', "用户%s属性缓存失败=>属性%s" % (user.name, cur))


def save_data(username, d, k, v):
    """
    """
    try:
        if d.get(username) is None:
            d[username] = {}

        d[username][k] = v
        # logger.info('存属性==',username, k, v)

    except:
        raise RuntimeError("存property失败=>%s" % k)


def clear_data(username, d):
    """
    清空用户相关缓存信息
    """
    for key in list(d.keys()):
        if username in key:
            del d[key]


class Struct(object):
    
    def __init__(self, data):
        self.datastr = str(data)
    
    def getValue(self, xpath):
        raise NotImplementedError("")
    
    def translate(self, chainstr):
        raise NotImplementedError("")


class XMLParser(Struct):
    def __init__(self, data):
        logger.info('==xml解析传入data=：\n', data)
        self.root = ET.fromstring(str(data))
    
    def getValue(self, xpath):
        
        logger.info('查找=>', xpath)
        result = ''
        route_path = ''
        chainlist = xpath.split('.')
        
        if len(chainlist) > 1:
            chainlist.pop(0)
        else:
            pass
        
        for chain in chainlist:
            o = dict()
            index = None
            propname = None
            tagname = None
            ms = re.findall('\[(.*?)\]', chain)
            # logger.info('ms=>',ms)
            kh = None
            
            for m in ms:
                try:
                    index = str(int(m))
                except:
                    propname = m
            
            tagname = re.sub(r'\[.+\]', '', chain)
            chain = re.sub('[.*?]', '', chain)
            
            route_path += '/' + tagname
            
            if index:
                route_path += '[%s]' % str(int(index) + 1)
            else:
                route_path += '[1]'
            
            if propname:
                return self.root.find('.' + route_path).attrib.get(propname, 'None')
        try:
            # logger.info('search=>','.'+route_path)
            return self.root.find('.' + route_path).text
        except:
            return 'None'


class JSONParser(Struct):
    
    def __init__(self, data):
        
        # logger.info("传入=>",data)
        self.obj = eval(self._apply_filter(data))
        
        # 兼容不同的系统 有些系统喜欢返回JSON字符串 有些json
        for i in range(5):
            if isinstance(self.obj, (str,)):
                self.obj = eval(self.obj)
    
    # logger.info('==JSONParser 数据转字典=>',self.obj,type(self.obj))
    
    # logger.info("待匹配数据=>",self.obj)
    
    def _apply_filter(self, msg):
        # logger.info("leix=",type(msg))
        msg = msg.replace("true", "True").replace("false", "False").replace("null", "None")
        # logger.info(msg)
        return msg
    
    def translate(self, chainstr):
        
        def is_ok(chainstr):
            stages = chainstr.split(".")
            for x in stages:
                if len(re.findall("^[0-9]\d+$", x)) == 1:
                    return False
            return True
        
        if is_ok(chainstr) == True:
            h = ''
            if isinstance(self.obj, (list,)):
                if chainstr.startswith('response.json'):
                    startindex = re.findall('response.json\[(.*?)\]', chainstr)[0]
                    h = "[%s]" % startindex
                    chainstr = chainstr.replace('response.json%s.' % h, '')
            elif isinstance(self.obj, (bool,)):
                logger.info('&' * 200)
                return 'self.obj'
            
            stages = chainstr.split(".")
            return "self.obj%s." % h + ".".join(
                ["get('%s')[%s" % (stage.split("[")[0], stage.split("[")[1]) if "[" in stage else "get('%s')" % stage
                 for stage in stages])
        
        else:
            return False
    
    def getValue(self, chainstr):
        errms = '解析数据链[%s]失败 数据链作为值返回' % chainstr
        xpath = self.translate(chainstr)
        if xpath:
            
            try:
                # logger.info('==查询源数据=>%s' % (self.obj))
                # logger.info('==查询源数据类型=>%s'%type(self.obj))
                # logger.info("==xpath查询=>%s" % xpath)
                r = eval(xpath)
                return r
            except:
                logger.info(errms)
                return chainstr
        else:
            logger.info(errms)
            return chainstr
