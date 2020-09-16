#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-10-12 09:42:34
# @Author  : Blackstone
# @to      :用例管理

import traceback, datetime,json,threading,difflib,asyncio
from manager.operate.cron import Cron
from django.db.models import Q
from manager import models as mm
from django.db import connection
from ME2.settings import logme
from concurrent.futures import  ThreadPoolExecutor,wait
import queue

from login import models as lm
from .StartPlan import RunPlan
from .context import *
from .invoker import runplan,get_run_node_plan_id
from .core import gettaskid,get_params,EncryptUtils
from manager.context import Me2Log as logger
from .operate.dataMove import DataMove
from tools.R import R
from tools.test import TreeUtil

@cache_sync
@monitor(action='添加产品')
def addproduct(request):
    product = None
    try:
        description = request.POST.get('description')
        product = mm.Product(description=description)
        product.save()
        return {
            'status': 'success',
            'msg': '新增[%s]成功' % description,
            'data': {
                'id': 'product_%s' % product.id,
                'pId': -1,
                'name': description,
                'type': 'product',
                'textIcon': 'fa icon-fa-home',
            }
        }
    except:
        logger.info(traceback.format_exc())
        return {
            'status': 'error',
            'msg': '新增[%s]异常' % product.description
        }

@cache_sync
@monitor(action='删除产品')
def delproduct(request):
    p = None
    try:
        id_ = request.POST.get('ids')
        msg = ''
        ids = id_.split(',')
        for i in ids:
            i = i.split('_')[1]
            p = mm.Product.objects.get(id=int(i))
            if len(getchild('product_plan', i)) > 0:
                return {
                    'status': 'fail',
                    'msg': '删除失败,[%s]含子数据' % p.description
                }
            p.isdelete=1
            p.save()
            
            return {
                'status': 'success',
                'msg': '删除[%s]成功' % p.description
            }
    
    except:
        return {
            'status': 'error',
            'msg': '删除[%s]异常' % p.description
        }

@cache_sync
@monitor(action='编辑产品')
def editproduct(request):
    uid = request.POST.get('uid')
    description = request.POST.get('description')
    try:
        p = mm.Product.objects.get(id=int(uid.split('_')[1]))
        pcopy=copy.deepcopy(p)
        p.description = description
        p.save()

        linkiter=mm.EditLink.objects.filter(snid='product_{}'.format(p.id))
        for link in linkiter:
            linkobj=mm.Product.objects.get(id=link.tnid.split('_')[1])
            _update_object(linkobj, _diff_object(pcopy,p,ignore_attr=['id']))
        return {
            'status': 'success',
            'msg': '编辑成功',
            'data': {
                'name': description
            }
        }
    
    except:
        logger.error(traceback.format_exc())
        return {
            'status': 'error',
            'msg': '编辑[%s]异常' % description
        }


# plan
@cache_sync
@monitor(action='新建计划')
def addplan(request):
    msg = ''
    try:
        pid = request.POST.get('pid').split('_')[1]
        description = request.POST.get('description')
        db_id = request.POST.get('dbid')
        schemename = request.POST.get('scheme')
        run_type = request.POST.get('run_type')
        before_plan = request.POST.get('before_plan')
        proxy = request.POST.get('proxy','')
        is_send_mail = 'open' if request.POST.get('is_send_mail') == 'true' else 'close'
        is_send_dingding = 'open' if request.POST.get('is_send_dingding') == 'true' else 'close'
        mail_config = mm.MailConfig(is_send_mail=is_send_mail, is_send_dingding=is_send_dingding)
        mail_config.save()
        
        plan = mm.Plan(description=description, db_id=db_id, schemename=schemename,run_type=run_type, mail_config_id=mail_config.id,before_plan=before_plan,proxy=proxy)
        plan.save()
        addrelation('product_plan',pid, plan.id)
        extmsg=''
        if run_type == '定时运行':
            config = request.POST.get('config')
            crontab = mm.Crontab()
            crontab.value = config
            crontab.plan = plan
            crontab.status = 'close'
            crontab.save()
            extmsg = Cron.addcrontab(plan.id)

        return {
            'status': 'success',
            'msg': '新增[%s]成功%s' % (description,extmsg),
            'data': {
                'id': 'plan_%s' % plan.id,
                'pId': 'product_%s' % pid,
                'name': description,
                'type': 'plan',
                'textIcon': 'fa icon-fa-product-hunt',
            }}
    except:
        return {
            'status': 'error',
            'msg': '新增失败[%s]' % traceback.format_exc()
        }

@cache_sync
@monitor(action='删除计划')
def delplan(request):
    id_ = request.POST.get('ids')
    msg = ''
    ids = id_.split(',')
    try:
        for i in ids:
            i = i.split('_')[1]
            i = int(i)
            plan = mm.Plan.objects.get(id=i)
            if len(list(getchild('plan_case', i))) > 0:
                return {
                    'status': 'fail',
                    'msg': '删除失败,[%s]含子数据' % plan.description
                }
            Cron.delcrontab(i)
            # plan.delete()
            ##消除上层依赖
            _regen_weight(request.session.get('username'), plan, trigger='del')
        # delrelation('product_plan',None, None,i)
        
        return {
            'status': "success",
            'msg': '删除成功'
        }
    
    except:
        return {
            'status': 'error',
            'msg': "删除失败[%s]" % traceback.format_exc()
        }


def handlebindplans(olddescription, newdescription, id_):
    logger.info("处理计划名修改后的标签中绑定的计划名称")
    oldtags = mm.Tag.objects.values('id', 'planids').filter(Q(planids__contains=olddescription))
    for oldtag in oldtags:
        planids = json.loads(oldtag['planids'])
        if olddescription in planids and id_ in planids[olddescription]:
            edittag = mm.Tag.objects.get(id=oldtag['id'])
            ol = json.loads(edittag.planids)
            ol[newdescription] = ol.pop(olddescription)
            edittag.planids = str(ol).replace("'", '"')
            edittag.save()
            logger.info(str(edittag.id) + '更新完成')

@cache_sync
@monitor(action='编辑计划')
def editplan(request):
    id_ = request.POST.get('uid').split('_')[1]
    config = request.POST.get('config')
    run_type = request.POST.get("run_type")
    newdescription = request.POST.get('description')
    msg = ''
    try:
        is_send_mail = request.POST.get("is_send_mail")
        is_send_dingding = request.POST.get("is_send_dingding")
        plan = mm.Plan.objects.get(id=id_)
        plancopy=copy.deepcopy(plan)
        olddescription = plan.description
        plan.description = newdescription
        plan.db_id = request.POST.get('dbid')
        plan.before_plan = request.POST.get('before_plan')
        plan.schemename = request.POST.get('scheme')
        logger.info('description=>', plan.description)
        plan.run_type = request.POST.get('run_type')
        plan.proxy = request.POST.get('proxy','')
        plan.save()
        extmsg=''
        if run_type == '定时运行':
            try:
                cron = mm.Crontab.objects.get(plan_id=id_)
                cron.value = config
                cron.save()
            except:
                crontab = mm.Crontab()
                crontab.value = config
                crontab.plan = plan
                crontab.status = 'close'
                crontab.save()
            extmsg = Cron.addcrontab(plan.id)
        else:
            Cron.delcrontab(plan.id)

        if plan.mail_config_id == '' or plan.mail_config_id is None:  # 针对老任务，没有邮箱配置
            mail_config = mm.MailConfig()
            if is_send_mail == 'true':
                mail_config.is_send_mail = 'open'
            else:
                mail_config.is_send_mail = 'close'
            if is_send_dingding == 'true':
                mail_config.is_send_dingding = 'open'
            else:
                mail_config.is_send_dingding = 'close'
            mail_config.save()
            plan.mail_config_id = mail_config.id
            plan.save()
        else:
            mail_config = mm.MailConfig.objects.get(id=plan.mail_config_id)
            if is_send_mail == 'true':
                mail_config.is_send_mail = 'open'
            else:
                mail_config.is_send_mail = 'close'
            if is_send_dingding == 'true':
                mail_config.is_send_dingding = 'open'
            else:
                mail_config.is_send_dingding = 'close'
            mail_config.save()
        msg = '编辑成功'


        #
        linkiter=mm.EditLink.objects.filter(snid='plan_{}'.format(plan.id))
        for link in linkiter:
            linkobj=mm.Plan.objects.get(id=link.tnid.split('_')[1])
            _update_object(linkobj, _diff_object(plancopy,plan,ignore_attr=['id']))


        
        if olddescription != newdescription:
            threading.Thread(target=handlebindplans, args=(olddescription, newdescription, id_)).start()
        
        return {
            'status': 'success',
            'msg': '编辑[%s]成功%s' % (plan.description,extmsg),
            'data': {
                'name': plan.description
            }
        }
    except:
        return {
            'status': 'error',
            'msg': "编辑异常[%s]" % traceback.format_exc()
        }


@monitor(action='运行用例')
def run(request):
    callername = request.session.get('username')
    runid = request.POST.get('ids')
    logger.info('runid:',runid)
    runkind = request.POST.get('runkind') or '2'
    planid = get_run_node_plan_id(runid)
    logger.info('获取待运行节点计划ID:',planid)
    taskid = gettaskid(planid)

    state_running =getRunningInfo(planid=planid,type='isrunning')

    if state_running != '0':
        msg = {"1":"验证","2":"调试","3":"定时"}[state_running]
        return {
            'status': 'fail',
            'msg': '计划正在运行[%s]任务，稍后再试！'%msg
        }
    logger.info('runidd:',runid)

    x = RunPlan(taskid,planid,runkind,callername,startNodeId=runid)
    threading.Thread(target=x.start).start()

    # t=threading.Thread(target=runplan,args=(callername, taskid, planid, runkind,runid))
    # t.start()
    request.session['console_taskid'] = taskid
    return {'status': 'success','msg': taskid,'data':planid}



@monitor(action='导出计划')
def export(request):
    flag = str(datetime.datetime.now()).split('.')[0]
    version = request.GET.get('version')
    logger.info('version=>', version)
    planid = request.GET.get('planid')
    m = DataMove()
    res = m.export_plan(planid, flag, version=int(version))
    print("eeeeeeeeeeeeeeeeeeeee",json.dumps(res[1],ensure_ascii=False))
    return {
        'status': res[0],
        'msg': res[1]
    }


##
@cache_sync
@monitor(action='新建用例')
def addcase(request):
    msg = ''
    try:
        ptype,pid = request.POST.get('pid').split('_')
        case = mm.Case()
        case.description = request.POST.get('description')
        case.db_id = request.POST.get('dbid')
        case.save()
        if ptype=='plan':
            addrelation('plan_case',pid, case.id)
        else:
            addrelation('case_case', pid, case.id)
        return {
            'status': 'success',
            'msg': '新增成功',
            'data': {
                'id': 'case_%s' % case.id,
                'pId': '%s_%s' %(ptype,pid),
                'name': case.description,
                'type': 'case',
                'textIcon': 'fa icon-fa-folder'
            }
            
        }
    except:
        return {
            'status': 'error',
            'msg': '新增失败[%s]' % traceback.format_exc()
        }

@cache_sync
@monitor(action='编辑用例')
def editcase(request):
    id_ = request.POST.get('uid').split('_')[1]
    msg = ''
    try:
        case = mm.Case.objects.get(id=id_)
        casecopy=copy.deepcopy(case)
        case.description = request.POST.get('description')
        case.db_id = request.POST.get('dbid')
        case.count = int(request.POST.get('count'))
        case.save()
        casename = case.description


        if case.count == 0:
            casename = '<s>%s</s>' % casename

        #
        linkiter=mm.EditLink.objects.filter(snid='case_{}'.format(case.id))
        for link in linkiter:
            linkobj=mm.Case.objects.get(id=link.tnid.split('_')[1])
            _update_object(linkobj, _diff_object(casecopy,case,ignore_attr=['id']))
        
        return {
            'status': 'success',
            'msg': '编辑成功',
            'data': {
                'name': casename
            }
        }
    except:
        return {'status': 'error', 'msg': '编辑失败[%s]' % traceback.format_exc()}

