def getdata_ryb(signkey,parame,**kws):
    import hashlib,base64
    import os
    from OpenSSL.crypto import load_privatekey, FILETYPE_PEM, sign
    from hashlib import sha1,md5
    from urllib import parse
    from manager.builtin import cout

    signStr=''
    #signKey = "712d2b45e3884624b2124b4ccfb59ff2"
    pemfilename='SendPrivateKey.pem'

    headdata=parame['mw']
    # print(headdata)

    if headdata['Signature'] != '':
     del headdata['Signature']
     keys = list(headdata.keys())
     keys = sorted([k for k in keys if headdata[k]!=''])
     cout('keys=',keys,**kws)
    # print(keys)

     signStr = '_'.join([str(headdata[k]) for k in keys])+'_'+signKey
     cout('验签加密明文：',signStr,**kws)
    ##加密过程
     hl=md5()
     hl.update(signStr.encode("GBK"))
     afmd=hl.hexdigest()
     cout('MD5hex：',afmd,**kws)
     prikeypath=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),'File',kws['callername'],pemfilename)
     key = load_privatekey(FILETYPE_PEM, open(prikeypath).read())
     signature= sign(key, afmd, 'sha1')
     paramsvalue = base64.b64encode(signature)
     sign0=bytes.decode(paramsvalue)
     cout('计算验签为：',sign0,**kws)
     headdata['Signature']=str(sign0)
     str_=str(headdata).replace('\n','').replace("'", '"')
     cout('最终Data参数计算的报文明文为：',str_,**kws)
     param=parse.quote(base64.b64encode(str_.encode()).decode())
     cout('最终Data参数计算的报文为：',param,**kws)
     param_=parse.quote(param)
     cout('最终Data参数计算urlencode的报文为：',param_,**kws)
     return param_
    
    elif headdata['Signature'] == '':
     str_ = str(headdata).replace('\n', '').replace("'", '"')
     cout('最终Data参数计算的报文明文为：', str_, **kws)
     param = parse.quote(base64.b64encode(str_.encode()).decode())
     cout('最终Data参数计算的报文为：', param, **kws)
     param_ = parse.quote(param)
     cout('最终Data参数计算urlencode的报文为：', param_, **kws)
     return param_