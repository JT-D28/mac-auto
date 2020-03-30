#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-09-27 14:45:12
# @Author  : Blackstone
# @to      :
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse

from ME2 import configs
from homepage.dealinfo import dealDeBuginfo
from login.models import *
from manager.models import *
from .core import ordered, Fu, getbuiltin, EncryptUtils, genorder, simplejson
from .db import Mysqloper
from .context import set_top_common_config, viewcache, gettestdatastep, gettestdataparams, get_task_session, \
    clear_task_session, get_friendly_msg, setRunningInfo, getRunningInfo

import re, traceback, redis, time, threading, smtplib, requests, json, warnings, datetime, socket
import copy, base64, datetime, xlrd,os
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from email.header import Header

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


def db_connect(config):
    """
    测试数据库连接
    """
    print('==测试数据库连接===')
    
    conn = None
    
    try:
        
        # print(len(conname),len(conname.strip()))
        description = config['description']
        dbtype = config['dbtype']
        dbname = config['dbname']
        # oracle不需要这两项
        host = config['host']
        port = config['port']
        #
        user = config['username']
        pwd = config['password']
        
        # print("=>没查到可用配置,准备新配一个")
        print("数据库类型=>", dbtype)
        print("数据库名(服务名|SID)=>", dbname)
        print("数据库地址=>", host, port)
        print("数据库账号=>", user, pwd)
        
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
        print('error=>', error)
        return ('error', '连接异常->%s' % get_friendly_msg(error))


def _get_full_case_name(case_id, curent_case_name):
    '''
    对于case_case结构的tree节点 报告中用例名显示为 casename0_casename1
    '''
    case0 = Case.objects.get(id=case_id)
    # fullname=case0.description
    olist = list(Order.objects.filter(follow_id=case_id, kind='case_case'))
    if len(olist) == 0:
        return curent_case_name
    
    else:
        cname = Case.objects.get(id=olist[0].main_id).description
        curent_case_name = "%s_%s" % (cname, curent_case_name)
        return _get_full_case_name(olist[0].main_id, curent_case_name)


def gettaskresult(taskid):
    from .cm import getchild
    print("==gettaskresult==")
    ##区分迭代次数
    bset = set()
    bmap = {}
    ##
    
    detail = {}
    spend_total = 0
    res = ResultDetail.objects.filter(taskid=taskid).order_by('createtime')
    
    # print(res)
    reslist = list(res)
    if len(reslist) == 0:
        return detail
    
    plan = reslist[0].plan
    planname = plan.description
    planid = plan.id
    
    has_ = []
    
    caseids = []
    
    for r in list(res):
        if r.case.id not in has_:
            has_.append(r.case.id)
            caseids.append(r.case.id)
        
        else:
            pass
    
    ##修复set乱序
    
    cases = [Case.objects.get(id=caseid) for caseid in caseids]
    
    # print('cases=>')
    # print(cases)
    report_url = 'http://%s/static/report_%s.html' % (configs.ME2_URL, taskid)
    detail['local_report_address'] = report_url
    detail['planname'] = planname
    detail['planid'] = planid
    detail['taskid'] = taskid
    detail['cases'] = []
    detail['success'] = 0
    detail['fail'] = 0
    detail['skip'] = 0
    detail['error'] = 0
    detail['min'] = 99999
    detail['max'] = 0
    detail['average'] = 0
    
    for d in cases:
        caseobj = {}
        case = d
        casename = case.description
        caseid = case.id
        # caseobj['casename']=casename
        caseobj['casename'] = _get_full_case_name(caseid, casename)
        if caseobj.get("steps", None) is None:
            caseobj['steps'] = {}
        caseid = case.id
        # print('taskid=>%s case_id=>%s'%(taskid,case))
        step_query = list(ResultDetail.objects.filter(taskid=taskid, case=case))
        ##case_step
        for x in step_query:
            # rblist=list(ResultDetail.objects.filter(taskid=taskid,plan=plan,case=case,step=stepinst,businessdata=business))
            # for rb in rblist:
            businessobj = {}
            business = x.businessdata
            # print('c=>%s'%business.id)
            status, step = gettestdatastep(business.id)
            # print('a=>%s b=>%s'%(case.id,step.id))
            step_weight = Order.objects.get(main_id=case.id, follow_id=step.id, kind='case_step').value
            
            business_index = \
                Order.objects.get(main_id=step.id, follow_id=business.id, kind='step_business').value.split('.')[1]
            businessobj['num'] = '%s_%s' % (step_weight, business_index)
            
            stepname = business.businessname
            result = x.result
            if 'omit' != result:
                if 'success' == result:
                    detail['success'] = detail['success'] + 1
                
                elif 'fail' == result:
                    detail['fail'] = detail['fail'] + 1
                
                elif 'skip' == result:
                    detail['skip'] = detail['skip'] + 1
                
                elif 'error' == result:
                    detail['error'] = detail['error'] + 1
                error = x.error
                businessobj['businessname'] = x.businessdata.businessname
                
                ##
                businessobj['result'] = result
                businessobj['error'] = error
                # businessobj['api']=re.findall('\/(.*?)[?]',step.url)[0] or step.body
                stepinst = None
                error, stepinst = gettestdatastep(business.id)
                if stepinst.url:
                    
                    # print('%s=>%s,%s'%(business.id,error,stepinst))
                    businessobj['stepname'] = stepinst.description
                    matcher = [a for a in stepinst.url.split('/') if
                               not a.__contains__("{{") and not a.__contains__(':')]
                    api = '/'.join(matcher)
                    if not api.startswith('/'):
                        api = '/' + api
                    businessobj['api'] = api
                else:
                    businessobj['stepname'] = stepinst.description
                    businessobj['api'] = stepinst.body.strip()
                
                businessobj['itf_check'] = business.itf_check
                businessobj['db_check'] = business.db_check
                # businessobj['spend']=ResultDetail.objects.get(taskid=taskid,plan=plan,case=case,step=stepinst,businessdata=business).spend
                businessobj['spend'] = x.spend
                spend_total += int(businessobj['spend'])
                if int(businessobj['spend']) <= int(detail['min']):
                    detail['min'] = businessobj['spend']
                
                if int(businessobj['spend']) > int(detail['max']):
                    detail['max'] = businessobj['spend']
                
                # caseobj.get('steps').append(businessobj)
                
                ##计算当前迭代次数
                if x.businessdata.id in bset:
                    bcount = bmap.get(str(x.businessdata.id), 0)
                    bcount = bcount + 1
                    bmap[str(x.businessdata.id)] = bcount
                    L = caseobj.get('steps').get(str(bcount), [])
                    L.append(businessobj)
                    caseobj['steps'][str(bcount)] = L
                
                else:
                    bset.add(x.businessdata.id)
                    bcount = bmap.get(str(x.businessdata.id), 0)
                    bcount = bcount + 1
                    bmap[str(x.businessdata.id)] = bcount
                    L = caseobj.get('steps').get(str(bcount), [])
                    L.append(businessobj)
                    caseobj['steps'][str(bcount)] = L
        
        ##case_case map
        
        detail.get("cases").append(caseobj)
    
    detail['total'] = detail['success'] + detail['fail'] + detail['skip'] + detail['error']
    if detail['success'] == detail['total']:
        detail['result'] = 'pass'
    else:
        detail['result'] = 'fail'
    
    try:
        detail['average'] = int(spend_total / detail['total'])
    except:
        detail['average'] = '-1'
    
    try:
        detail['success_rate'] = str("%.2f" % (detail['success'] / detail['total']))
    except:
        detail['success_rate'] = '-1'
    detail["reporttime"] = time.strftime("%m-%d %H:%M", time.localtime())
    
    ##
    print('报告数据=>', detail)
    
    return detail


def check_user_task():
    def run():
        # while True:
        #   time.sleep(2)
        # print("do task.")
        for username, tasks in _taskmap.items():
            for taskid, plans in tasks.items():
                for planid in plans:
                    runplan(planid)


def runplans(username, taskid, planids, is_verify, kind=None):
    """
    任务运行
    kind 运行方式 手动其他
    """
    kindmsg = ''
    if kind is not None:
        kindmsg = kind
    # print("kindmsg=>",kindmsg,username,taskid)
    verifymsg = '调试' if is_verify in ('0', None, '', 0) else '验证'
    
    viewcache(taskid, username, kind,
              "=======开始%s%s任务【<span style='color:#FF3399'>%s</span>】====" % (kindmsg, verifymsg, taskid))
    for planid in planids:
        threading.Thread(target=runplan, args=(username, taskid, planid, is_verify, kind)).start()


# def runplan(callername,taskid,planid,kind=None):
#   '''


#   '''
#   groupskip=[]

#   try:
#       plan=Plan.objects.get(id=planid)

#       dbid=plan.db_id
#       if dbid:
#           desp=DBCon.objects.get(id=int(dbid)).description
#           set_top_common_config(taskid, desp,src='plan')


#       #username=plan.author.name
#       username=callername
#       # viewcache("username=>",username)
#       viewcache(taskid,username,kind,"开始执行计划[<span style='color:#FF3399'>%s</span>]"%plan.description)
#       #cases=list(plan.cases.all())
#       cases=[Case.objects.get(id=x.follow_id)  for x in ordered(list(Order.objects.filter(main_id=planid,kind='case')))]

#       #print(cases)
#       result,error="",""
#       caseresult=[]
#       planresult=[]

#       for case in cases:
#           dbid=case.db_id
#           if dbid:
#               desp=DBCon.objects.get(id=int(dbid)).description
#               set_top_common_config(taskid, desp,src='case')

#           groupskip=[]
#           viewcache(taskid,username,kind,"开始执行用例[<span style='color:#FF3399'>%s</span>]"%case.description)
#           orderlist=ordered(list(Order.objects.filter(kind='step',main_id=case.id)))
#           for order in orderlist:
#               groupid=order.value.split(".")[0]
#               # step=Step.objects.get(id=order.follow_id)
#               start=time.time()
#               spend=0
#               if groupid not in groupskip:
#                   result,error=_step_process_check(callername,taskid,order,kind)
#                   spend=int((time.time()-start)*1000)

#                   if result is not 'success':
#                       groupskip.append(groupid)
#               else:
#                   result,error='skip','skip'


#               ##保存结果
#               print("准备保存结果===")
#               detail=ResultDetail()
#               detail.taskid=taskid
#               detail.plan=plan
#               detail.case=case
#               #detail.step=Step.objects.get(id=order.follow_id)
#               detail.businessdata=BusinessData.objects.get(id=order.follow_id)
#               detail.result=result
#               detail.error=error
#               detail.spend=spend
#               detail.save()


#               ##
#               caseresult.append(result)
#               ##
#               if "success" in result:
#                   result="<span class='layui-bg-green'>%s</span>"%result

#               elif "fail" in result:
#                   result="<span class='layui-bg-red'>%s</span>"%result
#               elif "skip" in result:
#                   result="<span class='layui-bg-orange'>%s</span>"%result

#               ##
#               #print(len(result),len('success'),result=='success')
#               if 'success' in result:
#                   viewcache(taskid,username,kind,"执行结果%s"%(result))
#               else:
#                   if error is False:
#                       error='表达式不成立'
#                   viewcache(taskid,username,kind,"执行结果%s 原因=>%s"%(result,error))
#                   # viewcache(taskid, username,kind,"%s,%s"%('success' in result,result))
#               # viewcache(taskid,username,kind,"--"*40)

#           casere=(len([x for x in caseresult if x=='success'])==len([x for x in caseresult]))
#           planresult.append(casere)
#           if casere:
#               viewcache(taskid, username,kind,"结束用例[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-green'>success</span>"%case.description)
#           else:
#               viewcache(taskid, username,kind,"结束用例[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-red'>fail</span>"%case.description)

#       #plan
#       planre=(len([x for x in planresult])==len([x for x in planresult if x==True]))

#       if planre:
#           plan.last='success'
#           plan.save()
#           viewcache(taskid, username,kind,"结束计划[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-green'>success</span>"%plan.description)
#       else:
#           plan.last='fail'
#           plan.save()
#           viewcache(taskid, username,kind,"结束计划[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-red'>fail</span>"%plan.description)

#       ##清除请求session
#       clear_task_session('%s_%s'%(taskid,callername))
#       ##

#       _save_builtin_property(taskid,username)
#       ##发送报告
#       config_id=plan.mail_config_id
#       if config_id:
#           mail_config=MailConfig.objects.get(id=config_id)
#           user=User.objects.get(name=username)
#           mail_res=MainSender.send(taskid,user,mail_config)
#           print("发送邮件 结果[%s]"%mail_res)
#           viewcache(taskid,username,kind,mail_res)

#   except Exception as e:
#       #traceback.print_exc()
#       print(traceback.format_exc())
#       viewcache(taskid,username,kind,'执行计划未知异常[%s]'%traceback.format_exc())

#   finally:
#       clear_data(username, _tempinfo)


def _runcase(username, taskid, case0, plan, planresult, is_verify, kind):
    caseresult = []
    
    dbid = case0.db_id
    if dbid:
        desp = DBCon.objects.get(id=int(dbid)).description
        set_top_common_config(taskid, desp, src='case')
    
    groupskip = []
    viewcache(taskid, username, kind, "开始执行用例[<span style='color:#FF3399'>%s</span>]" % case0.description)
    steporderlist = ordered(list(Order.objects.filter(Q(kind='case_step') | Q(kind='case_case'), main_id=case0.id)))
    ##case执行次数
    casecount = int(case0.count)
    # print('ccc=>',steporderlist)
    
    for lid in range(0, casecount):
        for o in steporderlist:
            if o.kind == 'case_case':
                case = Case.objects.get(id=o.follow_id)
                _runcase(username, taskid, case, plan, planresult, is_verify, kind)
                continue;
            
            stepid = o.follow_id
            
            try:
                
                stepcount = Step.objects.get(id=stepid).count
                if stepcount == 0:
                    continue;
                
                else:
                    # 步骤执行次数>0
                    for ldx in range(0, stepcount):
                        businessorderlist = ordered(list(Order.objects.filter(kind='step_business', main_id=stepid)))
                        # print('bbb=>',businessorderlist)
                        for order in businessorderlist:
                            groupid = order.value.split(".")[0]
                            # step=Step.objects.get(id=order.follow_id)
                            start = time.time()
                            spend = 0
                            if groupid not in groupskip:
                                print('传入order=>', order.value)
                                result, error = _step_process_check(username, taskid, order, kind)
                                spend = int((time.time() - start) * 1000)
                                
                                if result not in ('success', 'omit'):
                                    groupskip.append(groupid)
                            else:
                                result, error = 'skip', 'skip'
                            
                            ##保存结果
                            try:
                                print("准备保存结果===")
                                detail = ResultDetail()
                                detail.taskid = taskid
                                detail.plan = plan
                                detail.case = case0
                                detail.step = Step.objects.get(id=o.follow_id)
                                detail.businessdata = BusinessData.objects.get(id=order.follow_id)
                                detail.result = result
                                detail.error = error
                                detail.spend = spend
                                detail.loop_id = 1
                                detail.is_verify = is_verify
                                detail.save()
                                
                                print('保存结果=>', detail)
                            except:
                                print('保存结果异常=>', traceback.format_exc())
                            ##
                            caseresult.append(result)
                            ##
                            if "success" in result:
                                result = "<span class='layui-bg-green'>%s</span>" % result
                            
                            elif "fail" in result:
                                result = "<span class='layui-bg-red'>%s</span>" % result
                            elif "skip" in result:
                                result = "<span class='layui-bg-orange'>%s</span>" % result
                            elif "omit" in result:
                                result = "<span class='layui-bg-green'>%s</span>" % result
                            ##
                            # print(len(result),len('success'),result=='success')
                            if 'success' in result:
                                viewcache(taskid, username, kind, "步骤执行结果%s" % (result))
                            elif 'omit' in result:
                                continue
                            else:
                                # if error is False:
                                #     error = '表达式不成立'
                                viewcache(taskid, username, kind, "步骤执行结果%s 原因=>%s" % (result, error))
            
            except:
                continue;
    
    casere = (len([x for x in caseresult if x in ('success', 'omit')]) == len([x for x in caseresult]))
    planresult.append(casere)
    if casere:
        viewcache(taskid, username, kind,
                  "结束用例[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-green'>success</span>" % case0.description)
    else:
        viewcache(taskid, username, kind,
                  "结束用例[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-red'>fail</span>" % case0.description)



def runplan(callername, taskid, planid, is_verify, kind=None):

    groupskip = []
    username = callername
    try:
        plan = Plan.objects.get(id=planid)
        setRunningInfo(callername,planid,taskid,1)
        print('plan=>', plan)
        plan.is_running = 1
        plan.save()
        dbid = plan.db_id
        if dbid:
            print('plan dbid=>', dbid)
            desp = DBCon.objects.get(id=int(dbid)).description
            set_top_common_config(taskid, desp, src='plan')
        
        viewcache(taskid, username, kind, "开始执行计划[<span style='color:#FF3399'>%s</span>]" % plan.description)
        cases = [Case.objects.get(id=x.follow_id) for x in
                 ordered(list(Order.objects.filter(main_id=planid, kind='plan_case')))]
        result, error = "", ""
        # caseresult=[]
        planresult = []
        print('cases=>', cases)
        
        for case in cases:
            if case.count == 0 or case.count == '0':
                continue;
            else:
                # for ldx in range(0,case.count):
                _runcase(username, taskid, case, plan, planresult, is_verify, kind=None)
        
        # plan
        planre = (len([x for x in planresult]) == len([x for x in planresult if x == True]))
        
        if planre:
            plan.last = 'success'
            setRunningInfo(callername, planid, taskid, 0)
            plan.is_running = 0
            plan.save()
            viewcache(taskid, username, kind,
                      "结束计划[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-green'>success</span>" % plan.description)
        else:
            plan.last = 'fail'
            setRunningInfo(callername, planid, taskid, 0)
            plan.is_running = 0
            plan.save()
            viewcache(taskid, username, kind,
                      "结束计划[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-red'>fail</span>" % plan.description)
        # 处理日志
        threading.Thread(target=dealDeBuginfo, args=(taskid,)).start()
        
        ##清除请求session
        clear_task_session('%s_%s' % (taskid, callername))
        ##产生内置属性
        
        _save_builtin_property(taskid, username)
        
        ##生成本地报告
        MainSender.gen_report(taskid, MainSender.gethtmlcontent(taskid, ''))
        ##发送报告
        config_id = plan.mail_config_id
        if config_id:
            mail_config = MailConfig.objects.get(id=config_id)
            user = User.objects.get(name=username)
            mail_res = MainSender.send(taskid, user, mail_config)
            dingding_res = MainSender.dingding(taskid, user, mail_config)
            print("发送邮件 结果[%s]" % mail_res)
            viewcache(taskid, username, kind, mail_res)
            print("发送钉钉通知 结果[%s]" % dingding_res)
            viewcache(taskid, username, kind, dingding_res)
    
    except Exception as e:
        # traceback.print_exc()
        print(traceback.format_exc())
        viewcache(taskid, username, kind, '执行计划未知异常[%s]' % traceback.format_exc())
    
    finally:
        clear_data(username, _tempinfo)

def _step_process_check(callername, taskid, order, kind):
    """
    return (resultflag,msg)
    order.follw_id:业务数据id
    """
    result = "not start"
    try:
        user = User.objects.get(name=callername)
        businessdata = BusinessData.objects.get(id=order.follow_id)
        
        if businessdata.count == 0:
            # viewcache(taskid,callername,None,'[%s]执行次数=0 略过..'%businessdata.businessname)
            return ('omit', "测试点[%s]执行次数=0 略过." % businessdata.businessname)
        preplist = businessdata.preposition.split("|") if businessdata.preposition is not None else ''
        postplist = businessdata.postposition.split("|") if businessdata.postposition is not None else ''
        db_check = businessdata.db_check
        itf_check = businessdata.itf_check
        status, paraminfo = gettestdataparams(order.follow_id)
        
        # print('bbid=>',businessdata.id)
        status1, step = gettestdatastep(businessdata.id)
        
        username = callername
        
        if status is not 'success':
            return (status, paraminfo)
        if status1 is not 'success':
            return (status1, step)
        
        viewcache(taskid, username, kind, "--" * 100)
        viewcache(taskid, username, kind,
                  "开始执行步骤[<span style='color:#FF3399'>%s-%s</span>] 测试点[<span style='color:#FF3399'>%s</span>]" % (
                      order.value, step.description, businessdata.businessname))
        
        dbid = step.db_id
        if dbid:
            desp = DBCon.objects.get(id=int(dbid)).description
            set_top_common_config(taskid, desp, src='step')
        
        ##前置操作
        status, res = _call_extra(user, preplist, taskid=taskid, kind='前置操作')  ###????
        if status is not 'success':
            return (status, res)
        
        if step.step_type == "interface":
            viewcache(taskid, username, kind, "数据校验配置=>%s" % db_check)
            viewcache(taskid, username, kind, "接口校验配置=>%s" % itf_check)
            headers = []
            
            text, statuscode, itf_msg = '', -1, ''
            
            if step.content_type == 'xml':
                if re.search('webservice', step.url):
                    headers, text, statuscode, itf_msg = _callinterface(taskid, user, step.url, str(paraminfo), 'post',
                                                                        None, 'xml')
                    text = text.replace('&lt;', '<')
                    text = re.findall('(?<=\?>).*?(?=</ns1:out>)', text, re.S)[0]
                    text = '\n' + text
                else:
                    text, statuscode, itf_msg = _callsocket(taskid, user, step.url, body=str(paraminfo))
            else:
                headers, text, statuscode, itf_msg = _callinterface(taskid, user, step.url, str(paraminfo), step.method,
                                                                    step.headers, step.content_type, step.temp, kind)
            
            viewcache(taskid, username, kind,
                      "<span style='color:#009999;'>请求响应=><xmp style='color:#009999;'>%s</xmp></span>" % text)
            
            if len(str(statuscode)) == 0:
                return ('fail', itf_msg)
            elif statuscode == 200:
                ##后置操作
                status, res = _call_extra(user, postplist, taskid=taskid, kind='后置操作')  ###????
                if status is not 'success':
                    return (status, res)
                
                if db_check:
                    res, error = _compute(taskid, user, db_check, type="db_check", kind=kind)
                    if res is not 'success':
                        print('################db_check###############' * 20)
                        return ('fail', error)
                # else:
                #   viewcache(taskid,username,kind,'数据校验没配置 跳过校验')
                
                if itf_check:
                    if step.content_type in ('json', 'urlencode') and not headers['content-type'].__contains__('xml'):
                        res, error = _compute(taskid, user, itf_check, type='itf_check', target=text, kind=kind,
                                              parse_type='json', rps_header=headers)
                    else:
                        res, error = _compute(taskid, user, itf_check, type='itf_check', target=text, kind=kind,
                                              parse_type='xml', rps_header=headers)
                    
                    if res is not 'success':
                        return ('fail', error)
                # else:
                #   viewcache(taskid,username,kind,'接口校验没配置 跳过校验')
                
                return ('success', '')
            else:
                return ('fail', 'statuscode=%s' % statuscode)
            
            if itf_msg:
                print('################itf-msg###############' * 20)
                return ('fail', itf_msg)
        
        elif step.step_type == "function":
            viewcache(taskid, username, kind, "数据校验配置=>%s" % db_check)
            # viewcache("接口返回校验=>%s"%itf_check)
            
            # methodname=re.findall("(.*?)\(.*?\)", step.body.strip())[0]
            # builtinmethods=[x.name for x in getbuiltin() ]
            # builtin=(methodname in builtinmethods)
            
            viewcache(taskid, username, kind, "调用函数=>%s" % step.body)
            
            #print('关联id=>', step.related_id)
            res, msg = _callfunction(user, step.related_id, step.body, paraminfo, taskid=taskid)
            viewcache(taskid, username, kind, "函数执行结果=>%s" % res)
            
            # print('fjdajfd=>',res,msg)
            if res is not 'success':
                return res, msg
            
            status, res = _call_extra(user, postplist, taskid=taskid, kind='后置操作')  ###????
            if status is not 'success':
                return (status, res)
            
            if db_check:
                res, error = _compute(taskid, user, db_check, type='db_check', kind=kind)
                if res is not 'success':
                    return ('fail', error)
                else:
                    return ('success', '')
            else:
                # viewcache(taskid,username,kind,'数据校验没配置 跳过校验')
                return ('success', '')
    
    except Exception as e:
        # traceback.print_exc()
        print(traceback.format_exc())
        return ("error", "执行任务[%s] 未处理的异常[%s]" % (taskid, traceback.format_exc()))

def _callsocket(taskid, user, url, body=None, kind=None, timeout=1024):
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
            print(traceback.format_exc())
        
        finally:
            sock.close()
            return recvdata
    
    cs=None
    try:

        url_rv=_replace_variable(user, url,taskid=taskid)
        if url_rv[0] is not 'success':
            return ('','',url_rv[1])
        url_rp=_replace_property(user, url_rv[1],taskid=taskid)
        if url_rp[0] is not 'success':
            return ('','',url_rp[1])

        url=url_rp[1]
        
        ##
        body_rv = _replace_variable(user, body,taskid=taskid);
        if body_rv[0] is not 'success':
            return ('', '', body_rv[1])
        body_rp = _replace_property(user, body_rv[1],taskid=taskid)
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
        print('Content-Length=>', length)
        sendmsg = 'Content-Length:' + str(length) + '\r\n' + body
        
        viewcache(taskid, user.name, None, '执行socket请求')
        viewcache(taskid, user.name, None, "<span style='color:#009999;'>请求IP=>%s</span>" % host)
        viewcache(taskid, user.name, None, "<span style='color:#009999;'>请求端口=>%s</span>" % port)
        viewcache(taskid, user.name, None,
                  "<span style='color:#009999;'>发送报文=><xmp style='color:#009999;'>%s</xmp></span>" % sendmsg)
        # viewcache(taskid, user.name,None,"<span style='color:#009999;'>body=>%s</span>"%sendmsg)
        
        cs.sendall(bytes(sendmsg, encoding='GBK'))
        
        # recv_bytes=cs.recv(1024)
        # responsexml=b''
        
        # while True:
        #   recv_bytes =cs.recv(1024)
        #   print(2222)
        #   responsexml+=recv_bytes
        #   if not len(recv_bytes):
        #       break;
        
        return _getback(cs), 200, ''
    except:
        if cs:
            cs.close()
        err = traceback.format_exc()
        print(err)
        return ('', '', err)



def _callinterface(taskid, user, url, body=None, method=None, headers=None, content_type=None, props=None, kind=None):
    """
    返回(rps.text,rps.status_code,msg)
    """
    ##url data headers过滤
    viewcache(taskid, user.name, kind, "执行接口请求=>")
    if content_type == 'formdata':
        return ('', '', '', 'form-data方式暂不支持..')
    viewcache(taskid, user.name, kind, "<span style='color:#009999;'>content_type=>%s</span>" % content_type)
    viewcache(taskid, user.name, kind, "<span style='color:#009999;'>原始url=>%s</span>" % url)
    url_rp = _replace_property(user, url)
    if url_rp[0] is not 'success':
        return ('', '', '', url_rp[1])
    url_rv = _replace_variable(user, url_rp[1], taskid=taskid)
    if url_rv[0] is not 'success':
        return ('', '', '', url_rv[1])
    url = url_rv[1]
    viewcache(taskid, user.name, kind, "<span style='color:#009999;'>url=>%s</span>" % url)
    
    viewcache(taskid, user.name, kind,
              "<span style='color:#009999;'>原始params=><xmp style='color:#009999;'>%s</xmp></span>" % body)
    data_rp = _replace_property(user, body)
    if data_rp[0] is not 'success':
        return ('', '', '', data_rp[1])
    data_rv = _replace_variable(user, data_rp[1], taskid=taskid)
    if data_rv[0] is not 'success':
        return ('', '', '', data_rv[1])
    body = data_rv[1]
    viewcache(taskid, user.name, kind,
              "<span style='color:#009999;'>params=><xmp style='color:#009999;'>%s</xmp></span>" % body)
    
    # body=json.loads(body)
    
    # print(type(headers))
    viewcache(taskid, user.name, kind, "<span style='color:#009999;'>原始headers=>%s</span>" % (headers))
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
    viewcache(taskid, user.name, kind, "<span style='color:#009999;'>headers=>%s</span>" % {**default, **headers})
    viewcache(taskid, user.name, kind, "<span style='color:#009999;'>method=>%s</span>" % method)
    
    if content_type == 'json':
        # body=body.encode('utf-8')
        default["Content-Type"] = 'application/json;charset=UTF-8'
        body = json.dumps(eval(body))
    elif content_type == 'xml':
        default["Content-Type"] = 'application/xml'
        body = body.encode('utf-8')
    elif content_type == 'urlencode':
        # body=body.encode('utf-8')
        # body=json.loads(body)
        try:
            print('urlencode=>', body)
            if body.startswith("{"):
                body = eval(body)
            else:
                body = body.encode('UTF-8')
        
        except:
            print('参数转化异常：', traceback.format_exc())
            return ('', '', '', '接口参数格式不对 请检查..')
        default["Content-Type"] = 'application/x-www-form-urlencoded;charset=UTF-8'
    elif content_type == 'xml':
        isxml = 0
    else:
        raise NotImplementedError("content_type=%s没实现" % content_type)
    
    # viewcache(taskid,user.name,kind,"body[old]=%s"%body)
    
    # print("method=>",method)
    rps = None
    
    if method == "get":
        session = get_task_session('%s_%s' % (taskid, user.name))
        rps = session.get(url, params=body, headers={**default, **headers})
    elif method == 'post':
        # print(body.decode())
        # print({**default,**headers})
        # print(body)
        session = get_task_session('%s_%s' % (taskid, user.name))
        rps = session.post(url, data=body, headers={**default, **headers})
    
    # print("textfdafda=>",rps.text)
    else:
        return ('', '', '', "请求方法%s没实现.." % method)
    
    ###响应报文中props处理
    status, err = _find_and_save_property(user, props, rps.text)
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
        f = Function.objects.get(id=functionid)
    except:
        pass
    
    # flag
    if call_method_name in ('dbexecute2', 'dbexecute','local_to_ftp','ftp_to_local','local_file_check'):
        call_method_params.append("taskid='%s'" % taskid)
        call_method_params.append("callername='%s'" % user.name)
    
    call_str = '%s(%s)' % (call_method_name, ','.join(call_method_params))
    
    print('测试函数调用=>', call_str)
    ok = _replace_variable(user, call_str, src=1, taskid=taskid)
    if re.search(r"\(.*?(?=,taskid)", ok[1]):
        viewcache(taskid, user, None, "替换变量后的函数参数=>%s" % re.search(r"(?<=\().*?(?=,taskid)", ok[1]).group())
    
    res, call_str = ok[0], ok[1]
    if res is not 'success':
        return (res, call_str)

    print('1'*900)

    return Fu.call(f, call_str, builtin=builtin,username=user.name,taskid=taskid)


