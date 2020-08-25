import  time
def getmsg(v):
    dw='sec'
    if v<60:
        dw='sec'
    elif v<60*60:
        dw='min'
    elif v<60*60*24:
        dw='h'
    elif v<365*24*3600:
        dw='d'
    while True:
        last=v
        v=v//60

        if v==0:
            return '{}{}'.format(last,dw)


print(getmsg(3600*24))