import datetime


def now():
    '''
    返回时间格式如2019-09-01 12:23:15
    '''
    now = str(datetime.datetime.now())
    return "%s-%s-%s %s:%s:%s"%(now[:4],now[5:7],now[8:10],now[11:13],now[14:16],now[17:19])
