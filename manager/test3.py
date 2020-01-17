import requests
url="http://ats.fingard.net:9561/front/front/systemlogin/login!login.do"
param={'loginName': '9DC310809F93211B92AA689C1B036779', 'password': '924B3CE22314EF96C80ABF428536F6BE62187C338FAA983E', 'verifycode': 'verifycode', 'ckeckCode': '', 'bizEncryptFalg': '3DES', 'resCode': 'bizSign', 'opCode': 'bizSignIn2', 'lockuserflag': ''}
rps=requests.post(url,param)
print(rps.text)
# for h in rps.history:
