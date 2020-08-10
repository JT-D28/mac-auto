#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-11-19 09:51:22
# @Author  : Blackstone
# @to      :
import time, traceback, redis, datetime, requests, copy, os,multiprocessing
from django.conf import settings
from hashlib import md5
from ME2.settings import logme, BASE_DIR
from manager.models import *
from manager.models import Case as Case0
from login.models import *
from functools import update_wrapper

from manager.operate.mongoUtil import Mongo
from manager.operate.redisUtils import RedisUtils
from functools import update_wrapper

'''


'''
m_pool=multiprocessing.Pool(processes=4)


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

"""
控制台输出
redis key格式=>console.msg::username::taskid
"""


cons={}

def viewcache(taskid, *msg):
    try:
        what = "%s        %s<br>" % (time.strftime("[%m-%d %H:%M:%S]", time.localtime()), "".join([str(x) for x in msg if x]))
        Mongo.tasklog(taskid).insert_one({'time': time.time(), 'info': what})
    except Exception as e:
        Me2Log.error("viewcache异常")
        Me2Log.error(traceback.format_exc())


def remotecache(key, linemsg):
    con = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    con.lpush(key, linemsg)
    con.close()


# 运行中的任务 以及taskid
_runninginfo = dict()


def setRunningInfo(planid, taskid, runkind, dbscheme='全局'):
    planid = int(planid)
    # runkind 0:未运行   1：验证 2：调试  3:定时
    if Mongo.taskid().find({"planid": planid}).count() == 0:
        Mongo.taskid().insert_one({"planid": planid, "runkind": "0", "dbscheme": "全局", "verify": "", "debug": ""})
    updatestr=''
    if runkind in ['1', '3']:
        updatestr = {"runkind": runkind, "verify": taskid, "dbscheme": dbscheme}
    elif runkind == '2':
        updatestr = {"runkind": "2", "debug": taskid, "dbscheme": dbscheme}
    elif runkind == '0':
        updatestr = {"runkind": "0"}

    Mongo.taskid().update({"planid": planid}, {"$set": updatestr})

    Me2Log.info("储存运行信息", Mongo.taskid().find_one({"planid": planid}))


def getRunningInfo(planid='', type='isrunning'):
    planid = int(planid)
    _runninginfo = Mongo.taskid().find_one({"planid": planid})
    _runninginfo = _runninginfo if _runninginfo else {}

    if type == 'debug_taskid':
        return _runninginfo.get('debug','')
    elif type == 'verify_taskid':
        return _runninginfo.get('verify','')
    elif type == 'isrunning':
        return _runninginfo.get('runkind','0')
    elif type == 'dbscheme':
        from .models import Plan
        nofind = Plan.objects.get(id=planid).schemename
        dbscheme = _runninginfo.get('dbscheme', nofind)
        return dbscheme


def get_space_dir():
    '''
    获取我的空间绝对地址
    '''
    return os.path.join(os.path.dirname(__file__),'storage','private','File')

def get_temp_dir():
    '''
    获取模板文件绝对地址
    '''
    dirs=[]
    dirs.append(os.path.join(os.path.dirname(__file__),'template','cm'))
    dirs.append(os.path.join(os.path.dirname(__file__),'template','manager'))
    dirs.append(os.path.join(os.path.dirname(os.path.dirname(__file__)),'login','template','login'))

    return dirs

def get_project_dir():
    return os.path.dirname(os.path.dirname(__file__))


'''
mock
'''
mocknow=set()
repeat=set()

def clear_mock(username):
    for k in list(mocknow):
        if username in k:
            mocknow.remove(k)

def add_mock_key(key):
    mocknow.add(key)

def has_mock_run(key):
    return True if key in mocknow else False


