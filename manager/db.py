#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-08-29 10:41:39
# @Author  : Blackstone
# @to      :

# coding=utf-8
import re
import time
import logging, traceback
import os
from manager import models
from .context import get_top_common_config, viewcache

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


class Mysqloper:
    _pool = {}
    
    def __init__(self):
        
        self.sqlmax = 499
        self.sqlcount = 0
    
    def db_connect(self, configname):
        conname = configname
        if conname is None:
            raise RuntimeError('传入配置错误 未知数据库连接名！')
        
        print('===查询和使用数据库[%s]的配置信息' % (configname))
        
        # c=Mysqloper._pool.get(str(conname),None)
        c = None
        if c is not None:
            
            print("=>从连接池获取到一个可用配置 =>")
            conn = c
            return ('success', conn)
        
        else:
            
            try:
                
                # print(len(conname),len(conname.strip()))
                dbcon = models.DBCon.objects.get(description=conname.strip())
                
                self.dbtype = dbcon.kind
                self.dbname = dbcon.dbname
                # oracle不需要这两项
                self.host = dbcon.host
                self.port = dbcon.port
                #
                self.user = dbcon.username
                self.pwd = dbcon.password
                
                # print("=>没查到可用配置,准备新配一个")
                print("数据库类型=>", self.dbtype)
                print("数据库名(服务名|SID)=>", self.dbname)
                print("数据库地址=>", self.host, self.port)
                print("数据库账号=>", self.user, self.pwd)
                
                if self.dbtype.lower() == 'mysql':
                    import pymysql
                    
                    conn = pymysql.connect(db=self.dbname, host=self.host,
                                           port=int(self.port),
                                           user=self.user,
                                           password=self.pwd,
                                           charset='utf8mb4')
                
                
                elif self.dbtype.lower() == 'oracle_servicename':
                    import cx_Oracle
                    
                    dsn = cx_Oracle.makedsn(self.host, int(self.port), service_name=self.dbname)
                    conn = cx_Oracle.connect(self.user, self.pwd, dsn)
                
                elif self.dbtype.lower() == 'oracle_sid':
                    import cx_Oracle
                    dsn = cx_Oracle.makedsn(self.host, int(self.port), sid=self.dbname)
                    conn = cx_Oracle.connect(self.user, self.pwd, dsn)
                
                elif self.dbtype.lower() == 'db2':
                    import ibm_db_dbi
                    conn = ibm_db_dbi.connect("PORT=" + str(self.port) + ";PROTOCOL=TCPIP;",
                                              user=self.user,
                                              password=self.pwd,
                                              host=self.host,
                                              database=self.dbname)
                
                elif self.dbtype.lower() == 'pgsql':
                    import psycopg2 as pg2
                    conn = pg2.connect(database=self.dbname, user=self.user, password=self.pwd, host=self.host,
                                       port=int(self.port))
                
                print("连接成功！")
                #:
                Mysqloper._pool[str(conname)] = conn
                
                return ('success', conn)
            except Exception as e:
                print("数据库配置名=>", conname)
                error = traceback.format_exc()
                print(error)
                return ('error', ("数据库连接失败 请检查数据库[%s]是否正确配置" % (configname, error)))
    
    def db_commit(self):
        try:
            if self.conn:
                self.conn.commit()
        except:
            pass
    
    def db_close(self):
        try:
            [con.close() for con in Mysqloper._pool.values()]
        
        except  Exception as ee:
            return ('关闭数据库连接出现异常，请确认')
    
    def db_execute2(self, sql, taskid=None, callername=None):
        
        reslist = []
        print('db_execute2执行：', sql)
        print('##' * 100)
        try:
            sqls = sql.split("@")[0].split(";")
            conname = sql.split('@')[1]
            for sql in sqls:
                # print(type(sql),sql)
                # print(type(conname),conname)
                res, msg = self.db_execute("%s@%s" % (sql, conname), taskid=taskid, callername=callername)
                # print(sql)
                reslist.append(msg)
                if res is not 'success':
                    return res, msg
            return ('success', str(reslist))
        
        except:
            print(traceback.format_exc())
            return ('error', 'sql[%s]执行报错[%s]@' % (sql, traceback.format_exc()))
    
    def db_execute(self, sql, taskid=None, callername=None):
        
        """
		返回(sucess/fail/error,结果/消息)
		sql查询返回结果
		非查询返回影响条数
		"""
        sqlresult, error = None, ''
        conname = None
        # 判断当前连接是否正常
        try:
            ql = sql.split("@")
            sql = ql[0]
            conname = ql[1]
            
            dbnamecache = get_top_common_config(taskid)
            if dbnamecache == conname:
                conname = dbnamecache
            
            msg, self.conn = self.db_connect(conname)
            if msg is not 'success':
                return (msg, self.conn)
            
            # self.db_commit()
            cur = self.conn.cursor()  # 获取一个游标
            sql = sql.replace(chr(13), '').replace(chr(10), '').strip()
            self.sqlcount += 1
            # print('sqlfda=>',sql,len(sql),len(sql.strip()))
            cur.execute(str(sql))
            
            ##查询sql时候
            if re.match(r'(select).*(from).+(where){0,1}.*', sql.lower()) or re.match(r'(select).*(curdate).*',
                                                                                      sql.lower()):
                # for cs in range(15):
                data = cur.fetchall()
                data = list(data)
                print("sql[%s]查询结果=>%s" % (sql.lower(), data))
                
                if data and len(data) > 0:
                    # [('f1','f2'),()]
                    l1 = len(data)
                    l2 = len(data[0])
                    
                    ##单zu数据单字段
                    if l1 == 1 and l2 == 1:
                        sqlresult = str(data[0][0])
                    ##多字段 or 多组数据
                    else:
                        r = []
                        
                        return ('error', "sql[%s]查询结果返回存在多组数据或多个字段 不支持" % sql)
                
                elif sqlresult == None:
                    return ('success', '')
                
                else:
                    return ('fail', '查询结果为空[%s]' % sql)
            
            ##非查询sql
            else:
                sqlresult = cur.rowcount
                self.db_commit()
            
            msg = "[<span style='color:#009999;'>%s</span>]执行sql <span style='color:#009999;'>%s</span> 结果为 <span style='color:#009999;'>%s</span>" % (
                conname, sql, sqlresult)
            # print(msg)
            viewcache(taskid, callername, None, msg)
            
            cur.close()
            
            return ('success', sqlresult)
        
        except Exception as ee:
            # traceback.print_exc()
            # return RuntimeError('执行sql[%s],发生未知错误[%s].'%(sql,str(ee)))
            print(traceback.format_exc())
            return ('error', "数据库[%s]执行sql[%s]发生异常:\n[%s]" % (conname, sql, traceback.format_exc()))


class DBError(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr(self.value)
