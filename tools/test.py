
import requests,traceback

rps=requests.get('http://www.baidu.com/')
print(type(rps.status_code))