def add_mock(f):
    from tools.mock import TestMind
    from manager.models import Step,SimpleTest

    color_res = {
        'success': 'green',
        'fail': 'red',
        'skip': 'orange',
        'omit': 'green',
    }
    def _wrap(*args,**kws):
        try:
            Me2Log.info('[mock测试]==========================')
            callername=args[0]
            taskid=args[1]
            order=args[2]
            step=Step.objects.get(id=order.main_id)
            stepid=step.id
            Me2Log.info('[mock测试]\nusername={} stepid={}'.format(callername,stepid))
            key='{}_{}'.format(callername,stepid)
            if has_mock_run(key):
                pass
            else:
                add_mock_key(key)
                ##mock
                SL=SimpleTest.objects.filter(step_id=stepid)
                if not SL.exists():
                    TestMind().gen_simple_test_cases('step_{}'.format(stepid))
                vbs=TestMind().get_visual_business('step_{}'.format(stepid), callername)
                # Me2Log.info('vbs:',vbs)
                _m=set()
                
                for vb in vbs:
                    kind=1 if vb.businessname in _m else None
                    result,error=_step_mock(callername, taskid, step, vb,kind=kind)
                    _m.add(vb.businessname)

                    result = "<span class='layui-bg-%s'>%s</span>" % (color_res.get(result, 'orange'), result)
                    error = '   原因=>%s' % error if 'success' not in result else ''
                    viewcache(taskid, "步骤执行结果%s%s" % (result, error))

        except:
            Me2Log.info('[mock测试异常]{}',traceback.format_exc())
            return f(*args,**kws)


        return f(*args,**kws)
    return update_wrapper(_wrap,f)



def _step_mock(callername, taskid, step,businessdata, kind=None,is_repeat=0):
    """
    return (resultflag,msg)
    """
    from manager.invoker import _callinterface,_callsocket,_compute


    try:
        is_mock_open=step.is_mock_open
        if not is_mock_open:
            return

        user = User.objects.get(name=callername)
        # businessdata = BusinessData.objects.get(id=order.follow_id)
        timeout = 60 if not businessdata.timeout else businessdata.timeout
        
        if businessdata.count == 0:
            return ('omit', "测试点[%s]执行次数=0 略过." % businessdata.businessname)
        preplist = businessdata.preposition.split("|") if businessdata.preposition is not None else ''
        postplist = businessdata.postposition.split("|") if businessdata.postposition is not None else ''
        db_check = businessdata.db_check
        itf_check = businessdata.itf_check
        #status, paraminfo = BusinessData.gettestdataparams(order.follow_id)
        paraminfo = businessdata.params
        
        # Me2Log.info('bbid=>',businessdata.id)
        # status1, step = BusinessData.gettestdatastep(businessdata.id)
        
        username = callername   
        if is_repeat==0:     
            viewcache(taskid, "--" * 100)
            viewcache(taskid,
                      "开始执行步骤[<span style='color:#FF3399'>%s</span>] 测试点[<span style='color:#FF3399' id=%s>%s</span>]&nbsp;<i style='background-color:#009688;color:#fff;'>mock test</i>" % (
                          step.description,businessdata.id, businessdata.businessname))
        
        # dbid = getDbUse(taskid, step.db_id)
     
        # if dbid:
        #     desp = DBCon.objects.get(id=int(dbid)).description
        #     set_top_common_config(taskid, desp, src='step')
        # # 前置操作
        # status, res = _call_extra(user, preplist, taskid=taskid, kind='前置操作')  ###????
        # if status is not 'success':
        #     return (status, res)
        
        if step.step_type == "interface":
            if is_repeat==0:
                viewcache(taskid, "数据校验配置=>%s" % db_check)
                viewcache(taskid, "接口校验配置=>%s" % itf_check)
            headers = []
            
            text, statuscode, itf_msg = '', -1, ''
            
            if step.content_type == 'xml':
                if re.search('webservice', step.url):
                    headers, text, statuscode, itf_msg = _callinterface(taskid, user, step.url, str(paraminfo), 'post',
                                                                        None, 'xml', step.temp, kind, timeout)
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
                                                                    step.headers, step.content_type, step.temp, kind,
                                                                    timeout)
            if text.lstrip().startswith('<!DOCTYPE html>') and is_repeat==0:
                viewcache(taskid,"<span style='color:#009999;'>请求响应=><xmp style='color:#009999;'>内容为HTML，不显示</xmp></span>")
            else:
                if is_repeat==0:
                    viewcache(taskid,"<span style='color:#009999;'>请求响应=><xmp style='color:#009999;'>%s</xmp></span>" % text)
            
            if len(str(statuscode)) == 0:
                return ('fail', itf_msg)
            elif statuscode == 200:
                
                # ##后置操作
                # status, res = _call_extra(user, postplist, taskid=taskid, kind='后置操作')  ###????
                # if status is not 'success':
                #     return (status, res)
                
                if db_check:
                    res, error = _compute(taskid, user, db_check, type="db_check", kind=kind)
                    if res is not 'success':
                        Me2Log.info('################db_check###############' * 20)
                        return ('fail', error)
                
                if itf_check:
                    if step.content_type in ('json', 'urlencode','formdata'):
                        res, error = _compute(taskid, user, itf_check, type='itf_check', target=text, kind=kind,
                                              parse_type='json', rps_header=headers)
                    else:
                        res, error = _compute(taskid, user, itf_check, type='itf_check', target=text, kind=kind,
                                              parse_type='xml', rps_header=headers)
                    
                    if res is not 'success':
                        return ('fail', error)
                
                return ('success', '')
            else:
                return ('fail', 'statuscode=%s' % statuscode)
            
            if itf_msg:
                Me2Log.info('################itf-msg###############' * 20)
                return ('fail', itf_msg)
        
        elif step.step_type == "function":
            if is_repeat==0:
                viewcache(taskid,"数据校验配置=>%s" % db_check)
            
            # methodname=re.findall("(.*?)\(.*?\)", step.body.strip())[0]
            # builtinmethods=[x.name for x in getbuiltin() ]
            # builtin=(methodname in builtinmethods)
            
                viewcache(taskid,"调用函数=>%s" % step.body)
            
            Me2Log.info('关联id=>', step.related_id)
            res, msg = _callfunction(user, step.related_id, step.body, paraminfo, taskid=taskid)
            if is_repeat==0:
                viewcache(taskid, "函数执行结果=>%s" % res)
            
            # Me2Log.info('fjdajfd=>',res,msg)
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
                return ('success', '')
        return ('success','')
    
    except Exception as e:
        # traceback.Me2Log.info_exc()
        Me2Log.info(traceback.format_exc())
        return ("error", "执行任务[%s] 未处理的异常[%s]" % (taskid, traceback.format_exc()))

class monitor(object):
    '''
    用户操作日志监控
    action:必填
    descripton:选填 
        可填eval表达式 $开头
        不填默认为参数中包含decription|name字段的值 
    '''
    def __init__(self,*args0,**kws0):
        self.kind=kws0.get('kind','request')

        self.username='某人'
        self.description=kws0.get('description','')
        self.authorname=kws0.get('authorname','')

        self.action=kws0['action']

    @classmethod
    def push_user_message(cls,userids,news,sendername='admin',title='系统消息'):
        from manager.models import  News
        '''
        允许向单人推送消息
        允许向多人推送相同消息
        '''
        Me2Log.info('准备推送消息')
        if isinstance(userids,(str,)):
            if isinstance(news, (str,)):

                n=News()
                n.title=title
                n.description=news
                n.sender=User.objects.get(name=sendername)
                n.recv=userids.strip()
                n.recv_kind='USER'
                n.is_read=0
                n.save()

            elif isinstance(news, (list,)):
                for new in news:
                    cls._push_user_message(userids, str(new),sendername=sendername,title=title)

        elif isinstance(userids, (list,)):
            if isinstance(news, (str,)):
                for userid in userids:
                    n=News()
                    n.title=title
                    n.description=news
                    n.sender=User.objects.get(name=sendername)
                    n.recv=userid
                    n.recv_kind='USER'
                    n.is_read=0
                    n.save()



    def _get_authorname(self,authorname,callername,params):

        if authorname:
            if authorname.startswith('$'):
                authorname=authorname.replace('$','')
                ms=re.findall('\[.*?\]', authorname)
                for m in ms:
                    key=re.findall('\[(.*?)\]', m)[0]

                    if '__in' in authorname:
                        authorname=authorname.replace(m,str(params[key].split(',')))
                    else:
                        authorname=authorname.replace(m,params[key])
                        authorname=authorname+'author.name'
                try:

                    Me2Log.info('authorname1:',str(eval(authorname)))
                    return str(eval(authorname))
                except:
                    Me2Log.error('authorname表达式[%s]计算异常:',(authorname,traceback.format_exc()))
                    return callername
            else:
                return authorname
        else:
            return None

    def _get_description(self,description,params):
        '''
        '''
        if description:
            if description.startswith('$'):
                try:
                    description=description.replace('$', '')
                    ms=re.findall('\[.*?\]', description)
                    for m in ms:
                        key=re.findall('\[(.*?)\]', m)[0]
                        description=description.replace(m,params[key])

                    Me2Log.info(type(Case).__name__)
                    Me2Log.info('计算：%s'%description)
                    description=str(eval(description))
                    Me2Log.info('结果： %s'%description)
                except:
                    print(traceback.format_exc())
                    description='非法表达式 %s'%description
        else:
            for k,v in params.items():
                if 'name' in k:
                    description=str(v)
                    break;

                elif 'description' in k:
                    description=str(v)
                    break;

        return description


    def __call__(self,*args1,**kws1):
        def _wrap(*args2,**kws2):

            from manager.models import OperateLog,News

            result=args1[0](*args2,**kws2)
            params=dict()
            from manager.core import get_params
            if  type(args2[0]).__name__=='AsgiRequest':
                params=get_params(args2[0])

            else:
                params=kws2

            Me2Log.info('params:',params)

            self.username=params['user']
            msg='用户%s%s '%(self.username,self.action)
            description=self._get_description(self.description, params)
            authorname=self._get_authorname(self.authorname, self.username,params)

            msg=msg+'[%s]'%description if description else msg
            Me2Log.info(msg)

            og=OperateLog()
            og.opcode=''
            og.opname=self.action
            og.description=msg
            og.author=User.objects.get(name=self.username)
            og.save()

            Me2Log.info('authorname:',authorname)

            if authorname and  authorname!=self.username:
                news=News()
                news.title='系统提示信息'
                news.description=msg
                news.sender=User.objects.get(name='admin')
                news.is_read=0
                news.recv=User.objects.get(name=authorname).id
                news.recv_kind="USER"

                news.save()
                Me2Log.info('向用户[%s]发送一条信息[%s]'%(authorname,news.description))
            return result

        return update_wrapper(_wrap,args1[0])




# class ValidChecker(object):
#     '''
#     函数有效性校验工具  控制台输出提示

#     '''
#     _log_level='ERROR'
    
#     def custom_method_check(self,f):
#         from manager.core import Fu
#         '''
#         自定义函数有效性校验
#         '''
#         def _wrap(*args,**kws):
#             kws['level']=self._log_level
#             src='{}({})'.format(f,','.join(args))
#             tzm=Fu.tzm_compute(src, '(.*?)\((.*?)\)')
#             count=Function.objects.filter(flag=tzm).count()
#             if 0==count:
#                 cout('函数{}调用错误,请检查参数'.format(f),**kws)
#             elif count>1:
#                 cout('函数{}调用错误, 库中找到多个同flag'.format(f),**kws)


#             return f(*args,**kws)
#         return update_wrapper(_wrap, f)



#     def params_check(self,f):
#         '''
#         参数值有效性校验
#         '''
#         def _wrap(*args,**kws):
#             for p in args:
#                 if not isinstance(p, (str,list,tuple,dict,int,float)):
#                     cout('函数{}调用参数{}类型python无法识别请检查'.format(f,p),**kws)

#             return f(*args,**kws)
#         return update_wrapper(_wrap, f)