@cache_sync
@monitor(action='删除用例')
def delcase(request):
    id_ = request.POST.get('ids')
    ids = id_.split(',')
    try:
        for i in ids:
            i = i.split('_')[1]
            i = int(i)
            case = mm.Case.objects.get(id=i)
            if len(getchild('case_step', i)) or len(getchild('case_case', i)) > 0:
                return {
                    'status': 'fail',
                    'msg': '删除失败,[%s]含子数据' % case.description
                }
            
            # delrelation('plan_case',None, None,i)
            # case.delete()
            _regen_weight(request.session.get('username'), case, trigger='del')
        return {
            'status': 'success',
            'msg': '删除成功'
        }
    except:
        return {
            'status': 'error',
            'msg': "删除失败[%s]" % traceback.format_exc()
        }


##
@cache_sync
@monitor(action='新加步骤')
def addstep(request):
    from .core import getbuiltin
    try:
        pid = request.POST.get('pid').split('_')[1]
        step_type = request.POST.get('step_type')
        description = request.POST.get('description')
        headers = request.POST.get('headers')
        body = request.POST.get("body")
        url = request.POST.get('url')
        if url:
            url = url.strip()
        method = request.POST.get('method')
        content_type = request.POST.get('content_type')
        count = request.POST.get('count')
        tmp = request.POST.get('extract')
        businessdata = request.POST.get('business_data')
        logger.info('businessdata=>', type(businessdata), businessdata)
        dbid = request.POST.get('dbid')

        ##
        if step_type == 'dir':
            case = mm.Case()
            case.description = description
            case.db_id = dbid
            case.save()
            
            addrelation('case_case',pid, case.id)
            return {
                'status': 'success',
                'msg': '新建[%s]成功' % case.description,
                
                'data': {
                    'id': 'case_%s' % case.id,
                    'pId': 'case_%s' % pid,
                    'name': case.description,
                    'type': 'case',
                    'textIcon': 'fa icon-fa-folder',
                    
                }
            }
        
        step = mm.Step()
        step.step_type = step_type
        step.description = description
        step.headers = headers
        step.body = body
        step.url = url
        step.method = method
        step.content_type = content_type
        step.temp = tmp
        step.count=count
        
        step.db_id = dbid
        # step.encrypt_type=encrypt_type
        step.save()

        # mounttestdata(author,step.id)
        
        # if 'function'==step.step_type:
        #   # step.body=body
        #   funcname=step.body.strip()
        #   builtinmethods=[x.name for x in getbuiltin() ]
        #   builtin=(funcname in builtinmethods)
        
        #   if builtin is False:
        #       # flag=Fu.tzm_compute(step.body,'(.*?)\((.*?)\)')
        #       businessdatainst=None
        #       businessinfo=getchild('step_business',step.id)
        #       logger.info('vvvv=>',businessinfo,step.id)
        #       if len(businessinfo)>0:
        #           businessdatainst=businessinfo[0]
        
        #       status,res=gettestdataparams(businessdatainst.id)
        #       logger.info('gettestdataparams=>%s'%res)
        #       if status is not 'success':
        #           return (status,res)
        
        #       params=','.join(res)
        
        #       call_str='%s(%s)'%(funcname,params)
        #       flag=Fu.tzm_compute(call_str,'(.*?)\((.*?)\)')
        #       funcs=list(Function.objects.filter(flag=flag))
        #       if len(funcs)>1:
        #           return ('fail','找到多个匹配的自定义函数 请检查')
        #       related_id=funcs[0].id
        #       step.related_id=related_id
        
        addrelation('case_step', pid, step.id)
        
        return {
            'status': 'success',
            'msg': '新增测试步骤',
            'data': {
                'id': 'step_%s' % step.id,
                'pId': 'case_%s' % pid,
                'name': step.description,
                'type': 'step',
                'textIcon': 'fa icon-fa-file-o',
                
            }
        }
    except Exception as e:
        return {
            'status': 'error',
            'msg': "添加失败[%s]" % traceback.format_exc()
        }

@cache_sync
@monitor(action='编辑步骤')
def editstep(request):
    id_ = request.POST.get('uid').split('_')[1]
    try:
        count = request.POST.get('count')
        dbid = request.POST.get('dbid')

        step_type = request.POST.get('step_type')
        description = request.POST.get('description')
        headers = request.POST.get('headers')
        body = request.POST.get("body")
        url = request.POST.get('url')
        method = request.POST.get('method')
        content_type = request.POST.get('content_type')
        
        tmp = request.POST.get('extract')
        step = mm.Step.objects.get(id=id_)
        stepcopy=copy.deepcopy(step)
        if step.step_type != step_type:
            return {
                'status': 'fail',
                'msg': '编辑失败[不允许修改类型]'
            }
        
        # if step_type is None:
        #   step.step_type='function'
        
        step.count = int(count)
        step.description = description
        step.headers = headers
        step.body = body
        step.url = url
        step.method = method
        step.content_type = content_type
        step.temp = tmp
        step.db_id = dbid
        step.save()

        linkiter=mm.EditLink.objects.filter(snid='step_{}'.format(step.id))
        for link in linkiter:
            linkobj=mm.Step.objects.get(id=link.tnid.split('_')[1])
            _update_object(linkobj, _diff_object(stepcopy,step,ignore_attr=['id']))

        stepname = description
        
        logger.info('step save,count=>', count)
        if step.count == 0:
            stepname = '<s>%s</s>' % stepname
        
        # mounttestdata(username, step.id,trigger='edit')
        
        logger.info('step save,name=>', stepname)
        return {
            'status': 'success',
            'msg': '编辑成功',
            'data': {'name': stepname}
        }
    
    except Exception as e:
        logger.info(traceback.format_exc())
        return {
            'status': 'error',
            'msg': '编辑失败[%s]' % traceback.format_exc()
        }

@cache_sync
@monitor(action='删除步骤')
def delstep(request):
    id_ = request.POST.get('ids')
    ids = id_.split(',')
    try:
        for i in ids:
            i = i.split('_')[1]
            i = int(i)
            step = mm.Step.objects.get(id=i)
            businessdatainfo = getchild('step_business', i)
            if len(businessdatainfo) > 0:
                return {
                    'status': 'fail',
                    'msg': '删除失败,[%s]含子数据' % step.description
                }
            # delrelation('case_step',None, None,i)
            # step.delete()
            _regen_weight(request.session.get('username'), step, trigger='del')
        return {
            'status': 'success',
            'msg': '删除成功'
        }
    
    except Exception as e:
        return {
            'status': 'success',
            'msg': "删除失败[%s]" % traceback.format_exc()
        }


def _check_params(param_value):
    if param_value.startswith('{') and param_value.endswith('}'):
        logger.info('f1')
        try:
            eval(param_value)
            return True
        except:
            return False
    else:
        logger.info('f2')
        return True


##
@cache_sync
@monitor(action='新建测试点')
def addbusiness(request):
    from .core import getbuiltin, Fu
    bname = ''
    try:
        
        pid = request.POST.get('pid').split('_')[1]
        b = mm.BusinessData()
        b.businessname = request.POST.get('businessname')
        bname = b.businessname
        b.itf_check = request.POST.get('itf_check')
        b.db_check = request.POST.get('db_check')
        b.queryparams = request.POST.get('queryparams')
        b.params = request.POST.get('params')
        b.bodytype = request.POST.get('bodytype',"")
        b.parser_check = request.POST.get('parser_check')
        b.parser_id = request.POST.get('parser_id')
        b.description=request.POST.get('description')
        timeout=request.POST.get('timeout')
        b.timeout = timeout if timeout else 60
        # check_result=_check_params(b.params)
        # logger.info('nn=>',check_result)
        # if not check_result:
        #   return{
        #   'status':'error',
        #   'msg':'参数json格式异常，请检查！'
        #   }
        
        b.postposition = request.POST.get('postposition')
        b.preposition = request.POST.get('preposition')
        b.count = int(request.POST.get('count').strip()) if request.POST.get('count') != '' else int(1)
        if b.count == 0:
            bname = '<s>%s</s>' % bname
        
        b.save()
        addrelation('step_business',pid, b.id)
        
        ##funcion类型关联realted_id
        
        status, step = mm.BusinessData.gettestdatastep(b.id)
        if status is not 'success':
            return {
                'status': 'fail',
                'msg': '添加测试数据异常[%s]' % step
            }
        
        if 'function' == step.step_type:
            # step.body=body
            funcname = step.body.strip()
            builtinmethods = [x.name for x in getbuiltin()]
            builtin = (funcname in builtinmethods)
            
            if builtin is False:
                # flag=Fu.tzm_compute(step.body,'(.*?)\((.*?)\)')
                businessdatainst = None
                businessinfo = getchild('step_business', step.id)
                logger.info('vvvv=>', businessinfo, step.id)
                if len(businessinfo) > 0:
                    businessdatainst = businessinfo[0]
                
                status, res = mm.BusinessData.gettestdataparams(businessdatainst.id)
                logger.info('gettestdataparams=>%s' % res)
                if status is not 'success':
                    return {
                        'status': status,
                        'msg': str(res)
                    }
                
                params = ','.join(res)
                
                call_str = '%s(%s)' % (funcname, params)
                flag = Fu.tzm_compute(call_str, '(.*?)\((.*?)\)')
                funcs = list(mm.Function.objects.filter(flag=flag))
                if len(funcs) > 1:
                    return {
                        'status': 'fail',
                        'msg': '查找到多个函数请检查'
                    }
                related_id = funcs[0].id
                
                logger.info('修改step related_id=>', related_id)
                step.related_id = related_id
                step.save()
        
        return {
            'status': 'success',
            'msg': '添加[%s]成功' % b.businessname,
            'data': {
                'id': 'business_%s' % b.id,
                'pId': 'step_%s' % pid,
                'name': bname,
                'type': 'business',
                'textIcon': 'fa icon-fa-leaf',
            }
        }
    except:
        return {
            'status': 'error',
            'msg': '添加测试数据异常[%s]' % traceback.format_exc()
        }

@cache_sync
@monitor(action='编辑测试点')
def editbusiness(request):
    from .core import getbuiltin, Fu
    bname = ''
    try:
        
        b = mm.BusinessData.objects.get(id=request.POST.get('uid').split('_')[1])
        bcopy=copy.deepcopy(b)
        b.businessname = request.POST.get('businessname')
        bname = b.businessname
        b.itf_check = request.POST.get('itf_check')
        b.db_check = request.POST.get('db_check')
        b.queryparams = request.POST.get('queryparams')
        b.bodytype = request.POST.get('bodytype')
        b.params = request.POST.get('params')
        b.postposition = request.POST.get('postposition')
        b.preposition = request.POST.get('preposition')
        b.count = int(request.POST.get('count').strip()) if request.POST.get('count') != '' else int(1)
        b.parser_check = request.POST.get('file_check')
        b.parser_id = request.POST.get('parser_id')
        b.description=request.POST.get('description')
        b.timeout=request.POST.get('timeout')
        # check params
        check_result = _check_params(b.params)
        
        # if not check_result:
        #   return{
        #   'status':'error',
        #   'msg':'参数json格式异常，请检查！'
        #   }
        
        if b.count == 0:
            bname = '<s>%s</s>' % bname
        
        b.save()
        
        status, step = mm.BusinessData.gettestdatastep(b.id)
        if status is not 'success':
            return {
                'status': 'fail',
                'msg': '编辑业务数据异常[%s]' % step
            }
        
        ##重新计算related_id
        if 'function' == step.step_type:
            # funcname=re.findall("(.*?)\(.*?\)", step.body)[0]
            funcname = step.body.strip()
            builtinmethods = [x.name for x in getbuiltin()]
            builtin = (funcname in builtinmethods)
            
            if builtin is False:
                businessdatainst = None
                # businessinfo=list(step.businessdatainfo.all())
                businessinfo = getchild('step_business', step.id)
                if len(businessinfo) > 0:
                    businessdatainst = businessinfo[0]
                
                status, res = mm.BusinessData.gettestdataparams(businessdatainst.id)
                if status is not 'success':
                    return (status, res)
                
                params = ','.join(res)
                calll_str = '%s(%s)' % (step.body.strip(), params)
                flag = Fu.tzm_compute(calll_str, '(.*?)\((.*?)\)')
                funcs = list(mm.Function.objects.filter(flag=flag))
                if len(funcs) > 1:
                    return ('fail', '找到多个匹配的自定义函数 请检查')
                related_id = funcs[0].id
                step.related_id = related_id
                step.save()

        linkiter=mm.EditLink.objects.filter(snid='business_{}'.format(b.id))
        for link in linkiter:
            linkobj=mm.BusinessData.objects.get(id=link.tnid.split('_')[1])
            _update_object(linkobj, _diff_object(bcopy,b,ignore_attr=['id']))


        return {
            'status': 'success',
            'msg': '编辑成功',
            'data': {
                'name': bname
            }}
    except:
        return {
            'status': 'error',
            'msg': '编辑业务数据异常[%s]' % traceback.format_exc()
        }

