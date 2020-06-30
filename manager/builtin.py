#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-10-11 14:31:32
# @Author  : Blackstone
# @to      :

import traceback, time, datetime, random, re, requests

from .context import get_top_common_config, viewcache
from .db import Mysqloper



def cout(*msg, **kws):
    '''
    控制台输出日志
    关键字参数level={DEBUG,INFO,WARN,ERROR}
    '''
    taskid=kws['taskid']
    callername=kws['callername']
    level=kws.get('level','DEBUG')
    _colormap={
        'DEBUG':'#339999',
        'INOF':'#009688',
        'WARN':'#FFFF00',
        'ERROR':'#FF3300'
    }
    text=' '.join([str(x) for x in msg])
    msg = "<span style='color:%s;'>%s</span>" % (_colormap[level],text)
    viewcache(taskid, callername, None, msg)

def getpropety(key,**kws):
    '''
    用户获取属性
    '''
    from manager.invoker import _tempinfo
    username=kws['callername']
    try:
        v=_tempinfo.get(username,{}).get(key,'')
        cout('用户{}获取自定义属性{}的值{}success .'.format(username,key,v),**kws)
        return v

    except:
        return 'error'

def saveproperty(key,value,**kws):
    '''
    用户设置属性
    '''
    from manager.invoker import _tempinfo
    msg=''
    username=kws['callername']
    try:
        up=_tempinfo.get(username,{})
        up[key]=value
        msg='用户{}自定义属性{}={} success.'.format(username,key,value)
        return ('success',msg)
        
    except:
        msg='用户{}自定义属性{}={} error.'.format(username,key,value)
        return ('error',msg)

def dbexecute(sql, **kws):

	"""
	执行单条sql
	单字段查询语句返回查询结果,不支持多字段
	非查询语句返回执行后影响条数

	"""
	taskid=kws['taskid']
	callername=kws['callername']

	if taskid is None:
		return 'error', 'taskid为空'
	op = Mysqloper()
	sql = sql.replace('@@', '$#$')
	if re.search('@', sql) is None:
		sql = sql.split(";")[:-1] if sql.endswith(";") else sql.split(";")[0]
		dbnamecache = get_top_common_config(taskid)
		print("调用内置函数=>dbexecute \nsql=>", sql)
		return op.db_execute("%s@%s" % (sql, dbnamecache), taskid=taskid, callername=callername)
	else:
		print("调用内置函数=>dbexecute \nsql=>", sql)
		return op.db_execute(sql, taskid=taskid, callername=callername)


def dbexecute2(sql, **kws):
	"""
	执行多条sql
	某条执行失败返回失败信息
	否则返回'success'
	"""
	taskid=kws['taskid']
	callername=kws['callername']

	if taskid is None:
		return 'error', 'taskid为空'
	
	print('调用内置函数=>dbexecute2', taskid)
	d = []
	try:
		sql = sql.replace('@@','$#$')
		if re.search('@.*(;.*@)?', sql) is not None:
			sqls1 = re.split("@", sql)
			for i in range(len(sqls1)):
				if i == 0:
					continue
				else:
					# print(sqls1[i].split(";")[0])
					sqls1[i - 1] += "@" + sqls1[i].split(";")[0]
					sqls1[i] = sqls1[i].split(";", 1)[-1]
			if sqls1[-2].endswith(sqls1[-1]):
				sqls1.pop()
			for sql in sqls1:
				if '@' in sql:
					sqls = sql.split("@")[0].split(";")
					conname = sql.split('@')[1]
					for sql in sqls:
						if sql!='':
							res, msg = dbexecute("%s@%s" % (sql, conname), taskid=taskid, callername=callername)
							print('执行结果=>', (res, msg))
							if res != 'success':
								return res, msg
							d.append(str(msg))
				elif '@' not in sql:
					sqls = sql.split(";")[:-1] if sql.endswith(";") else sql.split(";")
					dbnamecache = get_top_common_config(taskid)
					for sql in sqls:
						if sql != '':
							res, msg = dbexecute("%s@%s" % (sql, dbnamecache), taskid=taskid, callername=callername)
							print('执行结果=>', (res, msg))
							if res != 'success':
								return res, msg
							d.append(str(msg))
			return 'success', '+'.join(d)
		elif re.search('@', sql) is None:
			sqls2 = sql.split(";")[:-1] if sql.endswith(";") else sql.split(";")
			dbnamecache = get_top_common_config(taskid)
			for sql in sqls2:
				if sql != '':
					res, msg = dbexecute("%s@%s" % (sql, dbnamecache), taskid=taskid, callername=callername)
					print('执行结果=>', (res, msg))
					if res != 'success':
						return res, msg
					d.append(str(msg))
			return 'success', '+'.join(d)
	
	except:
		print(traceback.format_exc())
		return 'error', '执行内置函数报错sql[%s] error[%s]' % (sql, traceback.format_exc())



def getDate(**kws):
    '''
    返回当前的日期格式如2017-08-18
    '''
    return str(time.strftime("%Y-%m-%d"))


