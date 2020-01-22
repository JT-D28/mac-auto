import re
url='http://websysnew.tfp-cmbc-mysql-uat.k8s.fingard.cn/webx/systemindex/userlogin.do'
print('/'+'/'.join(re.findall('http://(.*)',url)[0].split('/')[1:]))

print(url.split('/'))