@cache_sync
@monitor(action='删除测试点')
def delbusiness(request):
    try:
        
        id_ = request.POST.get('ids')
        ids = id_.split(',')
        for i in ids:
            i = int(i.split('_')[1])
            
            business = mm.BusinessData.objects.get(id=i)
            # business.delete()
            _regen_weight(request.session.get('username'), business, trigger='del')
        return {
            'status': 'success',
            'msg': '删除成功'
        }
    
    except:
        return {
            'status': 'error',
            'msg': '删除业务异常[%s]' % traceback.format_exc()
        }


@monitor(action='移动|复制节点')
def movenode(request):
    try:
        is_copy = request.POST.get('is_copy')
        movetype = request.POST.get('move_type')
        srcid = request.POST.get('src_id')
        if srcid.split('_')[0] in ['product','root']:
            return {
                'status': 'error',
                'msg': '操作失败，不允许移动'
            }
        targetid = request.POST.get('target_id')
        user = lm.User.objects.get(name=request.session.get('username'))
        # elementclass=srcid.split('_')[0]
        # elementid=srcid.split('_')[1]
        # if elementclass=='business':
        #   elementclass='businessData'
        # elementclass=_first_word_up(elementclass)
        # element=eval("%s.objects.get(id=%s)"%(elementclass,elementid))
        # _build_all(srcid, targetid, movetype, user, is_copy, user.name)
        if is_copy == 'false':
            movenode_reorder(srcid, targetid, movetype,user.name)
        elif is_copy == 'true':
            _build_all(srcid, targetid, movetype, user, is_copy, user.name)

        return {
            'status': 'success',
            'msg': '操作成功'}
    except:
        logger.info(traceback.format_exc())
        return {
            'status': 'error',
            'msg': '移动异常'
        }

def movenode_reorder(srcid, targetid, movetype,name):
    src_uid = srcid.split('_')[1]
    target_uid = targetid.split('_')[1]
    src_type = srcid.split('_')[0]
    target_type = targetid.split('_')[0]
    if movetype == 'inner':
        o = mm.Order.objects.get(follow_id=src_uid, kind__contains='_%s' % src_type,isdelete=0)
        o.main_id = target_uid
        maxv = list(mm.Order.objects.values_list('value', flat=True).filter(kind__contains='%s_'%target_type,main_id=target_uid,isdelete=0))
        li = [int(i.split(".")[1]) for i in maxv] if maxv else [0]
        o.value = '1.' + str(max(li) + 1)
        o.kind = '%s_%s'%(target_type,src_type)
        o.save()
        return
    else:
        o = mm.Order.objects.get(follow_id=src_uid, kind__contains='_%s' % src_type,isdelete=0)
        pkind , pid = _get_node_parent_info(target_type,target_uid)
        o.main_id = pid
        to = mm.Order.objects.get(Q(kind__contains='_%s' % target_type) & Q(follow_id=target_uid),isdelete=0)
        ogroup = to.value.split('.')[0]
        oindex = int(to.value.split('.')[1])
        o.value = '%s.%s' % (ogroup, oindex)
        o.kind = '%s_%s'%(pkind,src_type)
        o.save()
        src_type_upper = src_type.capitalize()
        if src_type_upper == 'Businessdata' or src_type_upper == 'Business':
            src_type_upper = 'BusinessData'
        el = eval("mm.%s.objects.get(id=%s)" % (src_type_upper, src_uid))
        _regen_weight(name,el,movetype,target_uid)






def movemulitnodes(request):
    try:
        is_copy = request.POST.get('is_copy')
        movetype = request.POST.get('move_type')
        src_ids = request.POST.get('src_ids')[:-1]
        src_ids = src_ids.split(';')
        targetid = request.POST.get('target_id')
        user = lm.User.objects.get(name=request.session.get('username'))
        logger.info('开始批量移动/复制')
        for srcid in src_ids:
            logger.info('移动/复制节点：{}，目标节点{},复制{},移动类型{}'.format(srcid,targetid,is_copy,movetype))
            _build_all(srcid, targetid, movetype, user, is_copy, user.name)
        
        return {
            'status': 'success',
            'msg': '操作成功'}
    except:
        logger.info(traceback.format_exc())
        return {
            'status': 'error',
            'msg': '移动异常'
        }





_order_value_cache = dict()


def addrelation(kind, main_id, follow_id):
    order = mm.Order()
    order.kind = kind
    order.main_id = main_id
    order.follow_id = follow_id
    order.value = getnextvalue(kind, main_id)
    order.save()


def delrelation(kind, callername, main_id, follow_id):
    # logger.info('==删除关联关系')
    # logger.info('kind=>',kind)
    # logger.info('main_id=>',main_id)
    # logger.info('follow_id=>',follow_id)
    try:
        ol = mm.Order.objects.get(kind=kind, main_id=main_id, follow_id=follow_id,isdelete=0)
        logger.info('==删除节点关联[%s]' % ol)
        # ol.delete()
        ol.isdelete=1
        ol.save()
    # length=len(ol)

    # logger.info('找到[%s]条待删除'%length)
    # for o in ol:
    #   o.delete()
    
    # if kind=='plan_case' and length==0:
    #   Order.objects.get(kind='case_case',follow_id=follow_id).delete()
    
    except:
        logger.info('==删除节点关联报错')
        logger.info(traceback.format_exc())


def get_all_child_nodes(nodeid,cur):
    '''
    获得指定节点的所有子项
    '''

    kind,nid=nodeid.split('_')[0],nodeid.split('_')[1]

    if kind=='plan':
        od=mm.Order.objects.filter(kind='plan_case',main_id=nid)
        for o in od:
            try:
                case=mm.Case.objects.get(id=o.follow_id,isdelete=0)
                cur.append({
                        'nid':'case_{}'.format(o.follow_id),
                        'name':case.description,
                        'level':'plan_case',
                    })
                get_all_child_nodes('case_{}'.format(o.follow_id), cur)
            except:
                pass

    elif kind=='case':
        od=mm.Order.objects.filter(kind='case_step',main_id=nid)
        for o in od:
            try:
                print('followid:=>',o.follow_id)
                step=mm.Step.objects.get(id=o.follow_id,isdelete=0)
                cur.append({
                        'nid':'step_{}'.format(o.follow_id),
                        'name':step.description,
                        'level':'case_step'
                    })

                get_all_child_nodes('step_{}'.format(o.follow_id), cur)
            except:
                pass

        od1=mm.Order.objects.filter(kind='case_case',main_id=nid)

        for o1 in od1:
            try:
                case=mm.Case.objects.get(id=o1.follow_id,isdelete=0)
                cur.append({
                        'nid':'case_{}'.format(o1.follow_id),
                        'name':case.description,
                        'level':'case_case'
                    })

                get_all_child_nodes('case_{}'.format(o1.follow_id), cur)
            except:
                pass


    elif kind=='step':
        od=mm.Order.objects.filter(kind='step_business',main_id=nid)
        for o in od:
            try:
                b=mm.BusinessData.objects.get(id=o.follow_id,isdelete=0)
                cur.append({
                    'nid':'business_{}'.format(b.id),
                    'name':b.businessname,
                    'level':'step_business'
                    })

                get_all_child_nodes('step_{}'.format(o.follow_id),cur)
            except:
                pass


        

# logger.info('删除完毕')
def getchild(kind, main_id):
    '''
    返回有序子项
    '''
    child = []
    orderlist = ordered(list(mm.Order.objects.filter(kind=kind, main_id=main_id,isdelete=0)))
    if kind == 'product_plan':
        for order in orderlist:
            # logger.info('planid=>', order.follow_id)
            try:
                # logger.info('plan class=>', mm.Plan)
                p = mm.Plan.objects.get(id=order.follow_id)
                # logger.infoe('添加计划=>',plan)
                child.append(p)
            # pirnt('child=>',child)
            except:
                logme.warn('找不到计划 ID=%s'%order.follow_id)
                #logger.info(traceback.format_exc())
    elif kind == 'plan_case':
        for order in orderlist:
            #logger.info('case class=>', mm.Case)
            print('hid:',order.follow_id)
            try:
                child.append(mm.Case.objects.get(id=order.follow_id))
            except:
                pass
    elif kind == 'case_step':
        for order in orderlist:
            #logger.info('main=>%s follow=>%s v=%s' % (order.main_id, order.follow_id, order.value))
            
            child.append(mm.Step.objects.get(id=order.follow_id))
    elif kind == 'step_business':
        for order in orderlist:
            child.append(mm.BusinessData.objects.get(id=order.follow_id))
    elif kind == 'case_case':
        for order in orderlist:
            child.append(mm.Case.objects.get(id=order.follow_id))
    
    else:
        orderlist = list(mm.Order.objects.filter(Q(main_id=main_id) & Q(kind__contains=kind,isdelete=0)))
        for order in orderlist:
            kind = order.kind
            ctype = kind.split('_')[1]
            # logger.info('old ctype=>',ctype)
            if ctype in ('business', 'businessdata'):
                ctype = "BusinessData"
            else:
                ctype = ctype[0].upper() + ctype[1:]
            
            # logger.info('last ctype=>',ctype)
            
            child.append(eval('mm.%s.objects.get(id=%s)' % (ctype, order.follow_id)))
    
    # logger.info('ck=>',child)
    return child


def ordered(iterator, key='value', time_asc=True):
    """
    执行列表根据value从小到大排序
    """
    try:
        for i in range(len(iterator) - 1):
            for j in range(i + 1, len(iterator)):
                groupa = int(str(getattr(iterator[i], key)).split(".")[0])
                groupb = int(str(getattr(iterator[j], key)).split(".")[0])
                if groupa > groupb:
                    tmp = iterator[i]
                    iterator[i] = iterator[j]
                    iterator[j] = tmp
                
                elif groupa == groupb:
                    indexa = int(getattr(iterator[i], key).split(".")[1])
                    indexb = int(getattr(iterator[j], key).split(".")[1])
                    if indexa > indexb:
                        tmp = iterator[i]
                        iterator[i] = iterator[j]
                        iterator[j] = tmp
                    
                    elif indexb == indexa:
                        timea = getattr(iterator[i], 'updatetime')
                        timeb = getattr(iterator[j], 'updatetime')
                        
                        if time_asc == True:
                            if timea > timeb:
                                iterator[i], iterator[j] = iterator[j], iterator[i]
                        
                        elif time_asc == False:
                            if timea < timeb:
                                iterator[i], iterator[j] = iterator[j], iterator[i]
    
    except:
        logger.info(traceback.format_exc())
    finally:
        return iterator


