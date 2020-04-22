
import requests,traceback
url='http://websysnew.tfp-cmbc-mysql-uat.k8s.fingard.cn/webx/internalaccount/transfer/import.do?businesstypeid=1002'
files={
    
}
rps=requests.post(url,files=files)
print(type(rps.status_code))

