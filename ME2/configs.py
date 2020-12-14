import configparser
import os
import random
import string


confs = configparser.ConfigParser()
confs.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini'), encoding="utf-8")
conf = confs['useconfig']

#
ID = conf['ID']
dbtype = conf['dbtype']
ME2_URL = conf['ME2_URL']
DATABASES_NAME = conf['DATABASES_NAME']
DATABASES_USER = conf['DATABASES_USER']
DATABASES_PWD = conf['DATABASES_PWD']
DATABASES_HOST = conf['DATABASES_HOST']
DATABASES_PORT = conf['DATABASES_PORT']
REDIS_HOST = conf['REDIS_HOST']
REDIS_PORT = conf['REDIS_PORT']
REDIS_PASSWORD = conf['REDIS_PASSWORD']

##MONGODB配置
MONGO_HOST = conf['MONGO_HOST']
MONGO_PORT = conf['MONGO_PORT']

Consul_ADDR = conf['Consul_ADDR']
Consul_PORT = conf['Consul_PORT']
Fabio_ADDR = conf['Fabio_ADDR']

# 邮件服务器配置 SMTP
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 465
EMAIL_HOST_USER = '1090233097@qq.com'  # 邮箱帐号
EMAIL_sender_nick = 'me2'  # 名称
EMAIL_HOST_PASSWORD = 'vgzevlmbpbmgfefd'  # 邮箱密码
EMAIL_FROM = '1090233097@qq.com'  # 邮件发送者帐号

# 初次启动时创建管理员账号  用户名默认：admin
IS_CREATE_SUPERUSER = True
SUPERUSER_PWD = 'admin#fingard'

WorkerInfo = {
	"url": "http://"+ME2_URL,
	"dsn": "%s:%s@tcp(%s:%s)/%s?charset=utf8mb4&parseTime=True&loc=Local" % (
		DATABASES_USER, DATABASES_PWD, DATABASES_HOST, DATABASES_PORT, DATABASES_NAME),
	"mongo": "mongodb://%s:%s" % (MONGO_HOST, MONGO_PORT)
}
