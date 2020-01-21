def getAmount(startamount=0.01,endamount=4999.99):
    import Personal
    if startamount >= endamount:
        endamount += startamount
    a=random.uniform(int(startamount),int(endamount))
    return str(round(a,2))