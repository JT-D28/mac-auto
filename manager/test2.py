def now_prefix(**prefixname):
    import datetime
    now = str(datetime.datetime.now())
    res="%s-%s-%s %s:%s:%s" % (now[:4], now[5:7], now[8:10], now[11:13], now[14:16], now[17:19])
    if prefixname.get('name'):
        res=prefixname.get('name')+res

    return res



print(now_prefix(name='3006'))
print(now_prefix())