def getNow(**kws):
    '''
    返回时间格式如2019-09-01 12:23:15
    '''
    now = str(datetime.datetime.now())
    return "%s-%s-%s %s:%s:%s" % (now[:4], now[5:7], now[8:10], now[11:13], now[14:16], now[17:19])


def getSomeDate(**kws):
    '''
    返回基于当前时间的前后几天时间,默认格式2019-12-09
    参数1(num)-1表示前一天,2表示后两天
    参数2(format)控制返回时间格式 默认'%Y-%m-%d'
    
    '''
    num=kws.get('num',1)
    format=kws.get('format','%Y-%m-%d')

    num = int(num)
    numday = datetime.timedelta(days=abs(num))
    today = datetime.date.today()
    v = None
    
    if (num > 0):
        v = datetime.datetime.strftime(today + numday, format)
    else:
        v = datetime.datetime.strftime(today - numday, format)
    
    return v


def createPhone(**kws):
    '''
    说明：随机生成手机号
    :return: 手机号
    '''
    prelist = ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139", "147", "150", "151", "152", "153",
               "155", "156", "157", "158", "159", "186", "187", "188"]
    return random.choice(prelist) + "".join(random.choice("0123456789") for i in range(8))


def createTenantCode(**kws):
    '''
    返回随机8位数
    '''
    return "".join(random.choice("0123456789") for i in range(8))


def createTransNo(**kws):
    '''
    createTransNo： 随机生成流水号
     参数：name 为字符串，此处表示英文名
     返回：name+当前时间（月日时分秒）+随机数字      共16位

    '''
    name=kws.get('name','')
    if name != None:
        n = 16 - len(name)
    else:
        n = 16
    nowtime = time.strftime("%m%d%H%M%S")
    if n < 10:
        nowtime = nowtime[:n]
    n = n - len(nowtime)
    return name + nowtime + ''.join(random.choice("0123456789") for i in range(n))


def createReqSeqID(**kws):
    '''
    createReqSeqID：随机生成批次号
    参数：name为字符串，此处表示英文名
    返回：name+当前时间（年月日时分秒，若name过长则省略年）+数字    共30位
    '''
    name=kws.get('name','')

    n = 30 - len(name)
    if n >= 14:
        nowtime = time.strftime("%Y%m%d%H%M%S")
    else:
        nowtime = time.strftime("%m%d%H%M%S")
        if n < 10:
            nowtime = nowtime[:n]
    n = n - len(nowtime)
    return name + nowtime + ''.join(random.choice("0123456789") for i in range(n))


def createOrgName(**kws):
    '''返回一个随机组织名称 形式如组织_随机数
    '''
    return '组织' + str(random.randint(0, 50))


def createRoleName(**kws):
    '''返回一个角色名称 形式如角色_随机数
    '''
    return '角色' + str(random.randint(0, 50))


def sleep(esc,**kws):
    '''
    休眠函数
    参数:休眠时间 s
    '''
    time.sleep(esc)

def check_response_list_row_count(response_text,key,count,**kws):
    '''
    校验返回json指定路劲列表大小是否和预期一致
    '''
    from manager.builtin import cout
    from manager.utils import JSONParser
    jp=JSONParser(response_text)
    actioncount=len(jp.getValue(key))
    cout('校验返回json中包含列表长度  期望={} 实际={}'.format(count,actioncount),**kws)
    return True if actioncount==count else False


def local_to_ftp(filename, ip, port, username, password, remotedir, **kws):
    '''
    本地文件上传ftp
        例如: local_to_ftp('本地文件','10.22.22.1',8021,'pt','pt123','/bank')
    '''
    from .myspace import SpaceMeta
    taskid=kws.get('taskid',None)
    callername=kws.get('callername',None)
    status, msg = SpaceMeta.local_to_ftp(filename, ip, port, username, password, remotedir, callername)
    cout(msg, taskid=taskid, callername=callername)
    return (status, msg)


def ftp_to_local(ip, port, username, password, remotefile,**kws):
    '''
    ftp文件下载
    '''
    from .myspace import SpaceMeta
    taskid=kws.get('taskid',None)
    callername=kws.get('callername',None)

    status, msg = SpaceMeta.ftp_to_local(ip, port, username, password, remotefile, callername)
    cout(msg, taskid=taskid, callername=callername)
    return (status, msg)


def local_file_check(filename, templatename, checklist, **kws):
    '''
    本地文件使用报文模板进行数据校验
    '''
    from .myspace import SpaceMeta

    taskid=kws.get('taskid',None)
    callername=kws.get('callername',None)
    
    cout('开始校验文件[%s]' % filename, taskid=taskid, callername=callername)
    cout('使用的报文模板[%s]' % templatename, taskid=taskid, callername=callername)
    cout('待校验字段[%s]' % '|'.join(checklist), taskid=taskid, callername=callername)
    status, msg = SpaceMeta.local_file_check(filename, templatename, checklist, callername)
    return (status, msg)


