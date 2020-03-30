import time,random
def createTransNo(**kws):
    '''可传参数name
    '''
    name=(lambda:'' if not kws.get('name') else kws.get('name'))()
    n=16-len(name)

    nowtime=time.strftime("%m%d%H%M%S")
    if n<10:
        nowtime=nowtime[:n]
    n=n-len(nowtime)
    return name+nowtime+''.join(random.choice("0123456789") for i in range(n))