def _regen_weight_force(parent_type, parent_id, ignore_id=None):
    '''
    重排父级权重
    '''
    logger.info('==强制删除后兄弟节点权重调整')
    try:
        kind = ''
        ol = ordered(list(mm.Order.objects.filter(Q(kind__contains='%s_' % parent_type) & Q(main_id=parent_id),isdelete=0)))
        mx = len(ol)
        cur = 0
        for idx in range(1, mx + 1):
            
            if str(ol[idx - 1].follow_id) == str(ignore_id):
                pass
            else:
                cur = cur + 1
                
                ol[idx - 1].value = '1.%s' % cur
                ol[idx - 1].save()
    except:
        logger.info('强制删除后兄弟节点权重调整异常=>', traceback.format_exc())


def _regen_weight(callername, element, trigger='prev', target_id=None):
    '''
    删除移动复制节点重新生成权重 事件节点的order除外 保持分组(flag)
    '''
    ##删除事件节点引用
    if trigger == 'del':
        c = element.__class__.__name__.lower()
        if c == 'businessdata':
            c = 'business'
        order = mm.Order.objects.get(Q(kind__contains='_%s' % c) & Q(follow_id=element.id),isdelete=0)
        parentid = order.main_id
        group = order.value.split('.')[0]
        parentkind = order.kind.split('_')[0]
        text = '%s_' % parentkind
        
        delrelation(order.kind, callername, parentid, element.id)
        
        # logger.info('==删除节点[%s]' % element)
        # element.delete()
        element.isdelete=1
        element.save()
        logger.info('==删除后重新生成权重')
        orderlist = ordered(list(mm.Order.objects.filter(Q(kind__contains=text) & Q(main_id=parentid),isdelete=0)))
        
        index = 0
        for order in orderlist:
            old = order
            index = index + 1
            curgroup = order.kind.split('.')[0]
            if curgroup != group:
                continue
            
            weight = '%s.%s' % (group, index)
            order.value = weight
            order.save()
            logger.info('[%s]=>[%s]' % (old, order))
        
        logger.info('生成后=>', orderlist)
    
    else:
        c = element.__class__.__name__.lower()
        if c == 'businessdata':
            c = 'business'
        order = mm.Order.objects.get(Q(kind__contains='_%s' % c) & Q(follow_id=element.id),isdelete=0)
        parentid = order.main_id
        group = order.value.split('.')[0]
        parentkind = order.kind.split('_')[0]
        text = '%s_' % parentkind
        # logger.info('text=%s main_id=%s'%(text,parentid))
        orderlist = ordered(list(mm.Order.objects.filter(Q(kind__contains=text) & Q(main_id=parentid),isdelete=0)))
        
        if trigger == 'prev':
            orderlist = ordered(orderlist, time_asc=False)
        elif trigger == 'next':
            orderlist = ordered(orderlist, time_asc=True)
        elif trigger == 'inner':
            # 最后一个不用在处理
            pass
        
        logger.info('===[%s]操作 根据时间处理再排序=>%s' % (trigger, orderlist))
        
        ##重新生成序号 只处理同组号的数据
        logger.info('==兄弟节点重新生成权重')
        
        index = 0
        for order in orderlist:
            old = order
            index = index + 1
            curgroup = order.value.split('.')[0]
            
            logger.info('==拖动组号=>%s 兄弟节点组号=>%s 相等=>%s' % (group, curgroup, group == curgroup))
            if curgroup != group:
                continue
            
            weight = '%s.%s' % (group, index)
            order.value = weight
            order.save()
            logger.info('[%s]=>[%s]' % (old, order))
        
        logger.info('生成后=>', orderlist)


def _resort_by_create_when_equal(orderlist, asc=True):
    for i in range(len(orderlist) - 1):
        for j in range(i + 1, len(orderlist)):
            if orderlist[j] == orderlist[i]:
                if asc:
                    if getattr(orderlist[i], 'updatetime') > getattr(orderlist[j], 'updatetime'):
                        orderlist[i], orderlist[j] = orderlist[j], orderlist[i]
                
                else:
                    if getattr(orderlist[i], 'updatetime') < getattr(orderlist[j], 'updatetime'):
                        orderlist[i], orderlist[j] = orderlist[j], orderlist[i]
    
    return orderlist


def getnextvalue(kind, main_id, flag=0):
    max_value = 0
    orderlist = []
    if kind in ('case_case', 'case_step'):
        orderlist = list(mm.Order.objects.filter(kind='case_case', main_id=main_id,isdelete=0)) + list(
            mm.Order.objects.filter(kind='case_step', main_id=main_id,isdelete=0))
    else:
        orderlist = list(mm.Order.objects.filter(kind=kind, main_id=main_id,isdelete=0))
    # logger.info('list=>',orderlist)
    
    if len(orderlist) == 0:
        return '1.1'
    else:
        lastvalue = ordered(orderlist)[-1].value
        group = lastvalue.split('.')[0]
        index = lastvalue.split('.')[1]
        newvalue = '%s.%s' % (group, int(index) + 1)
        return newvalue


def _get_delete_node(src_uid, src_type, iscopy, del_nodes):
    # logger.info('iscopy=>',iscopy)
    if iscopy == 'true':
        logger.info('==复制操作 略过添加待删除源数据')
    else:
        logger.info('==计算待删除源数据==')
        del_nodes.append((src_type, str(src_uid)))
        parent_type, parent_id = _get_node_parent_info(src_type, src_uid)
        
        # kind='%s_%s'%(parent_type,src_type)
        
        # logger.info('k1=>',kind)
        childs = getchild('%s_' % src_type, src_uid)  ##??
        # logger.info('childs=>',childs)
        for child in childs:
            child_type = child.__class__.__name__.lower()
            _get_delete_node(child.id, child_type, False, del_nodes)


def _sort_by_weight(childs):
    result = list()
    _m = {}
    _len = len(childs)
    
    if _len == 1:
        return childs
    
    elif _len > 1:
        for c in childs:
            node_type = c.__class__.__name__.lower()
            if node_type == 'businessdata':
                node_type = 'business'
            
            descp = ''
            try:
                desp = c.description
            except:
                desp = c.businessname
            logger.info('desp=>', descp)
            parent_type, parent_id = _get_node_parent_info(node_type, c.id)
            
            # if parent_id==-1:
            #   return childs
            
            logger.info('p=>', node_type, c.id)
            logger.info('res=>', parent_type, parent_id)
            kind = '%s_%s' % (parent_type, node_type)
            logger.info('o info=>%s %s %s' % (kind, parent_id, c.id))
            ov = mm.Order.objects.get(kind=kind, main_id=parent_id, follow_id=c.id,isdelete=0).value
            _m[str(ov)] = c
        ###
        akeys = [int(k.replace('1.', '')) for k in _m.keys()]
        bkeys = sorted(akeys)
        ckeys = ['1.' + str(k) for k in bkeys]
        
        for key in ckeys:
            result.append(_m.get(str(key)))
        
        return result
    
    else:
        return []


def _build_node(kind, src_uid, target_uid, move_type, user, build_nodes):
    target_type = kind.split('_')[0]
    target_type_upper = target_type[0].upper() + target_type[1:]
    if target_type_upper == 'Business':
        target_type_upper = 'BusinessData'
    
    src_type = kind.split('_')[1]
    # logger.info('src_type=>',src_type)
    src_type_upper = src_type[0].upper() + src_type[1:]
    if src_type_upper == 'Businessdata' or src_type_upper == 'Business':
        src_type_upper = 'BusinessData'
    
    ##构造target数据(重新生成)
    logger.info('==构建新节点实体数据')
    if kind in ('step_businessdata'):
        kind = 'step_business'
    logger.info(src_type_upper, '=>', src_uid)
    src = eval("mm.%s.objects.get(id=%s)" % (src_type_upper, src_uid))
    # logger.info('老id=>',src.id)
    src.id = None
    src.save()
    logger.info('构建完成[%s]' % src)
    build_nodes.append(src)
    # logger.info('新id=>',src.id)
    
    ##构造target关联
    logger.info('==构建新节点关联关联==')
    # logger.info(move_type)
    # logger.info('kind=>',kind)
    # logger.info('%s->%s'%(target_uid,src.id))
    
    if move_type == 'inner':
        order = mm.Order()
        order.kind = kind
        order.main_id = target_uid
        order.follow_id = src.id
        order.value = getnextvalue(kind, target_uid)
        logger.info('inner 构建完成[%s]' % order)
        order.save()
    else:
        kindlike = '%s_' % target_type
        
        logger.info('kindlike=>', kindlike)  ##error
        logger.info('targetid=>', target_uid)
        
        parent_order = mm.Order.objects.get(Q(kind__contains=kindlike) & Q(follow_id=target_uid),isdelete=0)
        parent_type = parent_order.kind.split('_')[0]
        ##不可能为business
        parent_type_upper = parent_type.split('_')[0][0].upper() + parent_type.split('_')[0][1:]
        parent = eval("mm.%s.objects.get(id=%s)" % (parent_type_upper, parent_order.main_id))
        
        order = mm.Order()
        order.kind = '%s_%s' % (parent_type, src_type)  ###?
        order.main_id = parent.id
        order.follow_id = src.id
        
        o = mm.Order.objects.get(Q(kind__contains='%s_' % target_type) & Q(follow_id=target_uid),isdelete=0)
        if len(build_nodes) == 1 and move_type == 'prev':
            ogroup = o.value.split('.')[0]
            oindex = int(o.value.split('.')[1])
            order.value = '%s.%s' % (ogroup, oindex)
        elif len(build_nodes) == 1 and move_type == 'next':
            ogroup = o.value.split('.')[0]
            oindex = int(o.value.split('.')[1])
            order.value = '%s.%s' % (ogroup, oindex)
        
        else:
            order.value = getnextvalue(kind, target_uid)
        
        logger.info('%s 构建完成[%s]' % (move_type, order))
        
        order.save()
    
    ##子节点存在情况
    # parent_type,parent_id=_get_node_parent_info(src_type,src_uid)
    # k2='%s_%s'%('',src_type)
    # logger.info('k2=>',k2)
    childs = getchild('%s_' % src_type, src_uid)  ##???
    # logger.info('==兄弟节点排序=>',childs)
    childs = _sort_by_weight(childs)
    # logger.info('排序结果=>',childs)
    
    # if child_type=='businessdata':
    #   continue;
    
    if len(childs) > 0:
        logger.info('==构建新节点下子节点数据')
    for child in childs:
        child_type = child.__class__.__name__.lower()  ###?
        src_type = src.__class__.__name__.lower()
        
        _build_node('%s_%s' % (src_type, child_type), child.id, src.id, 'inner', user, build_nodes)


def _build_all(src_id, target_id, move_type, user, is_copy, callername):
    logger.info('==开始构建目标位置所有节点==')
    src_uid = src_id.split('_')[1]
    target_uid = target_id.split('_')[1]
    src_type = src_id.split('_')[0]
    target_type = target_id.split('_')[0]
    kind = '%s_%s' % (target_type, src_type)
    
    ###获取事件节点model对象
    elementclass = src_id.split('_')[0]
    elementid = src_id.split('_')[1]
    if elementclass == 'business':
        elementclass = 'businessData'
    elementclass = _first_word_up(elementclass)
    element = eval("mm.%s.objects.get(id=%s)" % (elementclass, elementid))
    ##
    if move_type != 'inner':
        logger.info('targetid=>', target_uid)
        # order=Order.objects.get(follow_id=target_uid)
        # parenttype=order.kind.split('_')[0]
        # kind='%s_%s'%(parenttype,src_type)
        parent_type, parent_id = _get_node_parent_info(src_type, src_uid)
        kind = '%s_%s' % (parent_type, src_type)
    
    build_nodes = []
    _build_node(kind, src_uid, target_uid, move_type, user, build_nodes)
    
    logger.info('--构建目标位置所有节点结束')
    del_nodes = []
    _get_delete_node(src_uid, src_type, is_copy, del_nodes)
    # 移动目标区域兄弟节点需重新生成权重
    logger.info('==获取移动复制构造的第一个model对象=>', build_nodes[0])
    ##处理源数据
    logger.info('==获取拖动源待处理节点列表=>', del_nodes)
    for t in del_nodes:
        tclass = _first_word_up(t[0])
        if tclass in ('Business', 'Businessdata'):
            tclass = 'BusinessData'
        el = eval("mm.%s.objects.get(id=%s)" % (tclass, t[1]))
        _regen_weight(callername, el, trigger='del', target_id=target_id)
    logger.info('--拖动源处理结束')
    #
    logger.info('==处理拖动目标位置的排序显示')
    _regen_weight(callername, build_nodes[0], trigger=move_type, target_id=target_id)


