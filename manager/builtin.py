#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-10-11 14:31:32
# @Author  : Blackstone
# @to      :
import re
import traceback,time,datetime,random

from .context import get_top_common_config
from .db import Mysqloper


def dbexecute(sql,taskid=None,callername=None):
    """
    执行单条sql
    单字段查询语句返回查询结果,不支持多字段
    非查询语句返回执行后影响条数

    """
    op = Mysqloper()
    if re.search('@', sql) is None:
        sql = sql.split(";")[:-1] if sql.endswith(";") else sql.split(";")[0]
        dbnamecache = get_top_common_config(taskid)
        print("调用内置函数=>dbexecute \nsql=>", sql)
        return op.db_execute("%s@%s" % (sql, dbnamecache),taskid=taskid,callername=callername)
    else:
        print("调用内置函数=>dbexecute \nsql=>",sql)
        return op.db_execute(sql,taskid=taskid,callername=callername)


def dbexecute2(sql,taskid=None,callername=None):
    """
    执行多条sql
    某条执行失败返回失败信息
    否则返回'success'
    """

    print('调用内置函数=>dbexecute2')
    d=[]

    try:
        if re.search('@.*(;.*@)?', sql) is not None:
            sqls1 = re.split("@", sql)
            for i in range(len(sqls1)):
                if i == 0:
                    continue
                else:
                    # print(sqls1[i].split(";")[0])
                    sqls1[i - 1] += "@" + sqls1[i].split(";")[0]
                    sqls1[i] = sqls1[i].split(";", 1)[-1]
            if '@' in sqls1:
                sqls1.pop()
            for sql in sqls1:
                if '@' in sql:
                    sqls = sql.split("@")[0].split(";")
                    conname=sql.split('@')[1]
                    for sql in sqls:
                        res,msg=dbexecute("%s@%s"%(sql,conname),taskid=taskid,callername=callername)
                        print('执行结果=>',(res,msg))
                        if res!='success':
                            return res,msg
                        d.append(str(msg))
                elif '@' not in sql:
                    sqls = sql.split(";")[:-1] if sql.endswith(";") else sql.split(";")
                    dbnamecache = get_top_common_config(taskid)
                    for sql in sqls:
                        res, msg = dbexecute("%s@%s" % (sql, dbnamecache), taskid=taskid, callername=callername)
                        print('执行结果=>', (res, msg))
                        if res != 'success':
                            return res, msg
                        d.append(str(msg))
            return 'success','+'.join(d)
        elif re.search('@', sql) is None:
            sqls2=sql.split(";")[:-1] if sql.endswith(";") else sql.split(";")
            dbnamecache = get_top_common_config(taskid)
            for sql in sqls2:
                res,msg=dbexecute("%s@%s"%(sql,dbnamecache),taskid=taskid,callername=callername)
                print('执行结果=>',(res,msg))
                if res!='success':
                    return res,msg
                d.append(str(msg))
            return 'success','+'.join(d)

    except:
        print(traceback.format_exc())
        return 'error','执行内置函数报错sql[%s] error[%s]'%(sql,traceback.format_exc())
    

def getDate():
    '''
    返回当前的日期格式如2017-08-18
    '''
    return str(time.strftime("%Y-%m-%d"))

def getNow():
    '''
    返回时间格式如2019-09-01 12:23:15
    '''
    now = str(datetime.datetime.now())
    return "%s-%s-%s %s:%s:%s"%(now[:4],now[5:7],now[8:10],now[11:13],now[14:16],now[17:19])

def getSomeDate(num=1,format='%Y-%m-%d'):
    '''
    返回基于当前时间的前后几天时间,默认格式2019-12-09
    参数1(num)-1表示前一天,2表示后两天
    参数2(format)控制返回时间格式 默认'%Y-%m-%d'
    
    '''
    num=int(num)
    numday= datetime.timedelta(days=abs(num))
    today = datetime.date.today()
    v=None

    if(num>0):
        v=datetime.datetime.strftime(today+numday,format)
    else:
        v=datetime.datetime.strftime(today-numday,format)

    return v


def createPhone():
    '''
    返回随机手机号
    '''
    prelist=["130","131","132","133","134","135","136","137","138","139","147","150","151","152","153","155","156","157","158","159","186","187","188"]
    return random.choice(prelist)+"".join(random.choice("0123456789") for i in range(8))