def createSignatureWebApi(key,pemfilename,**kws):
    import os,base64

    from OpenSSL.crypto import load_privatekey, FILETYPE_PEM, sign
    from hashlib import md5

    keys=list(kws.keys())
    keys.sort()


    #print(keys)
    valstr=""
    for k in keys:
        if kws[k] !=None:
            valstr +=str(kws[k])+'_'
    valstr +=key
    hl=md5()
    hl.update(valstr.encode('GBK'))
    afmd=hl.hexdigest()
    prikeypath=os.path.join(os.path.dirname(os.path.dirname(__file__)),'keys',pemfilename)
    key = load_privatekey(FILETYPE_PEM, open(prikeypath).read())
    Signature= sign(key, afmd, 'sha1')

    paramsvalue = base64.b64encode(Signature)
    # print(paramsvalue)
    return bytes.decode(paramsvalue)