def _resort(orderlist, movetype, src_uid, target_uid):
    indexa = None
    indexb = None
    a = None
    b = None
    cindex = None
    
    target_uid = target_uid.split('.')[1]
    i = 0
    for order in orderlist:
        if order.follow_id == src_uid:
            indexa = i
        
        if order.follow_id == target_uid:
            indexb = i
        i = i + 1
    
    a = orderlist.pop(indexa)
    l = abs(indexb - indexa)
    
    if movetype == 'prev':
        orderlist.insert(indexb - 1, a)
    elif movetype == 'next':
        orderlist.insert(indexb + 1, a)
    
    return orderlist
def get_search_match(searchvalue):
    '''1.匹配的是父节点
       2.匹配的是子节点
       3.无匹配结果
    '''
    root={'id': -1, 'name': '产品线', 'type': 'root', 'textIcon': 'fa fa-pinterest-p', 'open': True}
    match_nodes=[]
    plans=mm.Plan.objects.exclude(isdelete=1).values()
    cases=mm.Case.objects.exclude(isdelete=1).values()
    steps=mm.Step.objects.exclude(isdelete=1).values()
    businesses=mm.BusinessData.objects.values()
    for x in plans:
        if x.get('description').__contains__(searchvalue):
            x['type']='plan'
            match_nodes.append(x)
    for x in cases:
        if x.get('description').__contains__(searchvalue):
            x['type']='case'
            match_nodes.append(x)
    for x in steps:
        if x.get('description').__contains__(searchvalue):
            x['type']='step'
            match_nodes.append(x)
    for x in businesses:
        if x.get('businessname').__contains__(searchvalue):
            x['type']='business'
            match_nodes.append(x)
    ##

    show_nodes=[root]
    for product in mm.Product.objects.all():
        show_nodes.append({
            'id': 'product_%s' % product.id,
            'pId': -1,
            'name': product.description,
            'type': 'product',
            'textIcon': 'fa icon-fa-home'
        })

    logger.info('match nodes:',match_nodes)
    exclude=set()
    pkg=[]

    for m in match_nodes:
        _get_node_parent_route_chain(m['type'], m['id'], pkg, exclude)

    if pkg:
        for x in show_nodes:
            x['open']=True
    show_nodes.extend(pkg)

    logger.info('前端返回node:',show_nodes)
    return show_nodes


def get_link_left_tree(nid):
    logger.info('开始计算左侧数据')
    #wait_del=_get_all_child_node_id(nid)#查询时间过大如果nid子节点复杂
    wait_del=[]
    datanode=[]
    history=mm.EditLink.objects.filter(snid=nid)

    parent_product_id=mm.Order.objects.get(kind='product_plan',follow_id=nid.split('_')[1]).main_id
    product_name=mm.Product.objects.get(id=parent_product_id).description
    logger.info('productname:{}'.format(product_name))
    if history.exists():
        logger.info('有历史数据')
        datanode.append({'id': -1, 'name': '产品池', 'type': 'root', 'textIcon': 'fa fa-pinterest-p33', 'open': True,'checked':True})
        productlist = list(mm.Product.objects.exclude(isdelete=1))
        for product in productlist:
            if str(product.id)==str(parent_product_id):
                #mm.Product.objects.get(id=parent_product_id).description
                datanode.append({
                    'id': 'product_%s' % product.id,
                    'pId': -1,
                    'name': product.description,
                    'type': 'product',
                    'textIcon': 'fa icon-fa-home'
                })
                datanode[-1]['checked']=True

    else:
        logger.info('无历史数据')
        datanode.append({'id': -1, 'name': '产品池', 'type': 'root', 'textIcon': 'fa fa-pinterest-p33', 'open': True})
        productlist = list(mm.Product.objects.exclude(isdelete=1))
        # logger.info('productlist:',productlist)
        for product in productlist:
            if str(product.id) == str(parent_product_id):
                datanode.append({
                    'id': 'product_%s' % product.id,
                    'pId': -1,
                    'name': product.description,
                    'type': 'product',
                    'textIcon': 'fa icon-fa-home'
                })

    return datanode


def set_node_checkflag(node,checkflag,nodes):
    for node in nodes:
        pass


def get_link_right_tree(nid):
    logger.info('开始计算右侧数据')
    #wait_del=_get_all_child_node_id(nid)#查询时间过大如果nid子节点复杂
    wait_del=[]
    datanode=[]
    history=mm.EditLink.objects.filter(snid=nid)

    parent_product_id=mm.Order.objects.get(kind='product_plan',follow_id=nid.split('_')[1]).main_id
    parent_product_right_ids=[x.tnid for x in mm.EditLink.objects.filter(snid='product_{}'.format(parent_product_id))]
    logger.info('right ids:{}'.format(parent_product_right_ids))
    if history.exists():
        logger.info('有历史数据')
        datanode.append({'id': -1, 'name': '产品池', 'type': 'root', 'textIcon': 'fa fa-pinterest-p33', 'open': True,'checked':True})
        productlist = list(mm.Product.objects.exclude(isdelete=1))
        # logger.info('productlist:',productlist)
        for product in productlist:
            datanode.append({
                'id': 'product_%s' % product.id,
                'pId': -1,
                'name': product.description,
                'type': 'product',
                'textIcon': 'fa icon-fa-home'
            })
            if 'product_{}'.format(product.id) in parent_product_right_ids:
                datanode[-1]['checked']=True

    else:
        logger.info('无历史数据')
        datanode.append({'id': -1, 'name': '产品池', 'type': 'root', 'textIcon': 'fa fa-pinterest-p33', 'open': True})
        productlist = list(mm.Product.objects.exclude(isdelete=1))
        # logger.info('productlist:',productlist)
        for product in productlist:
            datanode.append({
                'id': 'product_%s' % product.id,
                'pId': -1,
                'name': product.description,
                'type': 'product',
                'textIcon': 'fa icon-fa-home'
            })

    return datanode

icon_map = {
    'product': 'fa icon-fa-home',
    'plan': 'fa icon-fa-product-hunt',
    'case': 'fa icon-fa-folder',
    'step': 'fa icon-fa-file-o',
    'business': 'fa icon-fa-leaf'
}

def _get_model_obj(node_type,node_id):
    node_class=node_type.capitalize()
    node_class='BusinessData' if node_class=='Business' else node_class
    obj=eval('mm.{}.objects.filter(id={})'.format(node_class,node_id))

    return obj[0] if obj.exists() else None

def _get_node_parent_route_chain(node_type,node_id,set_=None,exclude=None,open=False):
    if node_type is None:return
    o=_get_model_obj(node_type,node_id)
    logger.info('获取model对象:',o)
    if o is None:
        return

    kind,pid=_get_node_parent_info(node_type, node_id)
    if kind is None:
        return
    logger.info('父节点:{} {}'.format(kind,pid))
    if kind=='root':
        return ;

    id_='{}_{}'.format(node_type,node_id)
    icon_text=icon_map.get(node_type)
    logger.info('icon_text=>',icon_text)
    if id_ not in exclude:

        set_.append({
            'textIcon': icon_text,
            'type': node_type,
            'id': id_,
            'pId':'{}_{}'.format(kind,pid),
            'open':open,
            'name': getattr(o,'description') or getattr(o,'businessname')
        })

        exclude.add(id_)
    _get_node_parent_route_chain(kind,pid,set_,exclude,open=True)



def _get_all_case_child_id(casenodeid,all_):
    caseid=casenodeid.split('_')[1]
    all_.append(caseid)
    cases=getchild('case_case', caseid)
    for case in cases:
        all_.append(case.id)
        _get_all_case_child_id('case_{}'.fomat(case.id), all_)


# def get_full_tree():
#     logger.info('[获取所有树节点数据]start')
#     starttime=time.time()
#     nodes = []
#     root = {'id': -1, 'name': '产品线', 'type': 'root', 'textIcon': 'fa fa-pinterest-p', 'open': True}
#     # products = list(mm.Product.objects.all())
#     query_product_sql = 'select description,author_id,id from manager_product where isdelete=0'
#     with connection.cursor() as cursor:
#         cursor.execute(query_product_sql)
#         products = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
#     # logger.info('products=>',products)
#     for product in products:
#         productname = product['description']
#         productobj = {
#             'id': 'product_%s' % product['id'],
#             'pId': -1,
#             'name': productname,
#             'type': 'product',
#             'textIcon': icon_map.get('product')
#         }
#
#         nodes.append(productobj)
#         # plan_order_list = list(mm.Order.objects.filter(kind='product_plan', main_id=product['id']))
#
#         query_plan_order_list = "select * from manager_order where kind='product_plan' and main_id=%s and isdelete=0"
#         with connection.cursor() as cursor:
#             cursor.execute(query_plan_order_list, [product['id']])
#             plan_order_list = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
#
#         # logger.info('$' * 200)
#         logger.info('plan_order_list=>', plan_order_list, len(plan_order_list))
#         for order in plan_order_list:
#             try:
#                 # plan = mm.Plan.objects.get(id=int(order.follow_id))
#                 query_plan_sql = 'select * from manager_plan where id=%s and isdelete=0'
#                 with connection.cursor() as cursor:
#                     cursor.execute(query_plan_sql, [order['follow_id']])
#                     plan = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()][0]
#
#                 planname = plan['description']
#                 planobj = {
#                     'id': 'plan_%s' % plan['id'],
#                     'pId': 'product_%s' % product['id'],
#                     'name': planname,
#                     'type': 'plan',
#                     'textIcon': icon_map.get('plan')
#                 }
#
#                 nodes.append(planobj)
#             except:
#                 # logger.info('异常查询 planid=>', order['follow_id'])
#                 continue;
#
#             # case_order_list = ordered(list(mm.Order.objects.filter(kind='plan_case', main_id=plan['id'])))
#
#             query_case_order_list_sql = "select * from manager_order where kind='plan_case' and main_id=%s and isdelete=0"
#             with connection.cursor() as cursor:
#                 cursor.execute(query_case_order_list_sql, [plan['id']])
#                 case_order_list = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
#                 case_order_list.sort(key=lambda e: e.get('value'))
#
#             # logger.info('case_order_list=>', case_order_list, len(case_order_list))
#             tasks = []
#             e = ThreadPoolExecutor()
#             for order in case_order_list:
#                 # case = mm.Case.objects.get(id=order.follow_id)
#                 query_case_sql = 'select * from manager_case where id=%s and isdelete=0'
#                 with connection.cursor() as cursor:
#                     cursor.execute(query_case_sql, [order['follow_id']])
#                     caselist = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
#                 if len(caselist) > 0:
#                     case = caselist[0]
#                     casename = case['description']
#                     caseobj = {
#                         'id': 'case_%s' % case['id'],
#                         'pId': 'plan_%s' % plan['id'],
#                         'name': case['description'],
#                         'type': 'case',
#                         'textIcon': icon_map.get('case')
#                     }
#                     nodes.append(caseobj)
#
#                 tasks.append(e.submit(_add_next_case_node,plan,case,nodes))
#             wait(tasks)
#
#     nodes.append(root)
#
#     logger.info('[获取所有树节点]结束 spend：{}s'.format(time.time()-starttime))
#     return nodes


def _add_next_case_node(parent, case, nodes):
    ##处理所属单节点
    logger.info('size:',len(nodes))
    # step_order_list = ordered(list(mm.Order.objects.filter(kind='case_step', main_id=case['id'])))
    step_order_list=[]
    query_step_order_sql = 'select * from manager_order where kind=%s and main_id=%s and isdelete=0'
    with connection.cursor() as cursor:
        #logger.info("[执行sql]select * from manager_order where kind='case_step' and main_id={} and isdelete=0{}".format(case['id']))
        cursor.execute(query_step_order_sql, ['case_step', case['id']])
        step_order_list = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
        step_order_list.sort(key=lambda e: e.get('value'))

        # logger.info('step_order_list:{}'.format(step_order_list))
    
    for order in step_order_list:
        # logger.info('stepid=>', order['follow_id'])
        # step = mm.Step.objects.get(id=order['follow_id'])
        query_step_sql = 'select * from manager_step where id=%s and isdelete=0'
        with connection.cursor() as cursor:
            cursor.execute(query_step_sql, [order['follow_id']])
            steplist = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
        
        # logger.info('#'*200)
        # logger.info('steplist=>',len(steplist))
        if len(steplist) > 0:
            step = steplist[0]
            nodes.append({
                'id': 'step_%s' % step['id'],
                'pId': 'case_%s' % case['id'],
                'name': step['description'],
                'type': 'step',
                'textIcon': icon_map.get('step')
            })
        
        # business_order_list = ordered(list(mm.Order.objects.filter(kind='step_business', main_id=step['id'])))
        query_business_order_list_sql = "select * from manager_order where kind='step_business' and main_id=%s and isdelete=0"
        with connection.cursor() as cursor:

            # logger.info('here id:',step['id'])
            cursor.execute(query_business_order_list_sql, [step['id']])

            # logger.info('fetchall size:',len(cursor.fetchall()))
            # logger.info(list(dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()))
            business_order_list = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
            # logger.info('*'*200,'开始计算nussi大小  business:  size:',len(business_order_list))
            business_order_list.sort(key=lambda e: e.get('value'))
        
        # logger.info('*'*200,'开始计算添加  business:  size:',len(business_order_list))
        for order in business_order_list:
            # business = mm.BusinessData.objects.get(id=order.follow_id)
            query_business_sql = 'select * from manager_businessdata where id=%s and isdelete=0'
            
            with connection.cursor() as cursor:
                cursor.execute(query_business_sql, [order['follow_id']])
                businesslist = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
            
            if len(businesslist) > 0:
                business = businesslist[0]
                nodes.append({
                    'id': 'business_%s' % business['id'],
                    'pId': 'step_%s' % step['id'],
                    'name': business['businessname'],
                    'type': 'business',
                    'textIcon': icon_map.get('business')
                })
    
    ##处理多级节点
    # case_order_list = ordered(list(mm.Order.objects.filter(kind='case_case', main_id=case['id'])))
    query_case_order_list_sql = "select * from manager_order where kind='case_case' and main_id=%s and isdelete=0"
    with connection.cursor() as cursor:
        cursor.execute(query_case_order_list_sql, [case['id']])
        case_order_list = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
        case_order_list.sort(key=lambda e: e.get('value'))
    for order in case_order_list:
        # case0 = mm.Case.objects.get(id=order.follow_id)
        query_case_sql = 'select * from manager_case where id=%s and isdelete=0'
        with connection.cursor() as cursor:
            cursor.execute(query_case_sql, [order['follow_id']])
            case0 = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()][0]
        
        nodes.append({
            'id': 'case_%s' % case0['id'],
            'pId': 'case_%s' % case['id'],
            'name': case0['description'],
            'type': 'case',
            'textIcon': icon_map.get('case')
        })
        
        _add_next_case_node(case, case0, nodes)


def _expand_parent(node, node_set):
    for c in node_set:
        if node.get('pId') == c.get('id'):
            c['open'] = True
            _expand_parent(c, node_set)


def _first_word_up(text):
    if len(text) == 1:
        return text.upper()
    elif len(text) > 1:
        return text[0].upper() + text[1:]
    else:
        return ''


def weight_decorate(kind, followid):
    final = ''
    weight = '-9999'
    text = ''
    t = kind.split('_')[1][0].upper() + kind.split('_')[1][1:]
    desp = 'description'
    if t == 'Business':
        t = 'BusinessData'
        desp = 'businessname'
    text = eval('mm.%s.objects.get(id=%s).%s' % (t, followid, desp))
    logger.info('kin=>', kind)
    logger.info('fl=>', followid)
    weight = mm.Order.objects.get(kind=kind, follow_id=followid,isdelete=0).value
    # final=weight+' ' +text
    final = text
    return final


def _status_decorate(decoratename, text):
    if decoratename == 'error':
        text = "<span class='error'>%s</span>" % text
    
    elif decoratename == 'fail':
        text = "<span class='fail'>%s</span>" % text
    
    elif decoratename == 'success':
        text = "<span class='success'>%s</span>" % text
    
    elif decoratename == 'skip':
        text = "<span class='skip'>%s</span>" % text
    
    elif decoratename == 'disabled':
        text = "<s>%s</s>" % text
    
    elif decoratename == 'high_light':
        text = "<span style='background-color:#FFFF00'>%s</span>" % text
    
    return text


def del_node_force(request):
    '''强制递归删除节点
    '''
    
    logger.info('=强制del_node_force删除数据')
    id_ = request.POST.get('ids')
    ids = id_.split(',')
    for i in ids:
        node_type = i.split('_')[0]
        idx = i.split('_')[1]
        
        # logger.info('node_type=>',node_type)
        # logger.info('idx=>',idx)
        
        ##重排序
        parent_type, parent_id = _get_node_parent_info(node_type, idx)
        
        _regen_weight_force(parent_type, parent_id, ignore_id=idx)
        
        #
        
        if node_type == 'product':
            _del_product_force(idx)
        
        elif node_type == 'plan':
            Cron.delcrontab(idx)
            _del_plan_force(idx)
        elif node_type == 'case':
            up = _get_case_parent_info(idx)[0]
            _del_case_force(idx, up='%s_case' % up)
        elif node_type == 'step':
            _del_step_force(idx)
    
    return {
        'status': 'success',
        'msg': '删除成功.'
    }


def _get_node_parent_info(node_type, node_id):
    logger.info('[查询节点父节点信息]id={}'.format(node_id))
    if node_type == 'case':
        return _get_case_parent_info(node_id)
    elif node_type == 'product':
        return ('root', -1)
    else:
        if node_type in ('businessdata'):
            node_type = 'business'
        kindlike = '_%s' % node_type
        ptype,pid=None,None
        try:
            o = mm.Order.objects.get(Q(kind__contains=kindlike) & Q(follow_id=node_id),isdelete=0)
            ptype,pid=o.kind.split('_')[0], o.main_id
            logger.info('[查到父节点信息]ptype={} pid={}'.format(ptype,pid))
            return (ptype,pid)
        except:
            return (None,None)



def _get_case_parent_info(case_id):
    # logger.info('del case id=>',case_id)
    case_desp = mm.Case.objects.get(id=case_id).description
    o=None
    try:
        o = mm.Order.objects.filter(Q(kind__contains='_case') & Q(follow_id=case_id),isdelete=0)[0]
        kind = o.kind.split('_')[0]
        logger.info('获得文件夹[%s]上层节点类型=>%s'%(case_desp,kind))
        return (kind, o.main_id)
    except:
        return (None,None)



def _del_product_force(product_id):
    try:
        product = mm.Product.objects.get(id=product_id)
        product_order_list = list(mm.Order.objects.filter(kind='product_plan', main_id=product_id,isdelete=0))
        
        for o in product_order_list:
            # o.delete()
            _del_plan_force(o.follow_id)
        
        product.isdelete=1
        product.save()
    except:
        logger.info(traceback.format_exc())


def _del_plan_force(plan_id):
    # 取消上层依赖
    try:
        o = mm.Order.objects.get(kind='product_plan', follow_id=plan_id,isdelete=0)
        o.isdelete=1
        o.save()
    except:
        logger.info('取消上层依赖异常.')
    try:
        plan = mm.Plan.objects.get(id=plan_id)
        plan_order_list = list(mm.Order.objects.filter(kind='plan_case', main_id=plan_id,isdelete=0))
        plan.isdelete=1
        plan.save()
        if len(plan_order_list) > 0:
            for o in plan_order_list:
                # o.delete()
                _del_case_force(o.follow_id, up='plan_case')
        

    except:
        logger.info(traceback.format_exc())


def _del_case_force(case_id, up='plan_case'):
    # 取消上层依赖
    try:
        o = mm.Order.objects.get(kind=up, follow_id=case_id,isdelete=0)
        o.isdelete=1
        o.save()
    except:
        logger.info('取消上层依赖异常.case_id=%s type=%s' % (case_id, up))
    
    case = mm.Case.objects.get(id=case_id)
    case.isdelete=1
    case.save()
    case_order_list = list(mm.Order.objects.filter(kind='case_step', main_id=case_id,isdelete=0))
    case_order_list_2 = list(mm.Order.objects.filter(kind='case_case', main_id=case_id,isdelete=0))
    
    ##处理case->step
    for o in case_order_list:
        # o.delete()
        # Step.objects.get(id=o.follow_id).delete()
        _del_step_force(o.follow_id)
    
    # 处理case->case
    for o in case_order_list_2:
        c = mm.Case.objects.get(id=o.follow_id)
        _del_case_force(c.id, up='case_case')
    # c.delete()
    # o.delete()
    #



def _del_step_force(step_id):
    # 取消上层依赖
    try:
        ord = mm.Order.objects.get(kind='case_step', follow_id=step_id,isdelete=0)
        ord.isdelete=1
        ord.save()
    except:
        logger.info('取消上层依赖异常.')
    
    try:
        step = mm.Step.objects.get(id=step_id)
        step.isdelete=1
        step.save()
        step_order_list = list(mm.Order.objects.filter(kind='step_business', main_id=step_id,isdelete=0))
        for o in step_order_list:
            o.isdelete=1
            o.save()
            business = mm.BusinessData.objects.get(id=o.follow_id)
            business.isdelete=1
            business.save()
    
    except:
        logger.info('删除步骤异常=>', traceback.format_exc())


def replacetext(request):
    '''
    文本替换
    '''
    node_id=request.POST.get('uid')
    old=request.POST.get('old')
    expected=request.POST.get('new')
    callername=request.session.get('username')
    r=R(callername,startnode_id=node_id, old=old, expected=expected )
    scope={
        'check_plan':request.POST.get('check_plan'),
        'check_case':request.POST.get('check_case'),
        'check_step':request.POST.get('check_step'),
        'check_business':request.POST.get('check_business'),
        'check_url':request.POST.get('check_url'),
        'check_header':request.POST.get('check_header'),
        'check_property':request.POST.get('check_property'),
        'check_params':request.POST.get('check_params'),
        }
    logger.info('scope:',scope)
    res= r.replace(scope)
    logger.info('文本替换结果:',res)
    return res

def replacerecover(request):
    '''
    文本替换回复
    '''
    uid=request.POST.get('uid')
    logger.info('开始节点文本恢复 uid=',uid)
    return R(request.session.get('username')).recover(uid)