def _call_extra(user, call_strs, taskid=None, kind='前置操作'):
    # print('执行[%s]:%s'%(kind,call_strs))
    f = None
    builtinmethods = [x.name for x in getbuiltin()]
    # call_list=call_strs.split('|');
    for s in call_strs:
        if not s.strip():
            continue
        
        if s == 'None' or s is None:
            continue;
        
        status, call_str = _replace_variable(user, s)
        if status is not 'success':
            return (status, res)
        
        methodname = ''
        try:
            methodname = re.findall('(.*?)\(', s)[0]
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
                viewcache(taskid, user.name, None, "<span style='color:#FF3333;'>函数库中发现多个匹配函数 这里使用第一个匹配项</span>")
        
        status, res = Fu.call(f, call_str, builtin=isbuiltin,username=user.name,taskid=taskid)
        viewcache(taskid, user.name, None, "执行[<span style='color:#009999;'>%s</span>]%s" % (kind, s))
        if status is not 'success':
            return (status, res)
    
    # viewcache(taskid,username,kind,"数据校验配置=>%s"%db_check)
    
    return ('success', '操作[%s]全部执行完毕' % call_strs)



def _compute(taskid, user, checkexpression, type=None, target=None, kind=None, parse_type='json', rps_header=None):
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
                print('ress1=>', ress)
                
                if ress[0] is 'success':
                    viewcache(taskid, user.name, None,
                              "校验表达式[<span style='color:#009999;'>%s</span>] 结果[<span style='color:#009999;'>%s</span>]" % (
                                  old, ress[0]))
                else:
                    viewcache(taskid, user.name, None,
                              "校验表达式[<span style='color:#FF6666;'>%s</span>] 结果[<span style='color:#FF6666;'>%s</span>] 原因[校验表达式[<span style='color:#FF6666;'>%s</span>]" % (
                                  old, ress[0], ress[1]))
                
                resultlist.append(ress)
        
        elif type == "itf_check":
            #
            
            for item in checklist:
                print('check', item)
                old = item
                item = _legal(item)
                ress = _eval_expression(user, item, need_chain_handle=True, data=target, taskid=taskid,
                                        parse_type=parse_type, rps_header=rps_header)
                print('ress2=>', ress)
                if ress[0] is 'success':
                    viewcache(taskid, user.name, None,
                              "校验表达式[<span style='color:#009999;'>%s</span>] 结果[<span style='color:#009999;'>%s</span>]" % (
                                  old, ress[0]))
                else:
                    msg = ress[1]
                    if msg is False:
                        msg = '表达式不成立'
                    viewcache(taskid, user.name, None,
                              "校验表达式[<span style='color:#FF6666;'>%s</span>] 结果[<span style='color:#FF6666;'>%s</span>] 原因[<span style='color:#FF6666;'>%s</span>]" % (
                                  old, ress[0], msg))
                
                resultlist.append(ress)
        
        
        else:
            return ('error', '计算表达式[%s]异常[_compute type传参错误]' % checkexpression)
        # print("结果列表=>",resultlist)
        # errmsgs=[flag for flag,msg in resultlist if isinstance(x,(str))]
        failmsg = '请检查_compute函数,_eval_expression函数返回fail时没传失败消息'
        
        print('resultlist=>', resultlist)
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
        print('==replace=>%s' % expressionsep)
        eval(expressionsep)
    except Exception as e:
        print('==_replace异常')
        
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
    # else:
    #   msg="不能合法化的表达式!=>%s"%expressionsep
    #   #viewcache(msg)
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
    try:
        
        # print("ourexpression=>",ourexpression)
        exp_rp = _replace_property(user, ourexpression)
        # print('qqqqq=>',exp_rp)
        
        # print('exp-pr=>',exp_rp)
        if exp_rp[0] is not 'success':
            return exp_rp
        
        exp_rv = _replace_variable(user, exp_rp[1], taskid=taskid)
        if exp_rv[0] is not 'success':
            return exp_rv
        # print('exp_rv=<',exp_rv)
        
        exp = exp_rv[1]
        
        res = None
        
        if need_chain_handle is True:
            
            k, v, op = _separate_expression(exp)
            print('获取的项=>', k, v, op)
            data = data.replace('null', "'None'").replace('true', "'True'").replace("false", "'False'")
            # print('data=>',data)
            
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
                # print('响应头=>',rh)
                
                if op == '$':
                    flag = rh.__contains__(v)
                elif op == '==':
                    act = rh
                    expect = str(v).strip()
                    # print('act=>%s expect=>%s'%(act,expect))
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
                    # print('类型=>',type(parse_type))
                    # print('data=>')
                    # print(data)
                    # 消除content-type首行
                    data = '\n'.join(data.split('\n')[1:])
                    print('reee', data)
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
            
            print('表达式合成{%s(%s),%s(%s),%s(%s)}' % (k, type(k), op, type(op), v, type(v)))
            
            if type(k) == type(v):
                exp = "".join([str(k), op, str(v)])
            else:
                exp = "".join([str(k), op, str(v)])
            # return ('fail','表达式[%s]校验不通过 期望[%s]和实际类型[%s]不一致'%(ourexpression,type(v),type(k)))
            # res=eval(exp)
            
            rr = eval(exp)
            if isinstance(rr, (tuple,)):
                raise RuntimeError('需要特殊处理')
            
            print("实际计算表达式[%s] 结果[%s]" % (exp, rr))
        
        return ('success', '') if rr is True else ('fail', '表达式%s校验失败' % ourexpression)
    except:
        print(traceback.format_exc())
        print('表达式等号两边加单引号后尝试判断..')
        exp = exp.replace("<br>", '')
        # return ('error','表达式[%s]计算异常[%s]'%(ourexpression,traceback.format_exc()))
        try:
            print('_op=>', _op)
            print('_exp=>', exp)
            for op in _op:
                if op in exp:
                    key = exp.split(op)[0]
                    value = exp.split(op)[1]
                    print('key=>', key)
                    print('value=>', value)
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
                    
                    print('判断结果=>', res)
                    if res is True:
                        return ('success', res)
                    else:
                        return ('fail', res)
            
            return ('fail', '')
        
        except:
            print('表达式计算异常.')
            return ('error', '表达式[%s]计算异常[%s]' % (ourexpression, traceback.format_exc()))



def _replace_function(user,str_,taskid=None):
    '''计算函数引用表达式
    '''
    # print('--计算引用表达式=>',str_)

    resultlist=[]
    builtinmethods=[x.name for x in getbuiltin()]
    str_=str(str_)

    call_str_list=re.findall('\$\[(.*?)\]',str_)

    if len(call_str_list)==0:return ('success',str_)

    for call_str in call_str_list:
        fname=re.findall('(.*?)\(', call_str)
        f=None
        try:
            f=Function.objects.get(name=fname[0])
        except:
            pass

        status,res=Fu.call(f,call_str,builtin=(lambda:True if fname in builtinmethods else False)(),username=user.name,taskid=taskid)
        resultlist.append((status,res))

        if status is 'success':
            print('替换函数引用 %s => %s '%('$[%s]'%call_str,str(res)))
            str_=str_.replace('$[%s]'%call_str,str(res))


    if len([x for x in resultlist if x[0] is 'success'])==len(resultlist):
        print('--成功计算引用表达式=>',str_)
        return ('success',str_)
    else:
        alist=[x[1] for x in resultlist if x[0] is not 'success']
        print('--异常计算引用表达式=>',alist[0])
        return ('error',alist[0])


        
def _replace_variable(user, str_, src=1, taskid=None):
    """
    返回(success,替换后的新字符串)
    返回(fail,错误消息)
    src:同_gain_compute()
    """
    if taskid is not None:
        pid = taskid.split('__')[0]
        pname = taskid.split('__')[1]
    try:
        old = str_
        varnames = re.findall('{{(.*?)}}', str_)


        for varname in varnames:


            
            vars = Variable.objects.filter(key=varname)
            var = None
            for m in vars:
                x = json.loads(Tag.objects.get(var=m).planids)
                if pname in x and pid in x.get(pname):
                    var = m
                    viewcache(taskid, user.name, None, '找到局部变量，将使用局部变量 %s 描述：%s' % (varname,var.description))
                    break
            if var is None:
                for m in vars:
                    try:
                        var = Tag.objects.get(var=m, isglobal=1).var
                        viewcache(taskid, user.name, None, '未找到局部变量，将使用全局变量 %s 描述：%s' % (varname,var.description))
                    except:
                        pass
                if var is None:
                    return ('error', '字符串[%s]变量替换异常[%s] 请检查包含变量是否已配置' % (str_, traceback.format_exc()))
                
            gain_rv = _replace_variable(user, var.gain, src=src, taskid=taskid)
            if gain_rv[0] is not 'success':
                # print(11)
                return gain_rv
            gain = gain_rv[1]
            
            value_rv = _replace_variable(user, var.value, src=src, taskid=taskid)
            if value_rv[0] is not 'success':
                # print(1221)
                return value_rv
            value = value_rv[1]
            
            is_cache = var.is_cache
            
            if len(gain) == 0 and len(value) == 0:
                warnings.warn("变量%s的获取方式和默认值至少填一项" % varname)
            elif len(gain) > 0 and len(value) > 0:
                old = old.replace('{{%s}}' % varname, str(value))
                # __replace_route["%s.%s"%(user.name,varname)]=value
                warnings.warn('变量%s获取方式和值都设定将被当做常量，获取方式和缓存失效' % varname)
            
            
            elif len(gain) == 0 and len(value) > 0:
                old = old.replace('{{%s}}' % varname, str(value))
                viewcache(taskid, user.name, None, '替换变量 {{%s}}=>%s' % (varname, value))
            # __replace_route["%s.%s"%(user.name,varname)]=value
            
            elif len(gain) > 0 and len(value) == 0:
                v = None
                if is_cache is True:
                    v = __varcache.get('%s.%s' % (user, varname))
                    if v is None:
                        v = _gain_compute(user, gain, src=src, taskid=taskid)
                        if v[0] is not 'success':
                            # print(14441)
                            return v
                        else:
                            v = v[1]
                        old = old.replace('{{%s}}' % varname, str(v))
                        viewcache(taskid, user.name, None, '替换变量 {{%s}}=>%s' % (varname, v))
                
                
                
                else:
                    v = _gain_compute(user, gain, src=src, taskid=taskid)
                    if v[0] is not 'success':
                        # print(11999)
                        return v
                    else:
                        v = v[1]
                    
                    # if v is None:
                    #   return ('error','')
                    old = old.replace('{{%s}}' % varname, str(v))
                    viewcache(taskid, user.name, None, '替换变量 {{%s}}=>%s' % (varname, v))
        
        return ('success', old)
    except Exception as e:
        print(traceback.format_exc())
        return ('error', '字符串[%s]变量替换异常[%s] 请检查包含变量是否已配置' % (str_, traceback.format_exc()))



def is_valid_where_sql(call_str):
    '''
    获取方式输入验证
    '''
    if call_str is None or len(call_str.strip()) == 0:
        return True
    
    call_str = call_str.strip()
    is_function = _is_function_call(call_str)
    print('is_function=>', is_function)
    
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
        # print('匹配结果=>',res,gain_str)
        if _is_function_call(gain_str):
            ##是方法调用
            # tzm=Fu.tzm_compute(gain_str,"(.*?)\((.*?)\)")
            flag = Fu.tzm_compute(gain_str, '(.*?)\((.*?)\)')
            print('flag1', flag)
            ms = list(Function.objects.filter(flag=flag))
            functionid = None
            if len(ms) == 0:
                # functionid=None
                # flag=Fu.tzm_compute(gain_str,'(.*?)\(.*?\)')
                # print('flag2', flag)
                try:
                    functionid = Function.objects.get(flag=flag).id
                except:
                    functionid = ''
                    pass
            elif len(ms) == 1:
                functionid = ms[0].id
            else:
                functionid = ms[0].id
                viewcache(taskid, user.name, None, "<span style='color:#FF3333;'>函数库中发现多个匹配函数 这里使用第一个匹配项</span>")
            # warnings.warn('库中存在两个特征码相同的自定义函数')
            
            a = re.findall('(.*?)\((.*?)\)', gain_str)
            call_method_name = a[0][0]
            call_method_params = a[0][1].split(',')
            
            if functionid is None:
                return ('error', '没查到匹配函数请先定义[%s,%s]' % (gain_str, flag))
            else:
                print('functionid=>', functionid)
            # return _callfunction(user, functionid, gain_str)
            return _callfunction(user, functionid, call_method_name, call_method_params, taskid=taskid)
        # return Fu.call(user,tzm,gain_str)
        
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
                    return op.db_execute2(gain_str, taskid=taskid, callername=user.name)
                else:
                    return op.db_execute(gain_str, taskid=taskid, callername=user.name)
            else:
                return ('success', '"%s"' % gain_str.strip())
    
    
    except Exception as e:
        # traceback.print_exc()
        return ('error', traceback.format_exc())


def _replace_property(user, str_,taskid=None):
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
        
        print('str_=>', str_)
        b = re.findall("\$\{(.*?)\}", str_)
        # viewcache("b length=>",len(b))
        # c=a+b
        c = b
        for it in c:
            # viewcache("key=>",it)
            # print('tmp==>',it)
            cur = it
            
            print("取属性==")
            print(_tempinfo, username, it)
            v = _tempinfo.get(username).get(it)
            
            # viewcache("vvv=>",v)
            if v is None:
                # raise RuntimeError('没有定义属性$%s 请先定义'%it)
                pass
            old = old.replace(r"${%s}" % it, str(v))
        
        # print('属性替换=》',old)
        
        return ('success', old)
    except Exception as e:
        print(traceback.format_exc())
        return ('error', '请检查是否定义属性%s 错误消息:%s' % (cur, traceback.format_exc()))


def _save_builtin_property(taskid, username):
    '''
    测试报告可用内置属性
     ${TASK_ID}
     ${TASK_REPORT_URL}
     ${PLAN_ID}
     ${PLAN_NAME}
     ${PLAN_RESULT}
     ${PLAN_CASE_TOTAL_COUNT}
     ${PLAN_CASE_SUCCESS_COUNT}
     ${PLAN_CASE_FAIL_COUNT}
     ${PLAN_STEP_TOTAL_COUNT}
     ${PLAN_STEP_SUCCESS_COUNT}
     ${PLAN_STEP_FAIL_COUNT}
     ${PLAN_STEP_SKIP_COUNT}
     #${PLAN_SUCCESS_RATE}
    '''
    detail = gettaskresult(taskid)
    if detail == {}:
        print('==内置属性赋值提前结束，执行结果表无数据')
        return
    
    base_url = settings.BASE_URL
    url = "%s/manager/querytaskdetail/?taskid=%s" % (base_url, taskid)
    save_data(username, _tempinfo, 'TASK_ID', detail['taskid'])
    save_data(username, _tempinfo, 'TASK_REPORT_URL', url)
    save_data(username, _tempinfo, 'PLAN_ID', detail['planid'])
    save_data(username, _tempinfo, 'PLAN_NAME', detail['planname'])
    save_data(username, _tempinfo, 'PLAN_RESULT',
              (lambda: 'success' if int(float(detail['success_rate'])) == 1 else 'fail')())
    save_data(username, _tempinfo, 'PLAN_CASE_TOTAL_COUNT', str(len(detail['cases'])))
    # save_data(username,_tempinfo, 'PLAN_CASE_SUCCESS_COUNT', detail[''])
    # save_data(username,_tempinfo, 'PLAN_CASE_FAIL_COUNT', detail[''])
    save_data(username, _tempinfo, 'PLAN_STEP_TOTAL_COUNT', detail['total'])
    save_data(username, _tempinfo, 'PLAN_STEP_SUCCESS_COUNT', detail['success'])
    save_data(username, _tempinfo, 'PLAN_STEP_FAIL_COUNT', detail['fail'])
    save_data(username, _tempinfo, 'PLAN_STEP_SKIP_COUNT', detail['skip'])
    save_data(username, _tempinfo, 'PLAN_SUCCESS_RATE', detail['success_rate'])


