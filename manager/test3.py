import requests

url='http://10.60.44.25:9183/atsbase-front/front/systemlogin/login!login.do'
params={'loginName': 'server', 'password': 'fingard1!', 'verifycode': 'verifycode', 'ckeckCode': '', 'bizEncryptFalg': '', 'resCode': 'bizSign', 'opCode': 'bizSignIn2', 'lockuserflag': ''}
headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36', 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}
rps=requests.post(url,params=params,headers=headers)
print(rps.text)