def remote_xml_read(xmlcontent,key,**kws):
    '''
    融汇远程xml文件校验
    '''
    from manager.invoker import XMLParser

    #
    xmlmsg=xmlcontent['data']['msg']
    pv=kws.get('p')
    if pv:
        if pv==xmlmsg[0:5]:
            #cout('msg前置数字串校验通过',taskid=kws['taskid'],callername=kws['callername'])
            pass
        else:
            return ('fail','msg前置数字串校验失败 实际值：%s'%xmlmsg[0:5])

    xmlmsg=xmlmsg[xmlmsg.index('<'):]
    p=XMLParser(xmlmsg)
    return p.getValue(key)

def response_match_db(response_text,checkmap,**kws):
    '''校验项和数据库值是否一致 {{RESPONSE_TEXT}}必填,checkmap必填,is_json_response可选
    '''
    from .invoker import JSONParser,XMLParser
    try:
        taskid=kws.get('taskid',None)
        callername=kws.get('callername',None)
        is_json_check=kws.get('is_json_response',True)
        response_text=str(response_text)
        p=JSONParser(response_text) if is_json_check else XMLParser(response_text)

        cout('response_text=>',response_text,taskid=taskid,callername=callername)
        for ak in checkmap:
            right=checkmap[ak]
            if str(checkmap[ak]).strip().startswith('select'):
                right=dbexecute(checkmap[ak],**kws)
            left=p.getValue(ak)
            if str(right)==str(left):
                continue;
            else:
                cout('%s=%s校验失败, %s!=%s'%(ak,checkmap[ak],left,right),**kws)

                return False
    except:
        cout(traceback.format_exc(),taskid=taskid,callername=callername)
        return False
    return True



def  tuipiao_file_check(timeflag,t_templatename,td_templatename,t_checklist,td_checklist,**kws):
    '''
    退票场景文件校验
    '''
    from datetime import datetime
    from ftplib import FTP
    import time,io
    import os, traceback, subprocess
    from manager.pa import MessageParser
    from manager.builtin import cout
    w=kws.get('wait',None)
    wait=int(w) if w else 5

    try:
        time.sleep(wait)
        ip,port,username,password='10.60.45.174',21,'AS330106','123456'
        callername=kws['callername']
        ######
        ftp = FTP()
        ftp.set_debuglevel(0)
        ftp.connect(ip, int(port))
        ftp.login(username, password)

        ###
        #today_lt_file='.'.join([str( datetime.now())[:10],'lt']).replace('-', '')
        today_lt_file='20200401.lt'
        today_lt_file_path='/tenant43/AS330106/upload/'+today_lt_file
        cout('使用的远程.lt文件:',today_lt_file_path,**kws)

        ###
        buf = io.StringIO()
        ftp.retrlines("RETR "+ today_lt_file_path, buf.write)
        t_file_name=[x for x in buf.getvalue().split('.t') if x][-1]+'.t'
        td_file_name=t_file_name+'d'

        buf2 = io.StringIO()
        today_td_file_path='/tenant43/AS330106/upload/'+td_file_name
        cout('使用的远程.td文件:',today_td_file_path,**kws)
        ftp.retrlines("RETR "+ today_td_file_path, buf2.write)

        today_t_file_path='/tenant43/AS330106/upload/'+t_file_name

        ####下载.t文件 解密解压 check
        status,msg=ftp_to_local(ip, port, username, password,today_t_file_path,**kws)
        if status is not 'success':
            cout('下载文件{}异常'.format(today_lt_file_path),**kws)
            return False

        local_t_file_path= os.path.join(os.path.dirname(__file__), 'storage', 'private', 'File', callername,
                                 t_file_name)

        toolpath=os.path.join(os.path.dirname(__file__), 'storage', 'public', 'tools','jiemi_rh_20200326.jar')

        command = 'java -jar %s %s' % (toolpath,local_t_file_path)

        p = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE)
        p.wait()
        decryptresult = p.communicate()[0].decode('GBK').replace('\n', '||')

        cout('解密解压[%s]获得文件[%s]内容:\n%s' % (command,local_t_file_path, decryptresult),**kws)
        
        parser = MessageParser.get_parse_config(t_templatename)
        if parser[0] is not 'success':
            return parser
        mp = MessageParser(parser[1], decryptresult, t_checklist)
        checkresult = mp.compute()
        cout('.t 本地文件校验计算明细=>', checkresult,**kws)   
        for exp in checkresult:
            if checkresult[exp][0] is not 'success':
                return checkresult[exp]

        ##.td check
        parser = MessageParser.get_parse_config(td_templatename)
        if parser[0] is not 'success':
            return parser

        cur_td_file_content=buf2.getvalue()
        mp = MessageParser(parser[1], cur_td_file_content, td_checklist)
        checkresult = mp.compute()
        cout('.td 本地文件校验计算明细=>', checkresult,**kws)

        for exp in checkresult:
            if checkresult[exp][0] is not 'success':
                return checkresult[exp]

        ftp.close()
        return True
    except:
        cout('退票校验异常:{}'.format(traceback.format_exc()),**kws)
        return False
