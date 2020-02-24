import re
url="{{websys_url}}/webx/internalaccount/accountingrule/active.do"
#url='http://websysnew.tfp-cmbc-mysql-uat.k8s.fingard.cn/webx/systemindex/userlogin.do'

a=[a for a in url.split('/') if not a.__contains__('{')]

print('/'+'/'.join(a))