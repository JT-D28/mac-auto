#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-11-19 09:51:22
# @Author  : Blackstone
# @to      :
import time, traceback, redis, datetime, requests, copy, os
from django.conf import settings
from hashlib import md5
from ME2.settings import logme, BASE_DIR
from manager.models import *
from manager.models import Case as Case0
from login.models import *
from manager.operate.redisUtils import RedisUtils

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

def viewcache(taskid, username, kind=None, *msg):
    if cons.get(taskid,None) is None:
        cons[taskid]=RedisUtils()
    con = cons.get(taskid)
    try:
        logname = BASE_DIR + "/logs/" + taskid + ".log"
        what = "".join((msg))
        what = "%s        %s" % (time.strftime("[%m-%d %H:%M:%S]", time.localtime()), what)
        with open(logname, 'a', encoding='UTF-8') as f:
            f.write(what + '<br>\n')

        # 定时任务不加入redis队列
        if kind is not None or username=='定时任务':
            return

        key = "console.msg::%s::%s" % (username, taskid)
        con.lpush(key, what)

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
    from .models import Plan
    Me2Log.info('username:%s planid:%s type:%s'%(username,planid,type))
    if type == 'lastest_taskid':
        latest_taskids = _runninginfo.get('lastest_taskid', {})
        latest_taskid = latest_taskids.get(username, '')
        return latest_taskid
    elif type == 'debug_taskid':
        planinfo = _runninginfo.get(str(planid), {})
        debug = planinfo.get('debug', {})
        debug_taskid = debug.get('taskid', '')
        return debug_taskid
    elif type == 'verify_taskid':
        planinfo = _runninginfo.get(str(planid), {})
        verify = planinfo.get('verify', {})
        verify_taskid = verify.get('taskid', '')
        return verify_taskid
    elif type == 'isrunning':
        planinfo = _runninginfo.get(str(planid), {})
        isrunning = planinfo.get('isrunning', '0')
        return str(isrunning)
    elif type == 'dbscheme':
        planinfo = _runninginfo.get(str(planid), {})

        nofind = Plan.objects.get(id=planid).schemename
        dbscheme = planinfo.get('dbscheme', nofind)

        return dbscheme


def get_space_dir(callername):
    '''
    获取我的空间绝对地址
    '''
    return os.path.join(os.path.dirname(__file__),'storage','private','File',callername)

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
    def _push_user_message(cls,userids,news,sendername='admin',title='系统消息'):
        '''
        允许向单人推送消息
        允许向多人推送相同消息
        '''
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

        return _wrap