def _find_and_save_property(user, dict_str, reponsetext):
    """
    属性保存 如响应json中没相关字段 则当做字符串
    """
    cur = None
    # print(type(dict_str),len(dict_str))
    try:
        if dict_str is None or len(dict_str.strip()) == 0:
            # print('NOOOO'*100)
            return ('success', '')
        
        d = eval(dict_str)
        # print(reponsetext)
        # print("d=>",d)
        for k, v in d.items():
            cur = k
            p = JSONParser(reponsetext)
            print('================_find_and_save_property==========')
            # print(p)
            # print(k,v)
            v1 = p.getValue(v)
            
            if not v1:
                # return ('fail','通过[%s]获取属性值失败,请检查'%v)
                v1 = v
            
            save_data(user.name, _tempinfo, k, v1)
        return ('success', '')
    
    except Exception as e:
        print(traceback.format_exc())
        return ('error', "用户%s属性缓存失败=>属性%s" % (user.name, cur))


def save_data(username, d, k, v):
    """
    """
    try:
        if d.get(username) is None:
            d[username] = {}
        
        d[username][k] = v
        
        print('存属性==')
        print(username, k, v)
        
        viewcache(username, "用户%s缓存数据=> %s=%s" % (username, k, v))
    
    except:
        raise RuntimeError("存property失败=>%s" % k)


def clear_data(username, d):
    """
    清空用户相关缓存信息
    """
    for key in list(d.keys()):
        if username in key:
            del d[key]
    
    viewcache(username, "清空用户%s缓存信息" % username)


class Struct(object):
    
    def __init__(self, data):
        self.datastr = str(data)
    
    def getValue(self, xpath):
        raise NotImplementedError("")
    
    def translate(self, chainstr):
        raise NotImplementedError("")


# class XMLParser(Struct):
#   def __init__(self,data):
#       pass

#   def getValue(self,xpath):
#       pass

#   def translate(self,chainstr):
#       pass

class XMLParser(Struct):
    def __init__(self, data):
        self.root = ET.fromstring(str(data))
    
    def getValue(self, xpath):
        
        print('查找=>', xpath)
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
            # print('ms=>',ms)
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
                # print('search=>','.'+route_path)
                # print('res=>',self.root.find('.'+route_path).attrib)
                return self.root.find('.' + route_path).attrib.get(propname, 'None')
        try:
            # print('search=>','.'+route_path)
            return self.root.find('.' + route_path).text
        except:
            return 'None'


class JSONParser(Struct):
    
    def __init__(self, data):
        
        # print("传入=>",data)
        self.obj = eval(self._apply_filter(data))
        
        # 兼容不同的系统 有些系统喜欢返回JSON字符串 有些json
        for i in range(5):
            if isinstance(self.obj, (str,)):
                self.obj = eval(self.obj)
    
    # print('==JSONParser 数据转字典=>',self.obj,type(self.obj))
    
    # print("待匹配数据=>",self.obj)
    
    def _apply_filter(self, msg):
        # print("leix=",type(msg))
        msg = msg.replace("true", "True").replace("false", "False").replace("null", "None")
        # print(msg)
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
            print('==当前数据=>%s' % type(self.obj))
            try:
                
                print('flag=>', self.obj.get('data', 'None'))
            except:
                pass
            print("==xpath查询=>%s" % xpath)
            try:
                
                r = eval(xpath)
                # if r is None:
                #   r=''
                # print('xpath=>',xpath)
                # print("hello."
                # print("type=>",type(r))
                
                return r
            except:
                print(errms)
                return chainstr
        else:
            print(errms)
            return chainstr


# def check(self,chainstr,expected):

#   #print(type(self.getValue(chainstr)),type(expected))

#   return str(self.getValue(chainstr))==str(expected)


class MainSender:
    '''
    测试报告工具类
    '''
    
    # my_sender='971406187@qq.com'    # 发件人邮箱账号
    # my_pass = 'mafkywyadboibfbj'              # 发件人邮箱密码
    # my_receive={
    # # 'hujj':'15157266151@126.com',
    # # 'hujj2':'971406187@qq.com',
    # 'hujj3':'hujj@fingard.com',
    # # 'chl':"chenhy@fingard.com",
    # # 'fhp':'fuhp@fingard.com',
    # # 'syc':'shanyc@fingard.com',
    # # 'xsl':'xuesl@fingard.com',
    # # 'zby':'zhengby@fingard.com',
    # # 'zjr':'zhanjr@fingard.com'
    # }
    # subject=""
    # workcontent=[
    
    # '1.新框架所有页面 编辑删除[100% 删除没做依赖检查后面加]',
    # '2.测试邮件配置分任务[15% 做了部分接口和数据模型调整]',
    # '3.迁移脚本优化',
    # '4.迁移用例',
    # '5.优化',
    # 'a.所有接口的session失效跳转',
    # 'b.一些重要bug修复 如步骤和用例调序bug修复',
    # 'c.删除依赖检查',
    # 'd.增加测试步骤测试用例时的批量操作',
    # 'e.增加文本验证规则',
    # 'f.@字符数据库关联查询 变量输入快捷键'
    # 'g.详情查看'
    
    # ]
    
    @classmethod
    def _format_addr(cls, s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))
    
    # @classmethod
    # def getworkcontent(cls):
    #   msg=''
    #   for line in cls.workcontent:
    #       msg+="<p>%s</p>"%line
    #   return msg
    @classmethod
    def gethtmlcontent(cls, taskid, rich_text):
        
        data = gettaskresult(taskid)
        
        # cls.subject='%s自动化测试报告-%s'%(data['planname'],str(datetime.datetime.now())[0:10])
        cls.subject = '%s自动化测试报告-%s' % (data['planname'], '2019-10-31')
        cssstr = '<style type="text/css">body{font-family:Microsoft YaHei}.success{color:#093}.fail{color:#f03}.skip{color:#f90}.error{color:#f0f}table{width:95%;margin:auto}th{background-color:#39c;color:#fff}td{background-color:#eee;text-align:center}</style>'
        bodyhtml = ''
        # bodyhtml='<span style="float:right;font-size:1px;font-color:#eee;">%s-%s</span>'%(data['taskid'],data['planid'])
        bodyhtml += '<h2 style="text-align: center;">[%s]接口测试报告</h2>' % data['planname']
        bodyhtml += "<p class='attribute'><strong>测试结果</strong></p>"
        bodyhtml += "<table><tr><th>#Samples</th><th>Failures</th><th>Success Rate</th><th>Average Time</th><th>Min Time</th><th>Max Time</th></tr><tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr></table>" % (
            data['total'], data['fail'], data['success_rate'], data['average'], data['min'], data['max'])
        bodyhtml += "<strong>测试详情</strong>"
        
        for case in data['cases']:
            bodyhtml += '<p style="text-indent:2em;" >用例名[%s]</p>' % (case['casename'])
            
            # bodyhtml+='<table>'
            # bodyhtml+="<tr><th>执行序号</th><th>结果</th><th>耗时(ms)</th><th>步骤名称</th><th>api</th><th>接口验证</th><th>数据验证</th><th>消息</th></tr>"
            steps_iterator = case['steps']
            for iter_index, vs in steps_iterator.items():
                bodyhtml += '<p>第%s次迭代</p>' % iter_index
                
                bodyhtml += '<table>'
                bodyhtml += "<tr><th>执行序号</th><th>结果</th><th>耗时(ms)</th><th>步骤名称</th><th>api</th><th>接口验证</th><th>数据验证</th><th>消息</th></tr>"
                for step in vs:
                    print('nnufa=>', step)
                    bodyhtml += '<tr>'
                    bodyhtml += '<td style="width:100px;">%s</td>' % step['num']
                    bodyhtml += '<td style="width:100px;" class="%s">%s</td>' % (step['result'], step['result'])
                    bodyhtml += '<td style="width:100px;">%s</td>' % step['spend']
                    bodyhtml += '<td style="width:200px;" title="%s">%s</td>' % (step['stepname'], step['stepname'])
                    bodyhtml += '<td style="width:200px;">%s</td>' % step['api']
                    bodyhtml += '<td style="width:100px;">%s</td>' % step['itf_check']
                    bodyhtml += '<td style="width:100px;">%s</td>' % step['db_check']
                    bodyhtml += '<td>%s</td>' % step['error']
                    bodyhtml += '</tr>'
                
                bodyhtml += '</table>'
        
        return cssstr + rich_text + '<br/>' + bodyhtml
    
    @classmethod
    def send(cls, taskid, user, mail_config):
        ret = 0
        error = ''
        try:
            is_send_mail = mail_config.is_send_mail
            if is_send_mail == 'close':
                return '=========发送邮件功能没开启 跳过发送================='
            sender_name = configs.EMAIL_HOST_USER
            sender_nick = configs.EMAIL_sender_nick
            sender_pass = configs.EMAIL_HOST_PASSWORD
            to_receive = mail_config.to_receive
            
            rich_text_rp = _replace_property(user, mail_config.rich_text)
            rich_text = ''
            if rich_text_rp[0] is 'success':
                rich_text_rv = _replace_variable(user, rich_text_rp[1], taskid=taskid)
                if rich_text_rv[0] is 'success':
                    rich_text = rich_text_rv[1]
                else:
                    ret = 1
                    error = '变量替换异常,检查变量是否已定义'
            else:
                ret = 1
                error = '属性替换异常 可用属性'
            
            smtp_host = configs.EMAIL_HOST  # "smtp.qq.com"
            smtp_port = configs.EMAIL_PORT  # 465
            subject = ''
            description = mail_config.description
            description_rp = _replace_property(user, description)
            if description_rp[0] is 'success':
                description_rv = _replace_variable(user, description_rp[1], taskid=taskid)
                if description_rv[0] is 'success':
                    subject = description_rv[1] + '————' + str(time.strftime("%m-%d %H:%M", time.localtime()))
                else:
                    ret = 1
                    error = '变量替换异常,检查变量是否已定义'
            
            else:
                ret = 1
                error = '属性替换异常 可用属性'
            
            htmlcontent = cls.gethtmlcontent(taskid, rich_text)
            msg = MIMEText(htmlcontent, 'html', 'utf-8')
            msg['From'] = formataddr([sender_nick, sender_name])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
            msg['To'] = '%s' % ','.join([cls._format_addr('<%s>' % to_addr) for to_addr in
                                         list(to_receive.split(','))])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
            # msg['Subject']=cls.subject          # 邮件的主题，也可以说是标题
            msg['Subject'] = subject
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)  # 发件人邮箱中的SMTP服务器，端口是25
            server.login(sender_name, sender_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
            server.sendmail(sender_name, list(to_receive.split(',')), msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
            server.quit()  # 关闭连接
        
        
        
        
        
        
        except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
            print(traceback.format_exc())
            ret = 2
            error = traceback.format_exc()
        
        return cls._getdescrpition(mail_config.to_receive, ret, error)
    
    @classmethod
    def gen_report(cls, taskid, htmlcontent):
        print('==本地缓存测试报告')
        with open('./local_reports/report_%s.html' % taskid, 'w') as f:
            f.write(htmlcontent)
    
    @classmethod
    def _getdescrpition(cls, to_receive, send_result, error=None):
        res = None
        if send_result is 0:
            res = '发送成功'
        elif send_result is 1:
            res = '发送成功 但邮件内容可能有小问题[%s]' % error
        
        elif send_result is 2:
            res = '发送失败[%s]' % error
        
        return '========================发送邮件 收件人:%s 结果：%s' % (to_receive, res)
    
    @classmethod
    def dingding(cls, taskid, user, mail_config):
        try:
            is_send_dingding = mail_config.is_send_dingding
            if is_send_dingding == 'close':
                return '=========发送钉钉功能没开启 跳过发送================='
            dingdingtoken = mail_config.dingdingtoken
            if dingdingtoken == '' or dingdingtoken is None:
                return '=========钉钉token为空 跳过发送================='
            else:
                url = 'https://oapi.dingtalk.com/robot/send?access_token=' + dingdingtoken
                res = gettaskresult(taskid)
                pagrem = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": "自动化测试报告",
                        "text": "计划【%s】的测试报告已生成：\n\n" % (res["planname"]) +
                                "> ***测试结果*** :\n\n" +
                                ">          用例总数：%s\n\n" % (res["total"]) +
                                ">          失败数量：%s\n\n" % (res["fail"]) +
                                ">          成功率：%s\n\n" % (res["success_rate"]) +
                                "> ###### %s [详情](%s) \n" % (time.strftime('%m-%d %H:%M', time.localtime(time.time())),
                                                             settings.BASE_URL + "/manager/querytaskdetail/?taskid=" + taskid)
                    },
                    "at": {
                        "isAtAll": True
                    }
                }
                headers = {
                    'Content-Type': 'application/json'
                }
                requests.post(url, data=json.dumps(pagrem), headers=headers)
                
                send_result = 0
        except:
            send_result = 1
        return cls._getdingding(mail_config.dingdingtoken, send_result)
    
    @classmethod
    def _getdingding(cls, dingdingtoken, send_result):
        if send_result == 0:
            res = '发送钉钉消息成功'
        elif send_result == 1:
            res = '发送钉钉消息失败'
        return '=========发送钉钉通知 结果：%s=================' % (res)


def upload_personal_file(filemap,username):
    upload_dir=os.path.join(os.path.dirname(__file__),'storage','private','File',username)
    try:

        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        for filename in filemap:
            filepath=os.path.join(upload_dir,filename)
            with open(filepath,'wb') as f:
                f.write(filemap[filename])
    except:
        print(traceback.format_exc())
        return ('error','写入异常'+traceback.format_exc())

    return ('success','本地写完')

class Transformer(object):
    _businessid_cache = dict()
    
    def __init__(self, callername, byte_list, content_type, taskid):
        
        print('【Transformer工具初始化】')    
        self._before_transform_check_flag = ('success', '')
        self._difference_config_file(byte_list)
        self.transform_id = taskid
        self.callername = callername
        self._has_create_var = False
    
    def _difference_config_file(self, byte_list):
        '''
        区分配置文件&用例文
        '''
        print('【识别上传文件】')
        try:
            print('上传文件数量=>', len(byte_list))
            for byte in byte_list:
                cur_workbook = xlrd.open_workbook(file_contents=byte)
                try:
                    global_sheet = cur_workbook.sheet_by_name('Global')
                    self.config_workbook = cur_workbook
                except:
                    self.data_workbook = getattr(self, 'data_workbook', [])
                    self.data_workbook.append(cur_workbook)
            
            ##校验文件
            print('配置=>', getattr(self, 'config_workbook', None))
            print('数据=>', getattr(self, 'data_workbook', []))
            if getattr(self, 'config_workbook', None) is None:
                self._before_transform_check_flag = ('fail', '没上传配置文件')
                return
            
            if getattr(self, 'data_workbook', []) == []:
                self.data_workbook = []
                self._before_transform_check_flag = ('fail', '没上传用例文件')
                return
            
            if len(self.data_workbook) > 1:
                self._before_transform_check_flag = ('fail', '暂时不支持1个配置文件对应多个case文件')
                return
        except:
            print(traceback.format_exc())
            self._before_transform_check_flag = ('error', '无法区分配置和用例文件')
            return
        
        self._before_transform_check_flag = ('success', '上传文件识别成功..')
    
    def _check_file_valid(self):
        """
        检查文件是否合法
        """
        return self._before_transform_check_flag
    
    def _check_function(self):
        '''
        检查函数是否定义 related_id准备
        '''
        all_function=list(Function.objects.all())+getbuiltin()
        all_function_name=[x.name for x  in all_function]
        try:
            #检查业务数据函数名称
            for dwb in self.data_workbook:
                act_data=self._get_workbook_sheet_cache(dwb,'执行数据')

                for rowdata in act_data:
                    vs=''
                    for v in rowdata.values():
                        vs+=str(v).strip()
                    if not vs:
                        continue;

                    step=Step()
                    step.author=User.objects.get(name=self.callername)
                    func_field_value=rowdata['函数名称']
                    # if func_field_value  not in all_function_name:
                    #print('canshu=>',rowdata['参数值'])
                    if '：' not in  rowdata['参数值'] and ':' not in rowdata['参数值']:
                        funcname=rowdata['函数名称']

                        #print('h=>',funcname)
                        if funcname not in(all_function_name):
                            #print('row=>',rowdata)
                            print('all_function_name',all_function_name)
                            return ('fail','执行数据页没定义函数[%s],请先定义'%funcname)

            #检查变量定义获取方式
            var_sheet=self._get_workbook_sheet_cache(dwb,'变量定义')
            for rowdata in var_sheet:
                gain=rowdata['获取方式'].strip()
                if _is_function_call(gain):
                    print('gain=>',gain)
                    methodname=re.findall('(.*?)\(.*?\)', gain)[0]
                    if methodname not in all_function_name:
                        print('all_function_name',all_function_name)
                        
                        return ('fail','变量定义页没定义函数[%s],请先定义'%methodname)

            return ('success','函数校验通过')
        except:
            return ('error','函数库内校验发生异常[%s]'%traceback.format_exc())

    def _set_content_type_flag(self,kind):
        #kind=('json','xml','urlencode','not json','not xml','not urlencode')
        if kind=='json':
            self.is_xml=False
        elif kind=='xml':
            self.is_xml=True
        elif kind=='urlencode':
            self.is_xml=False
        elif kind=='not_json':
            self.is_xml=None
        elif kind=='not_xml':
            self.is_xml=False
        elif kind=='not_urlencode':
            self.is_xml=True

    def _get_itf_basic_conifg(self):
        '''
        获取config init基本配置
        '''
        init_cache = self._get_workbook_sheet_cache(self.config_workbook, 'Init')
        
        for rowdata in init_cache:
            # print('basic_config=>',rowdata)
            if rowdata['默认对象'].lower().strip() == 'y' and rowdata['对象类型'].lower().strip() == 'interface':
                # print('fadfljadfljadajf')
                pv = rowdata['参数']
                if self._is_xml_h():
                    return {
                        'host': pv.split(',')[0],
                        'port': pv.split(',')[1],
                        
                    }
                else:
                    return {
                        'host': pv.split(',')[0]
                        
                    }
        
        return None
    
    def _is_xml_h(self):
        init_cache = self._get_workbook_sheet_cache(self.config_workbook, 'Init')
        
        for rowdata in init_cache:
            if rowdata['默认对象'].lower().strip() == 'y' and rowdata['对象类型'].lower().strip() == 'interface':
                pv = rowdata['参数']
                size = len(pv.split(','))
                # print('====www=>',size)
                
                return True if size == 5 else False
    
    def _get_itf_detail_config(self):
        '''获取接口具体配置信息
        '''
        res={}

        script_cache=self._get_workbook_sheet_cache(self.config_workbook, 'Scripts')
        for rowdata in script_cache:
            try:
                rowdatalist=rowdata['脚本全称'].split(',')
                # print('脚本全称=>',rowdatalist)

                path=rowdatalist[0]
                method=rowdatalist[1]
                content_type='urlencode'

                if len(rowdatalist)>2:
                    content_type=rowdatalist[2]

                res[rowdata['脚本简称']]={
                'path':path,
                'method':method,
                'content_type':(lambda:'urlencode' if content_type=='iphone' else content_type)()
                }
            except:
                print(traceback.format_exc())
                continue;

        return res

    def _get_workbook_sheet_cache(self,workbook,sheetname):
        """
        获取sheet键值数据
        """

        cache=[]

        sheet=workbook.sheet_by_name(sheetname)
        sheet_rows=sheet.nrows
        titles=sheet.row_values(0)
        title_order_map={}
        for index in range(len(titles)):
            title_order_map[str(index)]=str(titles[index])


        for rowindex in range(1, sheet_rows):
            row_map={}
            row=sheet.row_values(rowindex)
            for cellindex in range(len(row)):
                ctype=sheet.cell(rowindex,cellindex).ctype
                
                k=title_order_map[str(cellindex)]
                v=row[cellindex]
                #print('%s->%s'%(k,v))
                if 2==ctype:
                    v=int(v)
                row_map[k]=v

            cache.append(row_map)
        # print(kv_map)
        return cache

    def _get_business_sheet_cache(self):
        '''
        获取业务数据缓存
        '''
        cache={}
        index=0

        for dwb in self.data_workbook:
            sheets=dwb.sheet_names()
            for sheetname in sheets :
                if sheetname not in ('变量定义','执行数据'):
                    key='%s_I%s'%(sheetname,index)
                    cache[key]=self._get_workbook_sheet_cache(dwb, sheetname)

            index=index+1
        return cache


    def _get_act_data(self,d):
        r=[]
        for x in d:
            r+=d[x]

        return r


    def transform(self):

        print('【准备数据转化】')
        status,msg=self._check_file_valid()
        #print('检查结果=>',status,msg)
        if status!='success':
            return (status,msg)

        status,msg=self._check_function()
        if status!='success':
            return (status,msg)
        #workbookflag->actdata
        self.act_data_map={}
        self.act_data=[]
        self.var_data=[]
        resultlist=[]

        workbook_flag=0
        for dwb in self.data_workbook:
            result=[]
            self.act_data_map[workbook_flag]=self._get_workbook_sheet_cache(dwb,'执行数据')
            workbook_flag=workbook_flag+1
            self.act_data=self._get_workbook_sheet_cache(dwb,'执行数据')+self.act_data
            self.var_data=self._get_workbook_sheet_cache(dwb,'变量定义')+self.var_data

            print('【开始转换】接收数据集[%s,%s]'%(dwb,self.config_workbook))
            resultlist=[]
            f4=self.add_case()
            f5=self.add_plan()
            f1=self.add_var()
            f2=self.addbusinessdata()

            time.sleep(5)

            f3=self.add_step_data()
            f6=self.add_db_con()

            print('f1=>',f1)
            print('f2=>',f2)
            print('f3=>',f3)
            print('f4=>',f4)
            print('f5=>',f5)
            print('f6=>',f6)
            result.append(f1)
            result.append(f2)
            result.append(f3)
            result.append(f4)
            result.append(f5)
            result.append(f6)
            resultlist.append(result)
        ##分析结果
        for rs in resultlist:
            for r in rs:
                if r[0]!='success':
                    self._rollback()
                    return ('fail','转换失败')

        return('success','转换成功!')


    def _get_header(self,hid,**kws):
        _f=('数据编号','头部说明')
        c=''
        # print('fdajflda=>',self._get_business_sheet_cache().keys())
        cache=self._get_business_sheet_cache().get('head_I0')
        for rowdata in cache:
            if str( rowdata['数据编号'])==str(hid):
                pass

                vv=''
                for k,v in rowdata.items():
                    if k in('数据编号','头部说明'):continue;
                    if k in kws:
                        try:
                            vv=int(kws.get(k))
                        except:
                            vv=kws.get(k)

                        c+='<%s>%s</%s>'%(k,vv,k)
                    else:
                        try:
                            vv=int(v)
                        except:
                            vv=v

                        c+='<%s>%s</%s>'%(k,vv,k)


        # with open('header.txt','a+') as f:
        #     f.write('<Head>%s</Head>\n\n'%c)
        return '<Head>%s</Head>'%c

    def addbusinessdata(self):
        '''
        插入业务数据
        '''
        try:
            print('【开始添加业务数据】')
            _meta=['测试点','DB检查数据','UI检查数据','接口检查数据','数据编号']
            _m={
            '测试点':'businessname',
            'DB检查数据':'db_check',
            'UI检查数据':'',
            '接口检查数据':'itf_check',
            '数据编号':'',
            '头部信息':'',
            '头部说明':'',

            }

            ##接口业务数据
            print('--开始添加接口业务数据')

            for sheetname,cache in self._get_business_sheet_cache().items():

                print('sss=>',sheetname,cache)

                if sheetname.__contains__('head') or sheetname.__contains__('报文说明'):
                    continue;
                rowindex=0
                
                sheet_index=1#sheet明细行号
                for rowdata in cache:
                   #s print('rowdata=>',rowdata)
                    #print('=>1')

                    xmlcontent=''
                    params={}

                    headm={}
                    hid=-1

                    headv=rowdata.get('头部信息',None)##error
                    if headv:
                        headv=str(headv).replace('\n','')
                        hlist=str(headv).split('|')
                        hid=hlist[0]
                        
                        if len(hlist)>1:
                            for i in range(1,len(hlist)):
                                headm[hlist[i].split('=')[0]]=hlist[i].split('=')[1]

                    business=BusinessData()
                    business.businessname='%s_%s_%s'%(sheetname,sheet_index,self.transform_id)
                    sheet_index+=1

                    #print('=>2')
                    for fieldname,value in rowdata.items():
                        #print('=>3')
                        try:
                            if fieldname  in _m:
                                #print('=>4')
                                # if fieldname =='测试点':
                                #     business.businessname="%s_%s"%(value.strip(),self.transform_id)
                                #     #business.businessname="%s"%(value.strip())
                                #     continue
                                if fieldname=='DB检查数据':
                                    #business.db_check=self._replace_var(value)
                                    dck=self._replace_var(value)
                                    dck=dck.replace('\n','')
                                    if dck:
                                        if dck.__contains__('sleep'):
                                            business.db_check='|'.join(dck.split('|')[1:])
                                            business.postposition=dck.split('|')[0]

                                    continue
                                elif fieldname=='接口检查数据':
                                    business.itf_check=self._replace_var(value)
                                    continue
                            else:
                                #print('=>5')
                                ##hhhh
                                #print('==========fdafda=>',self._is_xml_h())
                                if self._is_xml_h():

                                    nodeinfo=''
                                    if fieldname.startswith('<'):
                                        xmlcontent+=fieldname

                                    else:
                                        xmlcontent+='<%s>%s</%s>'%(fieldname,value,fieldname)

                                else:
                                    params[fieldname]=value
                        except:
                            print(traceback.format_exc())

                    #print('=>6')
                    if  params.get('json',None):
                        params=params.get('json')
                    #print('=>7')
                    params=(str(params)).replace('"',"'").replace('\n','')
                    #print('[%s]params=>%s'%(sheet_index,str(params)))

                    if xmlcontent == '':
                        business.params=self._replace_var(params,sheet_index+1,rowindex+1)
                    else:
                        xmlcontent='<Root>#head#%s</Root>'%xmlcontent
                        xmlcontent=xmlcontent.replace('#head#',self._get_header(hid,**headm))
                        
                        business.params=self._replace_var(xmlcontent)

                    business.save()
                    print('==添加接口业务数据[%s]'%business)
                    self._businessid_cache['%s:%s'%(sheetname,rowindex+1)]=business.id
                    rowindex=rowindex+1

            print('---开始添加函数业务数据')
            ##函数业务数据
            aaindex=0
            for rowdata in self.act_data:
                aaindex=aaindex+1
                # print('--尝试添加函数业务数据')
                paramfield=rowdata['参数值']
                # print('paramfield=>',paramfield)
                if  not paramfield.__contains__('：') and not paramfield.__contains__(':'):
                    #businessname重复校验
                    name="%s_%s_%s"%(rowdata['测试要点概要'].strip(),str(aaindex),self.transform_id)
                    #name="%s"%(rowdata['测试要点概要'].strip())
                    size=len(list(BusinessData.objects.filter(businessname=name)))
                    # print('size=>',size)
                    if size>0:
                        print('测试点已存在[%s] next'%name)
                        continue
                    business=BusinessData()
                    business.businessname=name
                    business.params=self._replace_var(paramfield)
                    business.save()
                    print('==添加函数业务数据[%s]'%business)

            return('success','')
        except:
            return ('error','插入业务数据异常=>%s'%traceback.format_exc())



    def _get_step_names(self):
        return [x for x in self.data_workbook.sheet_names() if x not in('变量定义','执行数据')]


    def _replace_var(self,old,si=None,li=None):
        '''
        1.执行数据参数值
        2.DB检查数据
        3.接口检查数据
        4.数据字段
        '''
        # print('【变量转化】=>',old)
        varlist=re.findall('{[ru,].*?}', old)
        if len(varlist)>0:
            for x in varlist:
                varname=re.findall('{[ru],(.*?)}', x)
                # print(varname)
                if x.__contains__('lv_Signature') and si and li:
                    old=old.replace(x,'{{%s_%s_%s_%s}}'%(str(varname[0]).split('$')[0],si,li,self.transform_id))
                    print('替换签名变量名=>','{{%s_%s_%s_%s}}'%(str(varname[0]).split('$')[0],si,li,self.transform_id))
                else:
                    old=old.replace(x,'{{%s_%s}}'%(varname[0],self.transform_id))

        # print('转换后=>',old)
        return old


    def add_db_con(self):
        '''
        添加数据连接 oracle默认sid方式

        '''
        try:
            global_sheet=self._get_workbook_sheet_cache(self.config_workbook,'Global')
            con=None
            groupid=0
            for rowdata in global_sheet:
                # print('global_row->',rowdata)
                varname=rowdata['变量名称']

                if 'gv_dbtype' in varname:
                    groupid=groupid+1
                    con=DBCon()
                    dbtype=rowdata['值']
                    if dbtype.strip()=='oracle':
                        con.kind='oracle_sid'
                    else:
                        con.kind=dbtype

                elif 'gv_dbuser' in varname:
                    con.username=rowdata['值']
                elif 'gv_dbpwd' in varname or 'gv_dbpasswd' in varname:
                    con.password=rowdata['值']
                elif 'gv_dbhost' in varname:
                    con.host=rowdata['值']
                elif 'gv_dbport' in varname:
                    con.port=rowdata['值']
                elif 'gv_dbname' in varname:
                    con.dbname=rowdata['值']
                    con.host=con.dbname.split('/')[0]
                    con.dbname=con.dbname.split('/')[1]
                    if not con.port:
                        con.port='1521'
                    con.author=User.objects.get(name=self.callername)
                    con.description="库_%s_%s_%s"%(self.callername,self.transform_id,groupid)

                    print('新增数据连接=>')
                    print('dbnaem=>',con.dbname)
                    print('description=>',con.description)
                    print('username=>',con.username)
                    print('password=>',con.password)
                    print('host=>',con.host)
                    print('port=>',con.port)

                    con.save()
            return ('success','')
        except:
            return ('error','新增数据连接失败->%s'%traceback.format_exc())


    def add_step_data(self):
        '''
        添加step
        '''
        try:
            print('【开始添加步骤数据】')
            case=None

            for k,v in self.act_data_map.items():
                case=list(Case.objects.filter(description='迁移用例_%s_%s'%(self.transform_id,k)))[0]
                row_index=0
                for rowdata in v:
                    # step=Step()
                    # step.temp=''
                    # step.author=User.objects.get(name=self.callername)
                    func_field_value=rowdata['函数名称']
                    # if func_field_value  not in all_function_name:
                    row_index+=1
                    if rowdata['参数值'].__contains__('：') or  rowdata['参数值'].__contains__(':') :
                        #接口
                        bkname=''
                        if rowdata['参数值'].__contains__(':'):
                            bkname=rowdata['参数值'].split(':')[0]

                        elif rowdata['参数值'].__contains__('：'):
                            bkname=rowdata['参数值'].split('：')[0]

                        # print('bkname3=>',rowdata['参数值'].split('：'))
                        # print('bkname2=>',bkname)

                        ##多条
                        if rowdata['参数值'].__contains__('-'):
                            start=0
                            end=0
                            try:
                                start=rowdata['参数值'].split(':')[1].split('-')[0]
                                end=rowdata['参数值'].split(':')[1].split('-')[1]
                            except:
                                start=rowdata['参数值'].split('：')[1].split('-')[0]
                                end=rowdata['参数值'].split('：')[1].split('-')[1]

                            #count=int(end)-int(start)+1
                            for i in range(int(start),int(end)+1):
                                print('==多条=')

                                step=Step()
                                step.temp=''
                                step.author=User.objects.get(name=self.callername)

                                basic_config=self._get_itf_basic_conifg()
                                detail_config=self._get_itf_detail_config()

                                #print('基础配置=>',basic_config)
                                #
                                #print('详细配置=>',detail_config)
                                step.step_type='interface'
                                step.body=''
                                
                                step.headers=''
                                step.description='%s_%s_%s'%(rowdata['测试要点概要'],i,self.transform_id)

                                funcname=rowdata['函数名称']
                                try:
                                    step.content_type=detail_config.get(funcname).get('content_type')
                                    step.method=detail_config.get(funcname).get('method')
                                except:
                                    print('配置文件里没找到函数名[%s]称所对应的的配合信息'%funcname)

                                print('===============start===content_type 负值===================')
                                if self._is_xml_h():
                                    
                                    print('==================content_type 负值===================')
                                    if basic_config:
                                        step.content_type='xml'
                                        step.url='base_url_%s'%self.transform_id
                                        ##
                                        try:
                                            if not self._has_create_var:
                                                v=Variable()
                                                v.author=User.objects.get(name=self.callername)
                                                v.key='base_url_%s'%self.transform_id
                                                v.value='%s:%s'%(basic_config.get('host',''),basic_config.get('port',''))
                                                v.description='迁移url'
                                                v.gain=''
                                                v.save()

                                                self._has_create_var=True
                                        except:
                                           # print('9'*100)
                                           pass
                                else:
                                    print('==非xml')
                                    print('basic_config=>',basic_config)
                                    if basic_config:
                                        print('=有基础配置=')
                                        try:

                                            #step.url="%s%s"%(basic_config.get('host',''),detail_config.get(funcname).get('path',''))
                                            step.url="%s%s"%('{{base_url_%s}}'%self.transform_id,detail_config.get(funcname).get('path',''))
                                           # print('$$'*100)   
                                            print('step.url=>',step.url)
                                        except:
                                            print(traceback.format_exc())
                                        ##
                                        try:

                                            if not self._has_create_var:
                                                v=Variable()
                                                v.author=User.objects.get(name=self.callername)
                                                v.key='base_url_%s'%self.transform_id
                                                v.value=basic_config.get('host','')
                                                v.description='迁移url'
                                                v.gain=''
                                                v.save()

                                                self._has_create_var=True
                                        except:
                                           # print('9'*100)
                                           pass

                                is_exist=len(list(Step.objects.filter(description=step.description)))
                                if is_exist==0:
                                    step.save()
                                    print('添加步骤=>',step)
                                else:
                                    step=Step.objects.get(description=step.description)

                                ##step关联业务数据
                                self.add_case_step_relation(case.id, step.id)
                                print('--尝试获取业务id=>','%s_I0_%s_%s'%(bkname,i,self.transform_id))
                                b=BusinessData.objects.get(businessname='%s_I0_%s_%s'%(bkname,i,self.transform_id))
                                print('--成功获取业务id=>%s'%b)
                               

                                
                                self.add_step_business_relation(step.id, b.id)
                                #self.add_step_bussiness_relation2(step.id, self.data_workbook[k],rowdata['参数值'])
                                #self.add_case_business_relation2(case.id, self.data_workbook[k],rowdata['参数值'])

                        #单条
                        else:
                            print('===单条===')
                            step=Step()
                            step.temp=''
                            step.author=User.objects.get(name=self.callername)

                            lineindex=None
                            try:
                                lineindex=rowdata['参数值'].split(':')[1]
                            except:
                                lineindex=rowdata['参数值'].split('：')[1]


                            basic_config=self._get_itf_basic_conifg()
                            detail_config=self._get_itf_detail_config()

                            #print('基础配置=>',basic_config)
                            #
                            #print('详细配置=>',detail_config)
                            step.step_type='interface'
                            step.body=''
                            step.headers=''
                            #step.description='%s_%s_%s'%(rowdata['测试要点概要'],row_index,self.transform_id)
                            step.description='%s_%s_%s'%(rowdata['测试要点概要'],lineindex,self.transform_id)
                            funcname=rowdata['函数名称']
                            try:
                                step.content_type=detail_config.get(funcname).get('content_type')
                                step.method=detail_config.get(funcname).get('method')

                            except:
                                print('配置文件里没找到函数名[%s]称所对应的的配合信息'%funcname)
                            if self._is_xml_h():
                                if basic_config:
                                    #step.url='%s:%s'%(basic_config.get('host',''),basic_config.get('port',''))
                                    step.url="{{base_url_%s}}"%self.transform_id
                                    step.content_type='xml'

                                    try:
                                        if not self._has_create_var:
                                            v=Variable()
                                            v.author=User.objects.get(name=self.callername)
                                            v.key='base_url_%s'%self.transform_id
                                            v.value='%s:%s'%(basic_config.get('host',''),basic_config.get('port',''))
                                            v.description='迁移url'
                                            v.gain=''
                                            v.save()

                                            self._has_create_var=True
                                    except:
                                       # print('9'*100)
                                       pass

                            else:
                                if basic_config:
                                    #step.url="%s%s"%(basic_config.get('host',''),detail_config.get(funcname).get('path',''))
                                    step.url="%s%s"%('{{base_url_%s}}'%self.transform_id,detail_config.get(funcname).get('path',''))
                                    try:
                                        if not self._has_create_var:
                                            v=Variable()
                                            v.author=User.objects.get(name=self.callername)
                                            v.key='base_url_%s'%self.transform_id
                                            v.value=basic_config.get('host','')
                                            v.description='迁移url'
                                            v.gain=''
                                            v.save()

                                            self._has_create_var=True
                                    except:
                                       # print('9'*100)
                                       pass                      
                            # print('url=>',step.url)
                            # step.url=self._replace_var(step.url)

                            is_exist=len(list(Step.objects.filter(description=step.description)))
                            if is_exist==0:
                                step.save()
                                print('添加步骤=>',step)
                            else:
                                step=Step.objects.get(description=step.description)
                                print('已存在步骤[%s]'%step)

                            ##step关联业务数据
                            self.add_case_step_relation(case.id, step.id)

                            print('bkname=>',bkname)
                            print('lineindex=>',lineindex)
                            print('带匹配=>','%s_I0_%s_%s'%(bkname,lineindex,self.transform_id))
                            business_id=BusinessData.objects.get(businessname='%s_I0_%s_%s'%(bkname,lineindex,self.transform_id)).id
                            self.add_step_business_relation(step.id, business_id)
                            #self.add_step_bussiness_relation2(step.id, self.data_workbook[k],rowdata['参数值'])
                            #self.add_case_business_relation2(case.id, self.data_workbook[k],rowdata['参数值'])

                    else:
                        #函数
                        step=Step()
                        step.temp=''
                        step.author=User.objects.get(name=self.callername)
                        step.step_type='function'
                        step.body=func_field_value
                        # print('functionname=>',step.body)
                        step.description="%s_%s_%s"%(rowdata['测试要点概要'].strip(),row_index,self.transform_id)
                        #step.description="%s"%(rowdata['测试要点概要'].strip())
                        try:
                            step.related_id=Function.objects.get(name=step.body.strip()).id
                        except:
                            pass

                        step.save()
                        #step关联业务数据
                        try:
                            name="%s_%s_%s"%(rowdata['测试要点概要'].strip(),row_index,self.transform_id)

                            # l=list(BusinessData.objects.filter(businessname=name))
                            # print('size=>',len(l))
                            print('待匹配业务名=>',name)
                            businessId=BusinessData.objects.get(businessname=name).id
                            #businessId=BusinessData.objects.get(businessname="%s"%rowdata['测试要点概要'].strip()).id
                            self.add_case_step_relation(case.id, step.id)
                            self.add_step_business_relation(step.id, businessId)
                            #self.add_case_businss_relation(case.id, businessId)

                        except:
                            print(traceback.format_exc())
                            print('函数步骤没找到关联业务数据[%s]'%name)

            time.sleep(1)

            # genorder(kind='step',parentid=case.id)
            print('==添加步骤结束')
            return ('success','')
        except:
            return ('error','添加步骤异常[%s]'%traceback.format_exc())



    def add_plan(self):
        plan=None
        try:
            print('【添加计划】')
            dsp='迁移计划_%s'%self.transform_id
            length=len(list(Plan.objects.filter(description=dsp)))
            if length==0:
                plan=Plan()
                plan.description=dsp
                plan.author=User.objects.get(name=self.callername)
                plan.save()
                print('=新建计划=>',plan)

                #
                product=None
                L=list(Product.objects.filter(description='数据迁移'))
                exist=len(L)
                if exist==0:
                    product=Product()
                    product.description='数据迁移'
                    product.author=User.objects.get(name=self.callername)
                    product.save()
                else:
                    product=L[0]

                order=Order()
                order.kind='product_plan'
                order.main_id=product.id
                order.follow_id=plan.id
                order.value='1.1'
                order.author=User.objects.get(name=self.callername)
                order.save()
            else:
                plan=list(Plan.objects.filter(description=dsp))[0]

            self.add_plan_case_relation()

            # genorder(kind='case',parentid=plan.id)
            return ('success','')

        except:
            return ('error','添加计划异常=>%s'%traceback.format_exc())

    def add_case(self):
        case=None

        try:
            for k,v in self.act_data_map.items():
                dsp='迁移用例_%s_%s'%(self.transform_id,k)
                #dsp='迁移用例_%s'%k

                length=len(list(Case.objects.filter(description=dsp)))
                if length==0:
                    case=Case()
                    case.description=dsp
                    case.author=User.objects.get(name=self.callername)
                    case.save()
                    print('【添加用例】%s'%case.description)
            return ('success','')

        except:
            return ('error','添加用例异常=>%s'%traceback.format_exc())

    def add_plan_case_relation(self):
        # print('【关联计划和用例】')
        for k in self.act_data_map:

            plan=list(Plan.objects.filter(description='迁移计划_%s'%(self.transform_id)))[0]
            #plan=list(Plan.objects.filter(description='迁移计划_%s'%self.transform_id))[0]
            case=list(Case.objects.filter(description='迁移用例_%s_%s'%(self.transform_id,k)))[0]
            # plan.cases.add(case)
            order=Order()
            order.kind='plan_case'
            order.main_id=plan.id
            order.follow_id=case.id
            order.author=User.objects.get(name=self.callername)
            order.value='1.1'
            order.save()

    def add_case_step_relation(self,case_id,step_id):
        from .cm import getnextvalue
        #print('【关联用例和业务数据】')
        # step=Step.objects.get(id=step_id)
        # case=Case.objects.get(id=case_id)
        # case.businessdatainfo.add(business)

        length=len(list(Order.objects.filter(kind='case_step',main_id=case_id,follow_id=step_id)))
        if length==0:
            order=Order()
            order.kind='case_step'
            order.main_id=case_id
            order.follow_id=step_id
            order.author=User.objects.get(name=self.callername)
            order.value=getnextvalue(order.kind,order.main_id)
            order.save()


    def add_case_step_relation2(self,case_id,workbook,paramfieldvalue):

        print('【步骤关联业务数据】')
        case=Case.objects.get(id=case_id)
        sheetname=''

        if paramfieldvalue.__contains__('：'):
            sheetname=paramfieldvalue.split('：')[0]
        elif paramfieldvalue.__contains__(':'):
            sheetname=paramfieldvalue.split(':')[0]

        cache=self._get_workbook_sheet_cache(workbook,sheetname)#?????
        # is_contain_test_point_col=cache[0].__contains__('测试点'
        #根据参数列数字筛选合适的业务数据
        rangestr=''
        if paramfieldvalue.__contains__('：'):
            rangestr=paramfieldvalue.split('：')[1]
        elif paramfieldvalue.__contains__(':'):
            rangestr=paramfieldvalue.split(':')[1]


        fit=[]
        start=''
        end=''
        if rangestr.__contains__('-'):
            start=rangestr.split('-')[0]
            end=rangestr.split('-')[1]

            fit=[x for x in cache if int(x['数据编号'])>=int(start) and int(x['数据编号'])<=int(end)]
        else:
            start=rangestr
            fit=[x for x in cache if x['数据编号']==int(start)]

        for x in fit:
            testpoint=x.get('测试点',None)
            business=None
            if testpoint:
                try:
                    business=BusinessData.objects.get(businessname="%s_%s"%(testpoint,self.transform_id))
                    #business=BusinessData.objects.get(businessname="%s"%testpoint)
                except:
                    print('业务名称[%s_%s]查找返回的业务数据有多条'%(testpoint,self.transform_id))
                    business=list(BusinessData.objects.filter(businessname="%s_%s"%(testpoint,self.transform_id)))[0]
                    #business=list(BusinessData.objects.filter(businessname="%s"%testpoint))[0]
            else:
                business=BusinessData.objects.get(businessname="%s%s_%s"%(sheetname,x.get('数据编号'),self.transform_id))
                #business=BusinessData.objects.get(businessname="%s%s"%(sheetname,x.get('数据编号')))

            case.businessdatainfo.add(business)


            length=len(list(Order.objects.filter(kind='step',main_id=case_id,follow_id=business.id)))
            if length==0:
                order=Order()
                order.kind='step'
                order.main_id=case_id
                order.follow_id=business.id
                order.author=User.objects.get(name=self.callername)
                order.save()



    def add_step_business_relation(self,step_id,business_id):
        '''
        步骤关联业务数据
        '''
        # step=Step.objects.get(id=step_id)
        # business=BusinessData.objects.get(id=business_id)
        print('add_step_business_relation')
        from .cm import getnextvalue
        
        order = Order()
        order.kind = 'step_business'
        order.main_id = step_id
        order.follow_id = business_id
        order.author = User.objects.get(name=self.callername)
        order.value = getnextvalue(order.kind, order.main_id)
        order.save()
        print('==关联函数步骤和测试点[%s]' % order)
    
    # step.businessdatainfo.add(business)
    
    def add_step_bussiness_relation2(self, step_id, workbook, paramfieldvalue):
        '''
        通过参数列定位业务数据

        '''
        from .cm import getnextvalue

        try:
            print('add_step_business_relation2')

            step=Step.objects.get(id=step_id)
            sheetname=''
            if paramfieldvalue.__contains__('：'):
                sheetname=paramfieldvalue.split('：')[0]
            elif paramfieldvalue.__contains__(':'):
                sheetname=paramfieldvalue.split(':')[0]
            cache=self._get_workbook_sheet_cache(workbook,sheetname)#?????
            # is_contain_test_point_col=cache[0].__contains__('测试点'
            #根据参数列数字筛选合适的业务数据
            rangestr=''
            if paramfieldvalue.__contains__('：'):
                rangestr=paramfieldvalue.split('：')[1]
            elif paramfieldvalue.__contains__(':'):
                rangestr=paramfieldvalue.split(':')[1]

            print('f1==>',rangestr)

            fit=[]
            start=''
            end=''
            if rangestr.__contains__('-'):
                start=rangestr.split('-')[0]
                end=rangestr.split('-')[1]

                fit=[x for x in cache if int(x['数据编号'])>=int(start) and int(x['数据编号'])<=int(end)]
            else:
                start=rangestr
                fit=[x for x in cache if int(x['数据编号'])==int(start)]


            print('f2=>',fit)
            for x in fit:
                testpoint=x.get('测试点',None)
                if testpoint:
                    try:
                        business=BusinessData.objects.get(businessname='%s_%s'%(testpoint,self.transform_id))
                        #business=BusinessData.objects.get(businessname='%s'%testpoint)
                    except:
                        print('业务名称[%s_%s]查找返回的业务数据有多条'%(testpoint,self.transform_id))
                        business=list(BusinessData.objects.filter(businessname='%s_%s'%(testpoint,self.transform_id)))[0]
                        #business=list(BusinessData.objects.filter(businessname='%s'%testpoint))[0]
                else:
                    print('-查找测试点=>%s_I0%s_%s'%(sheetname,int(x.get('数据编号')),self.transform_id))
                    business=BusinessData.objects.get(businessname="%s_I0%s_%s"%(sheetname,x.get('数据编号'),self.transform_id))
                    #business=BusinessData.objects.get(businessname="%s%s"%(sheetname,x.get('数据编号')))


                order=Order()
                order.kind='step_business'
                order.main_id=step.id
                order.follow_id=business.id
                order.author=User.objects.get(name=self.callername)
                order.value=getnextvalue(order.kind,order.main_id)
                order.save()

                print('==步骤关联测试点[%s]'%order)
                #step.businessdatainfo.add(business)
        except:
            print(traceback.format_exc())


    def add_var(self):
        try:
            signmethodname=''

            ##常规变量
            for dwb in self.data_workbook:
                var_cache=self._get_workbook_sheet_cache(dwb, '变量定义')
                for var in var_cache:
                    description=var['变量说明'].strip()
                    gain=var['获取方式'].strip()
                    key=var['变量名称'].strip()
                    value=str(var['值']).strip()
                    # is_cache=False
                    var=Variable()
                    var.description=description
                    var.key='%s_%s'%(key,self.transform_id)
                    if  var.key.__contains__('lv_Signature'):
                        signmethodname=re.findall('(.*?)\(',gain)[0]

                    var.gain=self._get_may_sql_field_value(gain)
                    if var.gain.strip():
                        var.value=''
                    else:
                        var.value=self._get_may_sql_field_value(value)
                    var.author=User.objects.get(name=self.callername)
                    var.save()
                    print('==添加变量[%s]'%var)
            

            print('签名信息=>',signmethodname)
            if signmethodname:
                ##签名变量
                si=0
                li=0
                print('--开始处理签名变量')
                for dwb in self.data_workbook:
                    sheets=dwb.sheet_names()
                    for sheetname in sheets :
                        si+=1
                        if sheetname not in ('变量定义','执行数据'):
                            datalist=self._get_workbook_sheet_cache(dwb, sheetname)
                            for d in datalist:
                                li+=1
                                pa=[]
                                for key in d:
                                    if key not in('数据编号','DB检查数据','UI检查数据','接口检查数据','Signature'):
                                        pa.append("%s='%s'"%(key,self._replace_var(str(d[key]))))

                                    if str(d[key]).__contains__('lv_Signature'):
                                        f_pa=[]
                                        f_pa.append("'{{lv_key_%s}}'"%self.transform_id)
                                        if f_pa.__contains__('WebApi'):
                                            f_pa.append("'sendPrivateKey.pem.webapi'")
                                        [f_pa.append(x) for x in pa]

                                        var=Variable()
                                        var.description=''
                                        var.key='lv_Signature_%s_%s_%s'%(si,li,self.transform_id)
                                        var.value=''
                                        var.gain="%s(%s)"%(signmethodname,','.join(f_pa))
                                        var.author=User.objects.get(name=self.callername)
                                        var.save()
                                        print('--新建签名变量=>%s'%var)



            return ('success','')
        except:
            return ('error','添加变量异常=>%s'%traceback.format_exc())

    def _get_may_sql_field_value(self,old):
        '''sql含@链接的字段的处理  多个sql库名按照第一个sql的为准
        '''
        is_first=True
        sqlmatch=re.findall(r'(select|update|delete|insert).*(from|set|into).+(where){0,1}.*', old)
        # print(sqlmatch)
        if sqlmatch:
            groupid=1
            new_sql_list=[]
            sqllist=old.split(';')
            for sql in sqllist:
                if sql.strip()=='':
                    continue;
                new_sql=''
                if is_first:
                    is_first=False
                    if '@' in sql:
                        groupid=sql.split('@')[1]
                        length=len(groupid)
                        #print('len=>',length)
                        new_sql_list.append(sql[0:-int(length+1)])
                    else:
                        new_sql_list.append(sql)


                else:
                    if '@' in sql:
                        length=len(sql.split('@')[1])
                        new_sql_list.append(sql[0:-int(length+1)])

                    else:
                        new_sql_list.append(sql)

            return ';'.join(new_sql_list)+'@'+"库_%s_%s_%s"%(self.callername,self.transform_id,groupid)
        else:
            return old

    def _delcaserelation(self,caseid):
        try:
            Case.objects.get(id=caseid).delete()

        except:
            pass

        L1=list(Order.objects.filter(kind='case_case',main_id=caseid))
        L2=list(Order.objects.filter(kind='case_step',main_id=caseid))
        for o1 in L1:
            self._delcaserelation(o1.follow_id)
            o1.delete()

        for o2 in L2:
            businesslist=list(Order.objects.filter(kind='step_business',main_id=o2.follow_id))
            for business in businesslist:
                business.delete()
                try:
                    Step.objects.get(id=order.main_id).delete()
                except:
                    pass

                try:
                    BusinessData.objects.get(id=order.follow_id).delete()
                except:
                    pass

            o2.delete()





    def _rollback(self):
        """
        """
        print('==转换失败,开始回滚操作')
        # order表删除
        plan = Plan.objects.get(description='迁移计划_%s' % self.transform_id)
        planid = plan.id
        
        L1 = list(Order.objects.filter(kind='plan_case', main_id=planid))
        for o1 in L1:
            self._delcaserelation(o1.follow_id)
        
        plan.delete()
        
        # 清除实体表
        varlist = list(Variable.objects.all())
        for var in varlist:
            if var.description.__contains__(self.transform_id):
                var.delete()
        
        dblist = list(DBCon.objects.all())
        for db in dblist:
            if db.description.__contains__(self.transform_id):
                db.delete()
        
        print('=结束回滚操作】')

