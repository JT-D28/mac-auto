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
