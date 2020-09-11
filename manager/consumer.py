#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-08-30 15:07:14
# @Author  : Blackstone
# @to      :
import os

from channels.generic.websocket import WebsocketConsumer
import json, threading, time
import redis,traceback
from django.conf import settings

from ME2.settings import BASE_DIR
from manager.context import Me2Log as logger
from manager.operate.mongoUtil import Mongo
from manager.operate.redisUtils import RedisUtils



class ChatConsumer(WebsocketConsumer):

    def sendmsg(self):
        while True:
            # print('check.')
            time.sleep(0.1)
            t = self.con.rpop('list')
            if t is not None:
                print(t.decode())
                self.send(text_data=t.decode())

    def connect(self):
        # 连接时触发
        self.accept()
        # self.con = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        print('收到一个websocket连接.')
        # threading.Thread(target=self.sendmsg).start()

    def disconnect(self, code):
        # 关闭连接时触发
        pass

    def receive(self, text_data=None, bytes_data=None):
        # 收到消息后触发
        pass


class PkgSaveConsumer(WebsocketConsumer):

    '''
    包存入
    '''
    def __init__(self,args):
        super(PkgSaveConsumer, self).__init__(args)
        self._flag = False

    def teminate(self):
        pass

    def save(self):
        while 1:
            self.send('live')
            time.sleep(5)

    def connect(self):
        print('receive connect...')
        self.accept()
        pool = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)
        #self.con = redis.Redis(connection_pool=pool)
        self.con=redis.Redis(host=settings.REDIS_HOST,port=settings.REDIS_PORT,decode_responses=True)
        logger.info('con状态:',self.con.ping())
        # threading.Thread(target=self.save).start()


    def disconnect(self,code):
        self.teminate()
        logger.info('PkgSaveConsumer服务端断连 code={}=='.format(code))


    def receive(self,text_data=None, bytes_data=None):
        # logger.info('$$'*2000)

        logger.info('PkgSaveConsumer receive==')
        try:
            if text_data.startswith('mclient::ready'):
                self.username=text_data.split('::')[2]
                ##清除账户历史数据
                key = 'pkg::save::%s' % self.username
                self.con.delete(key)
                logger.info('用户{}清除历史录制数据'.format(self.username))

            else:
                key='pkg::save::%s'%self.username
                self.con.lpush(key, text_data)
                logger.info('<redis存入>{} => {}'.format(key,text_data))
                logger.info('cur queue size:',self.con.llen(key))
        except:
            logger.error('receive异常:',traceback.format_exc())


class PkgReadConsumer(WebsocketConsumer):
    '''
    包读取
    '''
    def __init__(self,args):
        super(PkgReadConsumer, self).__init__(args)
        self._flag = False
        self.username=None

    def teminate(self):
        self._flag = True

    def sendmsg(self):
        if self.username is None:
            return
        key='pkg::save::%s'%self.username
        while True:
            if self._flag:
                logger.info(' PkgReadConsumer结束发送消息')
                break;
            key_value_size=self.con.llen(key)

            if key_value_size>0:
                msg=self.con.rpop(key)
                #msg=None
                if msg:
                    logger.info('<redis读>', msg)
                    self.send(msg)
            # else:
            #     logger.info('<redis读>key_value_size=0')
            time.sleep(0.03)

    def connect(self):
        self.accept()
        pool = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)
        self.con = redis.Redis(connection_pool=pool)

    def disconnect(self,code):
        self.teminate()
        logger.info('PkgReadConsumer服务端断连 code={}=='.format(code))

    def receive(self,text_data=None, bytes_data=None):
        logger.info('PkgReadConsumer receive ...')
        if text_data.startswith('pkg::read'):
            self.username=text_data.split('::')[2]

        self.thread = threading.Thread(target=self.sendmsg)
        self.thread.setDaemon(True)
        self.thread.start()




class ConsoleConsumer(WebsocketConsumer):
    # console展现过
    __handled = []

    def __init__(self, args):
        super(ConsoleConsumer, self).__init__(args)
        self._flag = False

    def terminate(self):
        self._flag = True

    def reset(self):
        try:
            self._flag = False
            if self.username:
                del self.username
            if self.taskid:
                del self.taskid
        except:
            pass

    def sendmsg(self, username, taskid):
        try:
            oldcount = 0
            while 1:
                newcount = Mongo.tasklog(taskid).count_documents({})
                if newcount != oldcount:
                    res = Mongo.tasklog(taskid).find({},{"info":1,"_id":0}).limit(newcount - oldcount).skip(oldcount)
                    for i in res:
                        self.send(i['info'])
                        if '结束计划' in i['info']:
                            raise Exception
                        time.sleep(0.01)
                    oldcount = newcount
                time.sleep(0.05)
        except:
            pass

        # key = self.con.keys("console.msg::%s::%s" % (username, taskid))
        # if not key:
        #     self.send('hasRead')
        #     return
        # else:
        #     key = key[0]
        # print("查询到的任务id=>%s" % key)
        # while True:
        #     if self._flag:
        #         print("================结束向用户[%s]控制台发送消息===============" % username)
        #         break
        #     sep = self.con.rpop(key)
        #     if sep:
        #         self.send(sep)
        #     time.sleep(0.03)

    def connect(self):
        # 连接时触发
        self.accept()
        # pool = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)
        # redis.Redis(connection_pool=pool)
        # self.con = RedisUtils()

    # print("connect=>",self.con)
    # print('consolemsg 连接.=>',self.con.keys("console.msg::%s*"%self.username))

    def disconnect(self, code):
        # 关闭连接时触发
        print("用户[%s]关闭console 结束会话" % self.username)
        # ConsoleConsumer.__handled = ConsoleConsumer.__handled + self.keys
        # print("当前过滤key值=>", ConsoleConsumer.__handled)
        self.terminate()

    def receive(self, text_data=None, bytes_data=None):
        # 收到消息后触发
        # self.username=text_data

        if text_data.startswith("console.msg::read"):
            self.reset()
            get = text_data.split("::")
            self.username = get[2]
            self.taskid = get[3]
            print("receive=>", self.username, self.taskid)

            self.thread = threading.Thread(target=self.sendmsg, args=(self.username, self.taskid))
            self.thread.setDaemon(True)
            self.thread.start()


class logConsumer(WebsocketConsumer):
    def __init__(self, args):
        super(logConsumer, self).__init__(args)

    def sendmsg(self, taskid, is_running):
        logname = BASE_DIR + "/logs/" + taskid + ".log"
        done_msg = '结束计划'
        if os.path.exists(logname):
            with open(logname, 'r', encoding='utf-8') as f:
                if is_running == '0':
                    log_text = f.readlines()
                    count = len(log_text)
                    self.send(text_data=json.dumps({'data': log_text, 'count': count}))
                    self.disconnect()
                else:
                    while self.con==1:
                        log_text = f.readlines()
                        count = len(log_text)
                        self.send(text_data=json.dumps({'data': log_text, 'count': count}))
                        for i in log_text:
                            if done_msg in i:
                                return
                        time.sleep(0.1)

    def receive(self, text_data):
        is_running = text_data.split("::")[0]
        self.is_running = '1' if is_running != '0' else '0'
        self.taskid = text_data.split("::")[1]
        print("receive=>", self.taskid)
        print("receive=>", self.is_running)
        self.con = 1
        self.thread = threading.Thread(target=self.sendmsg, args=(self.taskid, self.is_running))
        self.thread.setDaemon(True)
        self.thread.start()

    def disconnect(self, code=None):
        self.con = 0
        print("%s 的日志打印结束" % self.taskid)
