def getDateByoffset(day):
    '''
    根据现在时间和设定偏移量获取标准时间
    :return:如1970-01-01 00:00:00
    '''
    import datetime
    return (datetime.datetime.now() + datetime.timedelta(days=day)).strftime("%Y-%m-%d %H:%M:%S")