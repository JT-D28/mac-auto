def createSignature(key,**kws):
    from hashlib import sha512
    keys=list(kws.keys())
    keys.sort()
    #print(keys)
    valstr=""
    for k in keys:
        if kws[k] !=None:
            valstr +=str(kws[k])+'_'
    valstr +=key
    hash=sha512()
    hash.update(valstr.encode('utf-8'))
    Signature=hash.hexdigest().upper()
    return Signature