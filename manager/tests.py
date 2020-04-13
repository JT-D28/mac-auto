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
print('signStr:',signStr)
##加密过程
hl=md5()
hl.update(signStr.encode("GBK"))
afmd=hl.hexdigest()


prikeypath=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),'File',kws['callername'],pemfilename)
key = load_privatekey(FILETYPE_PEM, open(prikeypath).read())
signature= sign(key, afmd, 'sha1')  
paramsvalue = base64.b64encode(signature)
print('ss1=>',bytes.decode(paramsvalue) )
return bytes.decode(paramsvalue) 




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