def add_record_step(request):
    def _params_dict(params):
        d={}
        if params:
            for sep in params.split(';'):
                d[sep.split('=')[0]]=sep.split('=')[1]
        return d
    def _content_type(input):
        choice=('formdata','json','urlencode','multipart/form-data')
        for c in choice:
            if c in input:
                return c
        return ''


    params=get_params(request)
    product,plan,case,step,business=None,None,None,None,None
    try:
        product=mm.Product.objects.get(description='临时录制',isdelete=0)
        logger.info('{}已存在'.format(product))
    except:
        product=mm.Product()
        product.description='临时录制'
        product.author=params['user']
        product.save()
        logger.info('创建{}'.format(product))

    try:
        plan=mm.Plan.objects.get(description='录制步骤',isdelete=0)
    except:
        plan=mm.Plan(description='录制步骤', db_id=None, schemename=None, author=params['user'],
                       run_type='手动运行', mail_config_id=None,before_plan=None,proxy='')
        plan.save()

    try:
        case=mm.Case.objects.get(description='@{}'.format(params['user'].name),author=params['user'],isdelete=0)
    except:
        logger.error('case create error:',traceback.format_exc())
        case=mm.Case(description='@{}'.format(params['user'].name),author=params['user'])
        case.save()

    ###挂在录制数据
    try:
        protocol='http' if params['is_https']=='false' else 'https'

        url='{}{}'.format(params['host'],params['url'])
        if not url.startswith('{{'):
            url='{}://'.format(protocol)+url

        headers=params.get('request_headers')
        step=mm.Step(description=params['url'],
                     step_type='interface',
                     headers=headers,
                     url=url,
                     method=params['method'].lower(),
                     content_type=_content_type(params['content_type']),
                     count=1,
                     author=params['user'],
                     db_id=None,
                     temp='',
                     isdelete = 0
                     )
        step.save()
    except:
        logger.error(traceback.format_exc())
    try:
        business=mm.BusinessData(businessname='成功',
                          count=1,
                          itf_check='',
                          db_check='',
                          params=params['params'],
                          preposition='',
                          postposition='',
                          isdelete = 0
                          )
        business.save()

    except:
        pass

    try:
        o=mm.Order.objects.filter(kind='product_plan',main_id=product.id,follow_id=plan.id,isdelete=0)
        if not o.exists():
            mm.Order(kind='product_plan',
                     main_id=product.id,
                     follow_id=plan.id,
                     value=getnextvalue('product_plan',product.id),
                     author=params['user']
                     ).save()

        o=mm.Order.objects.filter(kind='plan_case',main_id=plan.id,follow_id=case.id,isdelete=0)
        if not o.exists():
            mm.Order(kind='plan_case',main_id=plan.id,follow_id=case.id,
                     value=getnextvalue('plan_case',plan.id),
                     author=params['user']).save()

        o=mm.Order.objects.filter(kind='case_step',main_id=case.id,follow_id=step.id,isdelete=0)
        if not o.exists():
            mm.Order(kind='case_step',main_id=case.id,follow_id=step.id,
                     value=getnextvalue('case_step',case.id),
                     author=params['user']).save()

        o=mm.Order.objects.filter(kind='step_business',main_id=step.id,follow_id=business.id,isdelete=0)
        if not o.exists():
            mm.Order(kind='step_business',main_id=step.id,follow_id=business.id,
                     value=getnextvalue('step_business',step.id),
                     author=params['user']).save()
    except:
        logger.error(traceback.format_exc())
    return {
        'status':'success',
        'msg':"添加成功"
    }







'''
修改关联功能
'''
def queryplanlink(request):
    params=get_params(request)
    left,right=[],[]
    curid=params.get('curid').split('_')[1]
    els=mm.EditLink.objects.filter(p1=curid)
    if els.exists():
        nid=curid
        links=mm.EditLink.objects.filter(p1=nid)
        for link in links:
            if link.p2 in set([x for x in right]):
                continue;
            # de=mm.Plan.objects.get(id=link.p2).description
            right.append('plan_{}'.format(link.p2))

        plans=mm.Plan.objects.values('id','description')
        for plan in plans:
            # logger.info('indexid:{}'.format(plan.id))
            if str(plan['id'])==curid:
                logger.info('左数据忽略 {}'.format(curid))
                continue;
            left.append({
                    'description':plan['description'],
                    'nid':'plan_{}'.format(plan['id'])
                })

    else:
        plans=mm.Plan.objects.values('id','description')
        for plan in plans:
            if str(plan['id'])==curid:
                logger.info('左数据忽略 {}'.format(curid))
                continue;

            left.append({
                    'description':plan['description'],
                    'nid':'plan_{}'.format(plan['id'])
                })

        right=[]

    return{
        'status':'success',
        'msg':'查询成功',
        'data':[left,right]
    }
        

def editplanlink(request):
    params=get_params(request)
    uid=params.get('uid')
    planids=[x for x in params.get('planids').split(',') if x.strip()]

    ##清老的关联

    mm.EditLink.objects.filter(p1=uid.split('_')[1]).delete()

    ##

    [_addlink(uid, planid) for planid in planids]

    return{
        'status':'success',
        'msg':'编辑成功'
    }

def querynodelink(request):
    kind=get_params(request)['nid'].split('_')[0]
    nid=get_params(request)['nid'].split('_')[1]
    stepids,businessids=[],[]
    _get_step_business(get_params(request)['nid'], stepids, businessids)

    logger.info('节点{}下查到步骤：{} 查到测试点{}'.format(get_params(request)['nid'],stepids,businessids))

    res=[]
    for sid in stepids:
        step=mm.Step.objects.get(id=sid)
        sel=mm.EditLink.objects.filter(snid='step_{}'.format(sid))
        for l in sel:
            tnid=l.tnid
            tstep=mm.Step.objects.get(id=tnid.split('_')[1])
            res.append({
                    'id':l.id,
                    'snid':sid,
                    'tnid':tnid,
                    'sd':step.description,
                    'td':tstep.description,
                })

    for bid in businessids:
        b=mm.BusinessData.objects.get(id=bid)
        bel=mm.EditLink.objects.filter(snid='business_{}'.format(bid))
        for l in bel:
            tnid=l.tnid
            bb=mm.BusinessData.objects.get(id=tnid.split('_')[1])
            res.append({
                    'id':l.id,
                    'snid':bid,
                    'tnid':tnid,
                    'sd':b.businessname,
                    'td':bb.businessname
                })

    return{
        'status':'success',
        'msg':'查询成功',
        'data':res,
        'count':len(res)
    }

def _check_level(data1,data2):
    if data2.strip()=='[]':
        return True
    else:
        logger.info('data2 lne:',len(data2))
        logger.info('data2 :',data2)

    m=['product','plan','case','step','business']
    d1,d2='',''
    for _ in m:
        if _ in data1:
            d1=_
            break

    for _ in m:
        if _ in data2:
            d2=_
            break

    return d1==d2


def _fulldata(data,res):
    res=[]
    for item in data:
        if item['type']!='business' and not item.get('children') and item['checked']==True:
            cur=[]
            get_all_child_nodes(item['id'], cur)
            res=res+cur
        elif item.get('children'):
            for k in item.get('children'):
                pass

            # plans=getchild('product_plan',item['id'].split('_')[1])
    return res

def _handlefulldata(data1,data2,user,flag):
    count=0
    for d1 in data1:
        for d2 in data2:
            if d1['name']==d2['name']:
                el=mm.EditLink()
                el.snid=d1['nid']
                el.tnid=d2['nid']
                el.flag=el.flag
                el.save()
                count=count+1
                logger.info('[handledata建立link]snid={} tnid={}'.format(el.snid,el.tnid))
    return count
def querylinkcontrol(request):
    nid=get_params(request)['srcid']
    kind=get_params(request)['kind']
    queryid='link_control_{}'.format(nid)
    is_exist=mm.StatusControl.objects.filter(name=queryid).exists()
    if is_exist:
        return {
            'status':'fail',
            'msg':'已在关联'
        }
    else:
        return{
            'status':'success',
            'msg':''
        }

def _get_need_handle_nodeid(data,grab_node):
    '''补充前端数据可能需要计算子节点的项
    :param data:
    :param grab_node:
    :return:
    '''
    for d in data:
        if d['type']!='business' and d['checked']==True and d.get('children',None) is None:
            grab_node.append(d['id'])
        if d.get('children',None):
            _get_need_handle_nodeid(d.get('children'),grab_node)


def _get_me_o(nid):
    classname=None
    kind=nid.split('_')[0]
    oid=nid.split('_')[1]
    classname=kind.capitalized()
    if classname=='Business':
        classname='BusinessData'

    return 'mm.{}.objects.get(id={})'.format(classname,oid)


def addeditlink(request):
    count=0
    user=mm.User.objects.get(name=request.session.get('username'))
    params=get_params(request)
    con=mm.StatusControl()
    con.name='link_control_{}'.format(params['nid'])
    con.value=''
    con.save()
    logger.info('新建状态位：{}'.format(con.name))

    flag=EncryptUtils.md5_encrypt(str(time.time()))

    ##level校验
    if not _check_level(params['data1'],params['data2']):
        return{
            'status':'fail',
            'msg':'树两边层级不一样 不能关联'
        }
    data1=json.loads(params['data1'])
    data2=json.loads(params['data2'])

    ##需要都选
    if not data1 :
        mm.StatusControl.objects.filter(name='link_control_{}'.format(params['nid'])).delete()
        return{
            'status':'error',
            'msg':'请先选择要关联的用例'
        }

    ##清除已关联数据 重新关联
    history=list(mm.EditLink.objects.filter(snid=params['nid']))
    if history:
        flag=history[0].flag
        mm.EditLink.objects.filter(flag=flag).delete()
        logger.info('清除已关联数据 planid={} flag={}'.format(params['nid'],flag))

    if not data2:
        monitor.push_user_message(str(user.id), '关联修改完成.')
        mm.StatusControl.objects.filter(name='link_control_{}'.format(params['nid'])).delete()
        return{
            'status':'fail',
            'msg':'修改成功'
        }

    data1,data2=data1[0],data2[0]
    # logger.info('data1:\n{} \ndata2:{}'.format(data1,data2))
    left_routes,right_routes=[],[]
    ##检查左边树是否存在唯一的计划节点
    _get_route(data1,[],left_routes)
    _get_route(data2,[],right_routes)

    logger.info('left_routes:\n{}'.format(left_routes))
    logger.info('right_routes:\n{}'.format(right_routes))
    left_product_check,left_plan_check=[],[]
    for x in left_routes:
        if x and x[0] not in left_product_check:
            left_product_check.append(x[0])
        if x[1] not in left_plan_check:
            left_plan_check.append(x[1])

        if len(left_plan_check)>1 or len(left_product_check)>1:
            mm.StatusControl.objects.filter(name='link_control_{}'.format(params['nid'])).delete()
            return{
                'status':'error',
                'msg':'左边树暂时只支持选一个产品计划'
            }
    logger.info('left_routes_k:\n{}'.format([xx.get('name') for x in left_routes for xx in x]))
    logger.info('right_routes_k:\n{}'.format([xx.get('name') for x in right_routes for xx in x]))

    ##处理前端可能不完整的数据
    logger.info('开始处理前端可能不完整的数据')
    start_time = time.time()
    grab_node_left, grab_node_right = [], []
    need_link_left, need_link_right = [], []
    _get_need_handle_nodeid([data1], grab_node_left)
    for x in grab_node_left:
        get_all_child_nodes(x, need_link_left)
    _get_need_handle_nodeid([data2], grab_node_right)
    for x in grab_node_right:
        get_all_child_nodes(x, need_link_right)

    logger.info('need_link_left:', need_link_left)
    logger.info('need_link_right:', need_link_right)

    ###有BUG
    for x in need_link_left:
        for y in need_link_right:
            if x['name'] == y['name'] and x['nid'].split('_')[0] == y['nid'].split('_')[0] and x['level'] == y['level']:
                el = mm.EditLink()
                el.snid = x['nid']
                el.tnid = y['nid']
                el.flag = flag
                el.save()
                count = count + 1

    logger.info('处理完不完整数据 关联{}条'.format(count ))

    ##处理结束
    logger.info('开始处理前端完整的数据')
    cur_count=copy.deepcopy(count)
    for x in left_routes:
        xflag=':'.join(['{}_{}'.format(xx.get('id').split("_")[0],xx.get('name')) for xx in x][2:])
        xsize=len(x)
        # if xsize<5:
        #     logger.info('关联链节点最后不是测试点略过.')
        #     continue;
        # logger.info('xflag:',xflag,'xsize:',xsize)
        for y in right_routes:
            yflag=':'.join(['{}_{}'.format(xx.get('id').split("_")[0],xx.get('name')) for xx in y][2:])
            ysize=len(y)
            # if ysize<5:
            #     logger.info('关联链节点最后不是测试点略过.')
            #     continue;

            if xflag==yflag and xsize==ysize :
                logger.info('关联数据 xflag:{} yflag:{}'.format(xflag,yflag))
                for i in range(xsize):
                    xnid=x[i].get('id')
                    ynid=y[i].get('id')
                    xkind=xnid.split('_')[0]
                    ykind=ynid.split('_')[0]
                    if xkind!=ykind:
                        continue;

                    is_exist=mm.EditLink.objects.filter(snid=xnid,tnid=ynid,flag=flag)
                    if is_exist:
                        continue;

                    el=mm.EditLink()
                    el.snid=xnid
                    el.tnid=ynid
                    el.flag=flag
                    el.save()
                    logger.info('[建立link {}->{}]'.format(el.snid,el.tnid))
                    count=count+1

    logger.info('处理完前端明确关联数据 {}条'.format(count-cur_count))
    ##
    logger.info('本次关联结束 关联条数:{}..'.format(count))
    planname=mm.Plan.objects.get(id=params['nid'].split('_')[1]).description
    monitor.push_user_message(str(user.id),'计划[{}]关联完成 成功{}条'.format(planname,count))


    ##
    mm.StatusControl.objects.filter(name='link_control_{}'.format(params['nid'])).delete()
    return {
        'status':'success',
        'msg':'关联成功[{}]条.'.format(count)
    }