class DataMove:
    '''
    计划导入导出 兼容ME2老版本转成新版本
    '''
    
    def _init_tmp(self):
        self._data = {
            
            ##实体数据
            'entity': {
                'plan': {},
                'cases': [],
                'steps': [],
                'businessdatas': [],
                'dbcons': [],
                'vars': [],
                'funcs': [],
                'authors': []
                
            },
            
            ##依赖关系
            'relation': {
                'plan_case': {
                
                },
                'step_business': {
                
                },
                'case_step': {
                
                },
                'case_case': {
                
                }
                
            }}
    
    def __init__(self):
        self._init_tmp()
    
    def export_plans(self, planids):
        pass
    
    def export_plan(self, planid, export_flag, version=2):
        
        # print(version,type(version),version==2)
        return self._export_plan_new(planid, export_flag) if version == 2 else self._export_plan_old(planid,
                                                                                                     export_flag)
    
    def _add_author(self, authorname):
        namelist = [author.get('name') for author in self._data['entity']['authors']]
        if authorname not in namelist:
            author = User.objects.get(name=authorname)
            self._data['entity']['authors'].append({
                
                'name': author.name,
                'password': author.password,
                'email': author.email,
                'sex': author.sex,
            })
    
    def _add_dbcon(self, gain):
        namelist = [x.get('description') for x in self._data['entity']['dbcons']]
        sep = gain.split('@')
        
        try:
            if sep[-1] in namelist:
                return
            
            dbcon = DBCon.objects.get(description=sep[-1])
            self._data['entity']['dbcons'].append({
                'id': dbcon.id,
                'dbname': dbcon.dbname,
                'description': dbcon.description,
                'host': dbcon.host,
                'port': dbcon.port,
                'username': dbcon.username,
                'password': dbcon.password,
                'authorname': dbcon.author.name,
                'kind': dbcon.kind,
                
            })
        except:
            print('库中没找到连接 略过=>', sep[-1])
    
    def _add_var(self, key):
        namelist = [x.get('key') for x in self._data['entity']['vars']]
        if key not in namelist:
            try:
                var = Variable.objects.get(key=key)
                self._data['entity']['vars'].append({
                    'id': var.id,
                    'description': var.description,
                    'key': var.key,
                    'value': var.value,
                    'gain': var.gain,
                    'is_cache': var.is_cache,
                    'authorname': var.author.name
                })
                
                ##gain中含变量 这里只处理两层嵌套 多的会有问题
                gainvars = re.findall("{{(.*?)}}", var.gain)
                for va in gainvars:
                    v = Variable.objects.get(key=va)
                    self._data['entity']['vars'].append({
                        'id': v.id,
                        'description': v.description,
                        'key': v.key,
                        'value': v.value,
                        'gain': v.gain,
                        'is_cache': v.is_cache,
                        'authorname': v.author.name
                    })
            except:
                print('库中没找到变量 略过=>', key)
    
    def _get_bussiness_id(self):
        return '%s_%s' % ('vid', EncryptUtils.md5_encrypt(str(datetime.datetime.now())))
    
    def _add_case_relation_data(self, case):
        from .cm import getchild
        
        ##1.用例挂步骤场景
        steplist = getchild('case_step', case.id)
        for step in steplist:
            exist_step_ids = [step.get('id') for step in self._data['entity']['steps']]
            if step.id in exist_step_ids:
                continue
            
            stepd = {}
            stepd['id'] = step.id
            stepd['step_type'] = step.step_type
            stepd['method'] = step.method
            stepd['description'] = step.description
            stepd['headers'] = step.headers
            stepd['body'] = step.body
            stepd['url'] = step.url
            stepd['content_type'] = step.content_type
            stepd['tmp'] = step.temp
            stepd['authorname'] = step.author.name
            self._add_author(step.author.name)
            stepd['db_id'] = step.db_id
            
            self._data['entity']['steps'].append(stepd)
            
            c = self._data['relation']['case_step'].get(str(case.id), [])
            ordervalue = Order.objects.get(kind='case_step', main_id=case.id, follow_id=step.id).value
            c.append((str(step.id), ordervalue))
            self._data['relation']['case_step'][str(case.id)] = list(set(c))
            
            # print('%s=>%s'%(step.description,step.step_type))
            
            businesslist = getchild('step_business', step.id)
            
            for business in businesslist:
                ###########
                businessd = {}
                businessd['id'] = business.id
                businessd['businessname'] = business.businessname
                
                businessd['itf_check'] = business.itf_check
                businessd['db_check'] = business.db_check
                businessd['params'] = business.params
                varnames = re.findall('{{(.*?)}}', business.itf_check + business.db_check + business.params)
                self._varkeys = self._varkeys + varnames
                
                print('bname=>', businessd['businessname'])
                busnamelist = [business.get('businessname') for business in self._data['entity']['businessdatas']]
                ##
                if businessd['businessname'] not in busnamelist:
                    self._data['entity']['businessdatas'].append(businessd)
                    b = self._data['relation']['step_business'].get(str(step.id), [])
                    ordervalue = Order.objects.get(kind='step_business', main_id=step.id, follow_id=business.id).value
                    b.append((str(business.id), ordervalue))
                    self._data['relation']['step_business'][str(step.id)] = list(set(b))
                    
                    varnames = re.findall('{{(.*?)}}', step.headers + step.url)
                    self._varkeys = self._varkeys + varnames
                
                if step.step_type == 'function':
                    funcname = step.body.strip()
                    builtinmethods = [x.name for x in getbuiltin()]
                    builtin = (funcname in builtinmethods)
                    
                    if builtin is False:
                        status, res = gettestdataparams(business.id)  ###????????????????
                        print('%s=>%s' % (business.businessname, business.params))
                        if status is not 'success':
                            return JsonResponse(simplejson(code=3, msg=str(res)))
                        
                        params = ','.join(res)
                        call_str = '%s(%s)' % (step.body.strip(), params)
                        flag = Fu.tzm_compute(call_str, '(.*?)\((.*?)\)')
                        print('1call_str=>', call_str)
                        # print('falg=>',flag)
                        funcs = list(Function.objects.filter(flag=flag))
                        if len(funcs) > 1:
                            return JsonResponse(simplejson(code=44, msg='找到多个匹配的自定义函数 请检查'))
                        
                        stepd['related_id'] = funcs[0].id
                        
                        # 导出使用的函数
                        func = Function.objects.get(id=funcs[0].id)
                        self._data['entity']['funcs'].append({
                            'id': func.id,
                            'kind': func.kind,
                            'name': func.name,
                            'description': func.description,
                            'flag': func.flag,
                            'body': func.body,
                            'authorname': func.author.name
                        })
                        self._add_author(func.author.name)
        
        ##2.用例嵌套场景
        caselist0 = getchild('case_case', case.id)
        for case0 in caselist0:
            cased = {}
            cased['id'] = case0.id
            cased['description'] = case0.description
            cased['authorname'] = case0.author.name
            cased['db_id'] = case0.db_id
            
            self._data['entity']['cases'].append(cased)
            d = self._data['relation']['case_case'].get(str(case.id), [])
            ordervalue = Order.objects.get(kind='case_case', main_id=case.id, follow_id=case0.id).value
            d.append((str(case0.id), ordervalue))
            self._data['relation']['case_case'][str(case.id)] = list(set(d))
            self._add_case_relation_data(case0)
    
    def _export_plan_new(self, planid, export_flag):
        from .cm import getchild
        self._data['version'] = 2.0
        self._varkeys = []
        try:
            planid = planid.split('_')[1]
            plan = Plan.objects.get(id=planid)
            self._data['entity']['plan']['id'] = plan.id
            self._data['entity']['plan']['description'] = plan.description
            self._data['entity']['plan']['authorname'] = plan.author.name
            self._add_author(plan.author.name)
            self._data['entity']['plan']['runtype'] = plan.run_type
            # self._data['entity']['plan']['runvalue']=plan.run_value
            self._data['entity']['plan']['db_id'] = plan.db_id
            
            # caselist=list(plan.cases.all())
            caselist = getchild('plan_case', plan.id)
            
            for case in caselist:
                cased = {}
                cased['id'] = case.id
                cased['description'] = case.description
                cased['db_id'] = case.db_id
                cased['authorname'] = case.author.name
                self._add_author(case.author.name)
                self._data['entity']['cases'].append(cased)
                
                a = self._data['relation']['plan_case'].get(str(planid), [])
                ordervalue = Order.objects.get(kind='plan_case', main_id=plan.id, follow_id=case.id).value
                a.append((str(case.id), ordervalue))
                self._data['relation']['plan_case'][str(planid)] = list(set(a))
                self._add_case_relation_data(case)
            
            # 统一导出变量
            for key in self._varkeys:
                self._add_var(key)
                try:
                    var = Variable.objects.get(key=key)
                    self._add_author(var.author.name)
                    self._add_dbcon(var.gain)
                except:
                    pass
            return ('success', self._data)
        except:
            return ('error', '导出转换过程发生异常[%s]' % traceback.format_exc())
    
    def _get_vid(self):
        return 'vid_%s' % (EncryptUtils.base64_encrypt(str(datetime.datetime.now())))
    
    def _export_plan_old(self, planid, export_flag):
        self._data['version'] = 1.0
        varkeys = []
        try:
            plan = Plan.objects.get(id=planid)
            self._data['entity']['plan']['id'] = plan.id
            self._data['entity']['plan']['description'] = plan.description
            self._data['entity']['plan']['authorname'] = plan.author.name
            self._add_author(plan.author.name)
            self._data['entity']['plan']['runtype'] = plan.run_type
            # self._data['entity']['plan']['runvalue']=plan.run_value
            self._data['entity']['plan']['db_id'] = ''
            
            caselist = list(plan.cases.all())
            for case in caselist:
                cased = {}
                cased['id'] = case.id
                cased['description'] = case.description
                cased['db_id'] = ''
                cased['authorname'] = case.author.name
                self._add_author(case.author.name)
                self._data['entity']['cases'].append(cased)
                
                a = self._data['relation']['plan_case'].get(str(planid), [])
                ordervalue = Order.objects.get(kind='case', main_id=plan.id, follow_id=case.id).value
                
                a.append((str(case.id), ordervalue))
                self._data['relation']['plan_case'][str(planid)] = list(set(a))
                
                steplist = list(case.steps.all())
                for step in steplist:
                    bid = self._get_vid()
                    
                    businessd = {}
                    businessd['id'] = bid  ##????
                    businessd['businessname'] = '测试点1(pl%s)' % step.id
                    businessd['itf_check'] = step.itf_check
                    businessd['db_check'] = step.db_check
                    if step.step_type == 'interface':
                        businessd['params'] = step.body
                    else:
                        businessd['params'] = re.findall('\((.*?)\)', step.body)[0]
                    
                    varnames = re.findall('{{(.*?)}}', step.itf_check + step.db_check + step.body)
                    varkeys = varkeys + varnames
                    busnamelist = [business.get('businessname') for business in self._data['entity']['businessdatas']]
                    if businessd['businessname'] not in busnamelist:
                        self._data['entity']['businessdatas'].append(businessd)
                        
                        b = self._data['relation']['case_business'].get(str(case.id), [])
                        ordervalue = Order.objects.get(kind='step', main_id=case.id, follow_id=step.id).value
                        b.append((str(bid), ordervalue))  ###?????
                        self._data['relation']['case_business'][str(case.id)] = list(set(b))
                        
                        exist_step_ids = [step.get('id') for step in self._data['entity']['steps']]
                        if step.id in exist_step_ids:
                            continue
                        
                        stepd = {}
                        # step=step[1]
                        stepd['id'] = step.id
                        stepd['step_type'] = step.step_type
                        stepd['method'] = step.method
                        stepd['description'] = step.description
                        stepd['headers'] = step.headers
                        # stepd['body']=step.body
                        stepd['url'] = step.url
                        stepd['content_type'] = step.content_type
                        stepd['tmp'] = step.temp
                        stepd['authorname'] = step.author.name
                        self._add_author(step.author.name)
                        stepd['db_id'] = ''
                        self._data['entity']['steps'].append(stepd)
                        
                        varnames = re.findall('{{(.*?)}}', step.headers + step.url)
                        varkeys = varkeys + varnames
                        c = self._data['relation']['step_business'].get(str(step.id), [])
                        c.append(str(bid))  ####???????????
                        self._data['relation']['step_business'][str(step.id)] = list(set(c))
                        
                        if step.step_type == 'function':
                            stepd['body'] = re.findall("(.*?)\(", step.body)[0]
                            funcname = re.findall("(.*?)\(", step.body.strip())[0]
                            
                            builtinmethods = [x.name for x in getbuiltin()]
                            builtin = (funcname in builtinmethods)
                            
                            if builtin is False:
                                call_str = step.body.strip()
                                flag = Fu.tzm_compute(call_str, '(.*?)\((.*?)\)')
                                funcs = list(Function.objects.filter(flag=flag))
                                if len(funcs) > 1:
                                    return JsonResponse(simplejson(code=44, msg='找到多个匹配的自定义函数 请检查'))
                                
                                stepd['related_id'] = funcs[0].id
                                # 导出使用的函数
                                func = Function.objects.get(id=funcs[0].id)
                                self._data['entity']['funcs'].append({
                                    'id': func.id,
                                    'kind': func.kind,
                                    'name': func.name,
                                    'description': func.description,
                                    'flag': func.flag,
                                    'body': func.body,
                                    'authorname': func.author.name
                                })
                                self._add_author(func.author.name)
            
            # 统一导出变量
            for key in varkeys:
                self._add_var(key)
                try:
                    var = Variable.objects.get(key=key)
                    self._add_author(var.author.name)
                    self._add_dbcon(var.gain)
                except:
                    pass
            return ('success', self._data)
        except:
            return ('error', '导出转换过程发生异常[%s]' % traceback.format_exc())
    
    def _hanlde_repeat_name(self, filterstr, classstr, flag):
        
        _M = {
            'Variable': '变量',
            'DBCon': '数据连接',
            'Step': '变量'
        }
        key = filterstr.split('=')[0]
        oldvalue = filterstr.split('=')[1].strip()
        callstr = "len(list(%s.objects.filter(%s='%s')))" % (classstr, key, oldvalue)
        length = eval(callstr)
        if length > 0:
            if classstr in ('Variable', 'DBCon'):
                return 'fail', '%s[%s]已存在 略过导入请手动调整' % (_M.get(classstr, ''), oldvalue)
            
            elif classstr == 'BusinessData':
                # print('yes=>',classstr)
                return ('success', oldvalue)
            else:
                # final='%s#%s'%(oldvalue,flag)
                final = oldvalue
                print('%s重复处理=>%s' % (_M.get(classstr), final))
                return ('success', final)
        else:
            return ('success', oldvalue)
    
    def import_plan(self, product_id, content_byte_list, callername):
        _cache = {}
        _msg = []
        b = b''
        for byte in content_byte_list:
            b = b + byte
        bs = b.decode()
        bl = eval(bs)
        print('【开始导入数据】 ')
        # 导入实体类
        plan = bl['entity']['plan']
        cases = bl['entity']['cases']
        steps = bl['entity']['steps']
        businessdatas = bl['entity']['businessdatas']
        dbcons = bl['entity']['dbcons']
        vs = bl['entity']['vars']
        funcs = bl['entity']['funcs']
        authors = bl['entity']['authors']
        
        ##plan
        plano = Plan()
        _cache['plan_%s' % plan.get('id')] = plano
        plano.description = plan.get('description')
        plano.description = plano.description + str(datetime.datetime.now()).split('.')[0]
        
        plano.run_type = plan.get('runtype')
        plano.db_id = plan.get('db_id')
        try:
            author = User.objects.get(name=plan.get('authorname'))
            plano.author = author
            plano.save()
            
            ##
            order = Order()
            order.kind = 'product_plan'
            order.main_id = product_id
            order.follow_id = plano.id
            order.value = '1.1'
            try:
                author = User.objects.get(name=callername)
                order.author = author
                order.save()
            except:
                author = [author for author in authors if author.get('name') == callername][0]
                authoro = User()
                authoro.name = author.get('name')
                authoro.password = author.get('password')
                authoro.email = author.get('email')
                authoro.sex = author.get('sex')
                authoro.save()
                order.author = authoro
                order.save()
        
        
        except:
            author = [author for author in authors if author.get('name') == plan.get('authorname')][0]
            authoro = User()
            authoro.name = author.get('name')
            authoro.password = author.get('password')
            authoro.email = author.get('email')
            authoro.sex = author.get('sex')
            authoro.save()
            plano.author = authoro
            plano.save()
        
        flag = 'im%s' % plano.id
        # case
        for case in cases:
            caseo = Case()
            _cache['case_%s' % case.get('id')] = caseo
            print('=缓存case=>', 'case_%s' % case.get('id'))
            status, caseo.description = self._hanlde_repeat_name("description=%s" % case.get('description'), 'Case',
                                                                 flag)
            caseo.db_id = case.get('db_id')
            
            try:
                author = User.objects.get(name=case.get('authorname'))
                caseo.author = author
                caseo.save()
            except:
                author = [author for author in authors if author.get('name') == plan.get('authorname')][0]
                authoro = User()
                authoro.name = author.get('name')
                authoro.password = author.get('password')
                authoro.email = author.get('email')
                authoro.sex = author.get('sex')
                authoro.save()
                caseo.author = authoro
                caseo.save()
        
        ##step
        for step in steps:
            stepo = Step()
            _cache['step_%s' % step.get('id')] = stepo
            stepo.step_type = step.get('step_type')
            status, stepo.description = self._hanlde_repeat_name("description=%s" % step.get('description'), 'Step',
                                                                 flag)
            stepo.headers = step.get('headers')
            stepo.body = step.get('body', '')
            stepo.url = step.get('url')
            stepo.method = step.get('method')
            stepo.content_type = step.get('content_type')
            stepo.temp = step.get('tmp')
            stepo.db_id = step.get('db_id')
            try:
                author = User.objects.get(name=step.get('authorname'))
                stepo.author = author
                stepo.save()
            except:
                author = [author for author in authors if author.get('name') == step.get('authorname')][0]
                authoro = User()
                authoro.name = author.get('name')
                authoro.password = author.get('password')
                authoro.email = author.get('email')
                authoro.sex = author.get('sex')
                authoro.save()
                stepo.author = authoro
                stepo.save()
        
        ##bussiness
        for businessdata in businessdatas:
            bd = BusinessData()
            _cache['business_%s' % businessdata.get('id')] = bd
            status, bd.businessname = self._hanlde_repeat_name("businessname=%s" % businessdata.get('businessname'),
                                                               'BusinessData', flag)
            bd.itf_check = businessdata.get('itf_check')
            bd.db_check = businessdata.get('db_check')
            bd.params = businessdata.get('params')
            bd.save()
        
        # vars
        for v in vs:
            vo = Variable()
            _cache['var_%s' % v.get('id')] = vo
            vo.description = v.get('description')
            status, vo.key = self._hanlde_repeat_name("key=%s" % v.get('key'), 'Variable', flag)
            
            if status is not 'success':
                del _cache['var_%s' % v.get('id')]
                _msg.append(vo.key)
                continue;
            vo.value = v.get('value')
            vo.gain = v.get('gain')
            vo.is_cache = v.get('is_cache')
            try:
                author = User.objects.get(name=v.get('authorname'))
                vo.author = author
                vo.save()
            except:
                author = [author for author in authors if author.get('name') == v.get('authorname')][0]
                authoro = User()
                authoro.name = author.get('name')
                authoro.password = author.get('password')
                authoro.email = author.get('email')
                authoro.sex = author.get('sex')
                authoro.save()
                vo.author = authoro
                vo.save()
        
        ##dbcons
        for con in dbcons:
            cono = DBCon()
            _cache['dbcon_%s' % con.get('id')] = cono
            status, cono.description = self._hanlde_repeat_name("description=%s" % con.get('description'), 'DBCon',
                                                                flag)
            if status is not 'success':
                del _cache['dbcon_%s' % con.get('id')]
                _msg.append(cono.description)
                continue;
            cono.kind = con.get('kind')
            cono.host = con.get('host')
            cono.port = con.get('port')
            cono.dbname = con.get('dbname')
            cono.username = con.get('username')
            cono.password = con.get('password')
            try:
                author = User.objects.get(name=con.get('authorname'))
                cono.author = author
                cono.save()
            except:
                author = [author for author in authors if author.get('name') == con.get('authorname')][0]
                authoro = User()
                authoro.name = author.get('name')
                authoro.password = author.get('password')
                authoro.email = author.get('email')
                authoro.sex = author.get('sex')
                authoro.save()
                cono.author = authoro
                cono.save()
        
        ##funcs
        for f in funcs:
            fo = Function()
            _cache['func_%s' % f.get('id')] = fo
            fo.kind = f.get('kind')
            fo.description = f.get('description')
            fo.name = f.get('name')
            status, fo.flag = self._hanlde_repeat_name("flag=%s" % f.get('flag'), 'Function', flag)
            
            if status is not 'success':
                del _cache['func_%s' % f.get('id')]
                _msg.append(fo.flag)
                continue;
            
            fo.body = f.get('body')
            
            try:
                author = User.objects.get(name=f.get('authorname'))
                fo.author = author
                fo.save()
            except:
                author = [author for author in authors if author.get('name') == f.get('authorname')][0]
                authoro = User()
                authoro.name = author.get('name')
                authoro.password = author.get('password')
                authoro.email = author.get('email')
                authoro.sex = author.get('sex')
                authoro.save()
                fo.author = authoro
                fo.save()
        # 建立依赖关系
        plan_cases = bl['relation']['plan_case']
        case_step = bl['relation']['case_step']
        case_case = bl['relation']['case_case']
        step_businesss = bl['relation']['step_business']
        
        print('[step_businesss]=>%s' % step_businesss)
        ##
        for k, vs in plan_cases.items():
            plan = _cache.get('plan_%s' % k)
            for v, ordervalue in vs:
                case = _cache.get('case_%s' % v)
                order = Order()
                order.kind = 'plan_case'
                order.main_id = plan.id
                order.follow_id = case.id
                order.value = ordervalue
                try:
                    author = User.objects.get(name=callername)
                    order.author = author
                    order.save()
                except:
                    author = [author for author in authors if author.get('name') == callername][0]
                    authoro = User()
                    authoro.name = author.get('name')
                    authoro.password = author.get('password')
                    authoro.email = author.get('email')
                    authoro.sex = author.get('sex')
                    authoro.save()
                    order.author = authoro
                    order.save()
        
        ##
        print('case_step')
        for k, vs in case_step.items():
            case = _cache.get('case_%s' % k)
            print('查询case缓存=>', 'case_%s' % k)
            for v, ordervalue in vs:
                step = _cache.get('step_%s' % v)
                order = Order()
                order.kind = 'case_step'
                order.main_id = case.id
                order.follow_id = step.id
                order.value = ordervalue
                try:
                    author = User.objects.get(name=callername)
                    order.author = author
                    order.save()
                except:
                    author = [author for author in authors if author.get('name') == callername][0]
                    authoro = User()
                    authoro.name = author.get('name')
                    authoro.password = author.get('password')
                    authoro.email = author.get('email')
                    authoro.sex = author.get('sex')
                    authoro.save()
                    order.author = authoro
                    order.save()
        ##
        print('case_case')
        for k, vs in case_case.items():
            case = _cache.get('case_%s' % k)
            for v, ordervalue in vs:
                #
                
                case0 = _cache.get('case_%s' % v)
                order = Order()
                order.kind = 'case_case'
                order.main_id = case.id
                order.follow_id = case0.id
                order.value = ordervalue
                try:
                    author = User.objects.get(name=callername)
                    order.author = author
                    order.save()
                except:
                    author = [author for author in authors if author.get('name') == callername][0]
                    authoro = User()
                    authoro.name = author.get('name')
                    authoro.password = author.get('password')
                    authoro.email = author.get('email')
                    authoro.sex = author.get('sex')
                    authoro.save()
                    order.author = authoro
                    order.save()
                    
                    print(traceback.format_exc())
        
        ##
        print('[step_businesss]')
        for k, vs in step_businesss.items():
            step = _cache.get('step_%s' % k)
            print('[1]=>')
            for v, ordervalue in vs:
                print('[2]=>')
                business = _cache.get('business_%s' % v)
                print('[business]=>', business)
                order = Order()
                order.kind = 'step_business'
                order.main_id = step.id
                order.follow_id = business.id
                order.value = ordervalue
                
                # if not ordervalue:
                #   order.value='1.1'
                
                try:
                    author = User.objects.get(name=callername)
                    order.author = author
                    order.save()
                except:
                    author = [author for author in authors if author.get('name') == callername][0]
                    authoro = User()
                    authoro.name = author.get('name')
                    authoro.password = author.get('password')
                    authoro.email = author.get('email')
                    authoro.sex = author.get('sex')
                    authoro.save()
                    order.author = authoro
                    order.save()
                
                print('[建议步骤测试点关联]=>%s' % order)
        
        # 处理回调信息
        callbackmsg = ''
        for index in range(len(_msg)):
            callbackmsg = "%s.%s" % (int(index + 1), _msg[index]) + ' '
        
        return ('success', callbackmsg)
