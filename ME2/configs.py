# 数据库类型  sqlite3|mysql
dbtype = 'mysql'

# ME2 url地址
ME2_URL = '10.60.44.59:18007'

# 环境数据库配置  本地用 me2-local-test root 123456 10.60.44.59 3306
# mysql
DATABASES_NAME = 'me2-59'
DATABASES_USER = 'root'
DATABASES_PWD = '123456'
DATABASES_HOST = '10.60.44.59'
DATABASES_PORT = '3306'

# sqlite3 默认文件名为db.sqlite3


# redis配置
REDIS_HOST = '10.60.44.59'
REDIS_PORT = '6379'
REDIS_PASSWORD = ''

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