def _get_route(data,cur_route,all_route):
    d1checked=data.get('checked')
    d1kind=data.get('type')
    d1name=data.get('name','')
    d1child=data.get('children',[])

    if len(d1child)==0:
        all_route.append(copy.deepcopy(cur_route))
      
        return False


    for c in d1child:
        if c.get('checked'):
            cur_route.append(c)
            flag=_get_route(c,cur_route,all_route)
            if flag==False:
                cur_route=copy.deepcopy(cur_route[:-1])



def _filter_data(data):
    for nodedata in data:
        if nodedata.get('checked')==False:
            data.remove(nodedata)
        child=nodedata.get('children')



def _addlink(nid1,nid2):

    logger.info('需要关联的期望节点 {}&&{}'.format(nid1,nid2))
    try:
        starttype=nid1.split('_')[0]
        stepids1,businessids1=[],[]
        stepids2,businessids2=[],[]
        _get_step_business(nid1, stepids1, businessids1)
        _get_step_business(nid2, stepids2, businessids2)

        for s1 in stepids1:
            for s2 in stepids2:
                name1=mm.Step.objects.get(id=s1).description
                name2=mm.Step.objects.get(id=s2).description
                if name1==name2:
                    el=mm.EditLink()
                    el.snid='step_%s'%s1
                    el.tnid='step_%s'%s2
                    if mm.EditLink.objects.filter(snid='step_%s'%s1,tnid='step_%s'%s2).exists():
                        continue;
                    el.p1=nid1.split('_')[1]
                    el.p2=nid2.split('_')[1]
                    el.save()
                    logger.info('建立link {}->{}'.format('step_%s'%s1,'step_%s'%s2))

        for b1 in businessids1:
            for b2 in businessids2:
                bname1=mm.BusinessData.objects.get(id=b1).businessname
                bname2=mm.BusinessData.objects.get(id=b2).businessname

                if bname1==bname2:
                    el=mm.EditLink()
                    el.snid='business_%s'%b1
                    el.tnid='business_%s'%b2
                    if mm.EditLink.objects.filter(snid='business_%s'%b1,tnid='business_%s'%b2).exists():
                        continue;
                    el.p1=nid1.split('_')[1]
                    el.p2=nid2.split('_')[1]
                    el.save()
                    logger.info('建立link {}->{}'.format('business_%s'%b1,'business_%s'%b2))
        return{
            'status':'success',
            'msg':'关联成功'
        }
    except:
        logger.error('关联异常:\n{}'.format(traceback.format_exc()))
        return{
            'status':'error',
            'msg':'关联异常'
        }

def _get_step_business(nid,stepids,businessids):
    nodetype=nid.split('_')[0]
    nodeid=nid.split('_')[1]

    if 'plan'==nodetype:
        caseo=mm.Order.objects.filter(kind='plan_case',main_id=nodeid)
        for co in caseo:
            #####
            stepo=mm.Order.objects.filter(kind='case_step',main_id=co.follow_id)
            for step in stepo:
                if not step.follow_id in stepids:
                    stepids.append(step.follow_id)
                businesso=mm.Order.objects.filter(kind='step_business',main_id=step.follow_id)
                for bu in businesso:
                    if not bu.follow_id in businessids:
                        businessids.append(bu.follow_id)

            #####
            last_cases=[]
            caseids=_get_last_cases('case_{}'.format(co.follow_id,),last_cases=last_cases)
            for caseid in caseids:
                stepo=mm.Order.objects.filter(kind='case_step',main_id=caseid.split('_')[1])
                for step in stepo:
                    if not step.follow_id in stepids:
                        stepids.append(step.follow_id)
                    businesso=mm.Order.objects.filter(kind='step_business',main_id=step.follow_id)
                    for bu in businesso:
                        if not bu.follow_id in businessids:
                            businessids.append(bu.follow_id)

    elif 'case'==nodetype:
        stepo=mm.Order.objects.filter(kind='case_step',main_id=nid.split('_')[1])
        for step in stepo:
            if not step.follow_id in stepids:
                stepids.append(step.follow_id)
            businesso=mm.Order.objects.filter(kind='step_business',main_id=step.follow_id)
            for bu in businesso:
                if not bu.follow_id in businessids:
                    businessids.append(bu.follow_id)

        #####
        last_cases=[]
        caseids=_get_last_cases(nid,last_cases=last_cases)
        for caseid in caseids:
            stepo=mm.Order.objects.filter(kind='case_step',main_id=caseid.split('_')[1])
            for step in stepo:
                if not step.follow_id in stepids:
                    stepids.append(step.follow_id)
                businesso=mm.Order.objects.filter(kind='step_business',main_id=step.follow_id)
                for bu in businesso:
                    if not bu.follow_id in businessids:
                        businessids.append(bu.follow_id)


def _get_last_cases(caseid,last_cases=None):
    if last_cases is None:
        last_cases=[]
    o=mm.Order.objects.filter(kind='case_case',main_id=caseid.split('_')[1])
    if o.exists():
        for x in o:
            return _get_last_cases('case_{}'.format(x.follow_id),last_cases=last_cases)
    else:
        last_cases.append(caseid)
        return last_cases


def _diff_object(obj1,obj2,ignore_attr=None):
    map_={}
    if obj1.__class__.__name__!=obj2.__class__.__name__:
        logger.info(1)
        return map_

    attrs1,attrs2=dir(obj1.__class__),dir(obj2.__class__)
    if attrs1!=attrs2:
        logger.info(2)
        return map_

    setlist=[x for x in attrs1 if not x.startswith('_')]

    # setlist=[x for x in setlist if type(getattr(obj1,x)).__name__ in ('str','int')]
    # logger.info('set2:{}'.format(setlist))
    a=[]
    for f in setlist:
        if 'pk'==f:
            continue;
        try:
            classname=type(getattr(obj1,f))
            # print('111:',type())
            if classname  in(str,int):
                a.append(f)

        except:
            pass

    for attrname in setlist:
        if ignore_attr and attrname in ignore_attr:
            continue;

        try:
            v1=getattr(obj1,attrname)
            v2=getattr(obj2, attrname)
            if v1!=v2:
                al=map_.get(attrname,[])
                al.append(v1)
                al.append(v2)
                map_[attrname]=al
        except:
            pass

    return map_

def _update_object(target,diff):
    '''
        根据修改前后的对象属性差字典 自动修改关联的步骤或测试点
        int&str格式外的属性暂时没考虑
    '''
    logger.info('==调整对象{}属性值'.format(target))
    for attrname in [x for x in dir(target) if not x.startswith('__')]:
        if attrname in diff:
            oldvalue=getattr(target, attrname)
            if oldvalue==diff[attrname][0]:
                setattr(target, attrname, diff[attrname][1])
                logger.info('==调整属性{} {}->{}'.format(attrname,diff[attrname][0],diff[attrname][1]))


    target.save()
    logger.info('==调整结束==')


def _compute_attribute(diff,targetstr):
    logger.info('=开始根据差异map推演目标值==')
    count_,map_={},{}
    logger.info('差异map:{}'.format(diff))
    logger.info('推演目标初始值:{}'.format(list(targetstr)))
    ########
    for i in range(len(diff)):
        if diff[i].startswith('-') or diff[i].startswith('+'):
            bchar=_get_before_common_char(i,diff)
            # logger.info('bchar[{}]->{}, cur->{}:'.format(i,bchar,diff[i]))
            keycount= 0 if count_.get(bchar,None) is None else count_.get(bchar)
            keyc=0 if keycount-1<0 else keycount-1
            mapvalue=map_.get('{}[{}]'.format(bchar,keyc),[])
            # logger.info('{} 已有:{}'.format('{}[{}]'.format(bchar,keyc),mapvalue))
            mapvalue.append(diff[i])
            map_['{}[{}]'.format(bchar,keyc)]=mapvalue
            # logger.info('保存字符{} 操作序列：{}'.format('{}[{}]'.format(bchar,keyc),mapvalue))
            if diff[i].startswith('+'):
                curindx=0 if count_.get(diff[i].strip(),None) is None else count_.get(diff[i].strip())
                count_[diff[i][-1]]=curindex+1
        else:
            curindex=0 if count_.get(diff[i].strip(),None) is None else count_.get(diff[i].strip())
            count_[diff[i][-1]]=curindex+1

    ######
    count_={}
    targetcopy=list(targetstr)
    delidx=[]
    for i in range(len(targetcopy)):
        try:
            keycount=0 if count_.get(targetcopy[i],None) is None else count_.get(targetcopy[i])
            key='{}[{}]'.format(targetcopy[i],keycount)
            # logger.info('查询key:{}'.format(key))
            operatelist=map_.get(key,None)
            if operatelist:
                # logger.info('获得字符{} 操作序列:{}'.format(key,operatelist))
                for op in operatelist:
                    if op.startswith('-'):
                        # logger.info('targetcopy[i+1]:{} op[-1]:{}'.format(targetcopy[i+1],op[-1]))
                        try:
                            delid=i+1+len(delidx)
                            delidx.append(delid)

                            # logger.info('保留[-]操作序号{}'.format(delid))
                        except:
                            logger.error(traceback.format_exc())

                    elif op.startswith('+'):
                        try:
                            targetcopy.insert(i+1, op[-1])
                        except:
                            logger.error(traceback.format_exc())

            count_[targetcopy[i]]=keycount+1
          
        except:
            logger.error(traceback.format())

    # logger.info('[-]操纵前的：{}   delids:{}'.format(targetcopy,delidx))

    for i in range(len(targetcopy)):
        for di in delidx:
            if di==i:
                targetcopy[i]='~~'
   
    targetcopy=[x for x in targetcopy if x!='~~']

    logger.info('推演目标结果值:{}'.format(targetcopy))
    return ''.join(targetcopy)

def _get_before_common_char(index,iter):
    n=iter[:index][::-1]
    for ch in n:
        if not ch.startswith('-'):
            return ch[-1]

    return None




