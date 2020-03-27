def now():
    import datetime
    d2=datetime.datetime.now()
    now = str(d2)
    return now[:4]+now[5:7]+now[8:10]+now[11:13]+now[14:16]+now[17:19]+now[20:22]