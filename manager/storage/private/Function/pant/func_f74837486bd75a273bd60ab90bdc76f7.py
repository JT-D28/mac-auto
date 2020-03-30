def createTransNo(name=''):
    import time,random
    if name !=None:
        n=16-len(name)
    else:
        n=16
    nowtime=time.strftime("%m%d%H%M%S")
    if n<10:
        nowtime=nowtime[:n]
    n=n-len(nowtime)
    return name+nowtime+''.join(random.choice("0123456789") for i in range(n))