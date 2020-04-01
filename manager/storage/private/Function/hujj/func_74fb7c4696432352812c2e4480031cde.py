def getRequestDataWithsignKey(parame):
    import hashlib
    import json
    from typing import Dict, Any
    from collections import namedtuple
    signKey = '8f5f5d93af2e4befb23af83c3a6cf210'
    signStr=''
    if parame is not None:
        print(parame)
        for key in parame.keys():
            if key == "requestHead":
                headdata = parame[key]
                #print(headdata)
                for value in headdata.keys():
                    if key == "sign":
                        signs = headdata.pop("sign")
                #heads = addMd5SignWithSignkey(headdata,signKey)

                keys = []
                # 按照参数名字升序排序
                for key in headdata:
                    keys.append(key)
                keys = sorted(keys)
                # print (keys)

                # 拿出相应key的值
                aa = []
                for key in keys:
                    aa.append(headdata[key])
                str = ''
                index = 0
                for s in aa:
                    index = index + 1
                    if index == len(aa):
                        str = str + s
                    else:
                        str = str + s + '_'

                signStr = str + '_' + signKey

                signature = hashlib.md5(signStr.encode('utf-8')).hexdigest()
                signStr = signature
                #print(signstr1)
        return signStr
    else:
        print('--- 请输入请求参数 ---')
        return ''