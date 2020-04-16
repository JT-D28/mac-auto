def getdata(parame,**kws):
    import hashlib,base64
    import os
    from OpenSSL.crypto import load_privatekey, FILETYPE_PEM, sign
    from hashlib import sha1,md5
    from urllib import parse
    from manager.builtin import cout

    signStr=''
    signKey = "c9b576e12251f3a7f30c548672fcbd9a"
    pemfilename='SendPrivateKey.pem'

    headdata=parame['mw']
    # print(headdata)
    #del headdata['Signature']

    keys = list(headdata.keys())
    keys = sorted([k for k in keys if headdata[k]!=''])
    # print(keys)

    signStr = '_'.join([headdata[k] for k in keys])+'_'+signKey
    cout('验签加密明文：',signStr,**kws)
    ##加密过程
    hl=md5()
    hl.update(signStr.encode("GBK"))
    afmd=hl.hexdigest()
    prikeypath=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),'File',kws['callername'],pemfilename)
    key = load_privatekey(FILETYPE_PEM, open(prikeypath).read())
    signature= sign(key, afmd, 'sha1')  
    paramsvalue = base64.b64encode(signature)
    sign0=bytes.decode(paramsvalue) 
    cout('计算验签为：',sign0,**kws)
    headdata['Signature']=str(sign0)
    cout('最终Data参数计算的报文为：',headdata,**kws)
    sss="N/GbG+wCrC/pw6GhmG/igAecktcoktCyMVBloVTWgYo9jY2XiJ7To5EvcgXMOomRqPkT7FM1w8ESoZrq9ro8bLKV06/3fkZCMjqWJZrjF8chQ2sXEonmoPlJWUnwyv1n5M+hZ4SPSu7+enAWxpZoQhNl2jcdznZwj2W814wOE5Y="
    cout('正确的验签码为:',sss,**kws)

    str_=str(headdata).replace('\n','').replace(' ','').replace("'", '"')
    return parse.quote(base64.b64encode(str_.encode()).decode())
    #return base64.b64encode(str_.encode()).decode()
