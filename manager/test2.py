<<<<<<< HEAD
import requests,re
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

class XMLParser():
    def __init__(self,data):
        self.root=ET.fromstring(str(data))

    def getValue(self,xpath):

        print('查找=>',xpath)
        result=''
        route_path=''
        chainlist=xpath.split('.')

        if len(chainlist)>1:
            chainlist.pop(0)
        else:
            pass

        for chain in chainlist:
            o=dict()
            index=None
            propname=None
            tagname=None
            ms=re.findall('\[(.*?)\]', chain)
            # print('ms=>',ms)
            kh=None

            for m in ms:
                try:
                    index=str(int(m))
                except:
                    propname=m

            tagname=re.sub(r'\[.+\]', '', chain)
            chain=re.sub('[.*?]', '', chain)

            route_path+='/'+tagname

            if index:
                route_path+='[%s]'%str(int(index)+1)
            else:
                route_path+='[1]'

            if propname:
                # print('search=>','.'+route_path)
                # print('res=>',self.root.find('.'+route_path).attrib)
                return self.root.find('.'+route_path).attrib.get(propname,'None')
        try:
            # print('search=>','.'+route_path)
            return self.root.find('.'+route_path).text
        except:
            return 'None'
url='http://10.60.44.222:3330/webservice/outService.ws?wsdl'
param=''
with open('request.txt',encoding='utf-8') as f:
    old=f.read()
    param=old

txt=requests.get(url=url,params=param,headers={"Content-type": "text/xml; charset=UTF-8;'SOAPAction':''"}).text

print(txt)
=======
import re
from hashlib import md5, sha512


def _md5(s):
	"""
	函数文件名标识
	"""
	new_md5 = md5()
	new_md5.update(s.encode(encoding='utf-8'))
	return new_md5.hexdigest()


def tzm_compute(src, pattern):
	"""
	计算方法特征码
	通过pattern从src字符串获取方法名和参数串计算特征码
	"""
	pool = [chr(x) for x in range(97, 123)]
	m = re.findall(pattern, src)
	funcname = m[0][0]
	paramlist = m[0][1].split(",")
	
	# 带关键字参数和可变参数的 都按a()计算
	# 参数带=好 记为关键参数 去除
	paramlist = [p for p in paramlist if not p.startswith('*') and not p.__contains__('=')]
	size = len(paramlist)
	paramstr = ",".join(pool[0:size])
	final = "%s(%s)" % (funcname, paramstr)
	print('final=>', final)
	
	return _md5(final)


def createSignature(key, **kws):
	from hashlib import sha512
	keys = list(kws.keys())
	keys.sort()
	# print(keys)
	valstr = ""
	for k in keys:
		if kws[k] != None:
			valstr += str(kws[k]) + '_'
	valstr += key
	hash = sha512()
	hash.update(valstr.encode('utf-8'))
	Signature = hash.hexdigest().upper()
	return Signature


print(createSignature('wwww', AppVersion='1.11.0', UserInfoURID='', EnterpriseNum='AC530001', PhoneNum='',
                      OrganizationID='0103', IdentityType=1, IdentityID='2018092901'))
>>>>>>> 6e909c317dcfbd2ae9b81b17acd36b996ecf8557
