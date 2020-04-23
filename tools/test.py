import requests
url='http://websysnew.tfp-cmbc-mysql-uat.k8s.fingard.cn/webx/internalaccount/transfer/import.do?businesstypeid=1002'
headers={'Referer':'http://websysnew.tfp-cmbc-mysql-uat.k8s.fingard.cn/webx/internalaccount/transfer/importPage.pub?businesstypeid=1002'}
headers={}
rps=requests.post(url,files=None,headers=headers)
print(rps.status_code)
print(rps.text)