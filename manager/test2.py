def createWebApiSignature(parame,**kws):
    import hashlib,base64
    from hashlib import sha1,md5
    import json
    from typing import Dict, Any
    from collections import namedtuple

    signStr=''
    signKey = "c9b576e12251f3a7f30c548672fcbd9a"
    pemfilename='SendPrivateKey.pem'

    headdata=parame['mw']
    # print(headdata)
    #del headdata['Signature']

    keys = list(headdata.keys())
    keys = sorted([k for k in keys if headdata[k]!=''])
    # print(keys)

    signStr = '_'.join([headdata[k] for k in keys])+signKey
    print('signStr:',signStr)
    ##加密过程
    hl=md5()
    hl.update(signStr.encode("GBK"))
    afmd=hl.hexdigest()
    prikeypath=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),'File',kws['callername'],pemfilename)
    key = load_privatekey(FILETYPE_PEM, open(prikeypath).read())
    signature= sign(key, afmd, 'sha1')  
    paramsvalue = base64.b64encode(signature)
    sign0=bytes.decode(paramsvalue) 

    headdata['Signature']=str(sign0)

    str_=str(headdata).replace('\n','').replace(' ','').replace("'", '"')
    return base64.b64encode(str_.encode()).decode()







print(createWebApiSignature(ak))

# u="测试_车险缴费_00_330123131231313146_0_12345678_张三_QT330002_0_0_127.0.0.1_7551000001_EAdsaqSy1dD9Fe0DQ==_http://114.55.25.39:2837_55792171_1586324988_17758176904_000000_20200418175525_20200407155525_1_c9b576e12251f3a7f30c548672fcbd9a"
# print(len(u.split('_')))