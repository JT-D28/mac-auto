import base64,json
def getdata(str_):
    import base64
    str_=str(str_['mw'])
    str_=str_.replace(' ','').replace('\n', '')
    return base64.b64encode(str_.encode()).decode()

data={
'EnterpriseNum':'QT330002',
'mw':{'LimitCreditPay':"0","TimeExpire":"20200418175525","CallFlag":"00","NonceStr":"EAdsaqSy1dD9Fe0DQ==","OutTradeNo":"1586324988","MchId":"7551000001","Attach":"测试","CertType":"0","OrganizationId":"55792171","MchCreateIp":"127.0.0.1","TimeStart":"20200407155525","EnterpriseNum":"QT330002","CustName":"张三","TotalFee":"1","CertNum":"330123131231313146","PhoneNum":"17758176904","NotifyUrl":"http://114.55.25.39:2837","Signature":"N/GbG+wCrC/pw6GhmG/igAecktcoktCyMVBloVTWgYo9jY2XiJ7To5EvcgXMOomRqPkT7FM1w8ESoZrq9ro8bLKV06/3fkZCMjqWJZrjF8chQ2sXEonmoPlJWUnwyv1n5M+hZ4SPSu7+enAWxpZoQhNl2jcdznZwj2W814wOE5Y=","Region":"000000","IsCheckIdentity":"0","Body":"车险缴费","CircPaymentNo":"12345678"},
'data':'eydMaW1pdENyZWRpdFBheSc6JzAnLCdUaW1lRXhwaXJlJzonMjAyMDA0MTgxNzU1MjUnLCdDYWxsRmxhZyc6JzAwJywnTm9uY2VTdHInOidFQWRzYXFTeTFkRDlGZTBEUT09JywnT3V0VHJhZGVObyc6JzE1ODYzMjQ5ODgnLCdNY2hJZCc6Jzc1NTEwMDAwMDEnLCdBdHRhY2gnOifmtYvor5UnLCdDZXJ0VHlwZSc6JzAnLCdPcmdhbml6YXRpb25JZCc6JzU1NzkyMTcxJywnTWNoQ3JlYXRlSXAnOicxMjcuMC4wLjEnLCdUaW1lU3RhcnQnOicyMDIwMDQwNzE1NTUyNScsJ0VudGVycHJpc2VOdW0nOidRVDMzMDAwMicsJ0N1c3ROYW1lJzon5byg5LiJJywnVG90YWxGZWUnOicxJywnQ2VydE51bSc6JzMzMDEyMzEzMTIzMTMxMzE0NicsJ1Bob25lTnVtJzonMTc3NTgxNzY5MDQnLCdOb3RpZnlVcmwnOidodHRwOi8vMTE0LjU1LjI1LjM5OjI4MzcnLCdTaWduYXR1cmUnOidOL0diRyt3Q3JDL3B3NkdobUcvaWdBZWNrdGNva3RDeU1WQmxvVlRXZ1lvOWpZMlhpSjdUbzVFdmNnWE1Pb21ScVBrVDdGTTF3OEVTb1pycTlybzhiTEtWMDYvM2ZrWkNNanFXSlpyakY4Y2hRMnNYRW9ubW9QbEpXVW53eXYxbjVNK2haNFNQU3U3K2VuQVd4cFpvUWhObDJqY2R6blp3ajJXODE0d09FNVk9JywnUmVnaW9uJzonMDAwMDAwJywnSXNDaGVja0lkZW50aXR5JzonMCcsJ0JvZHknOifovabpmannvLTotLknLCdDaXJjUGF5bWVudE5vJzonMTIzNDU2NzgnfQ==',
}


# print(getdata(data))
def base64_encrypt(str_):
    str_=str(str_)
    # print('str_1',str_)
    str_=str_.replace('\n','').replace(' ','').replace("'", '"')
    # print('str_2',str_)
    return base64.b64encode(str_.encode()).decode()

def base64_decrypt(str_):
    return base64.b64decode(str_).decode()

old={"LimitCreditPay":"0","TimeExpire":"20200418175525","CallFlag":"00","NonceStr":"EAdsaqSy1dD9Fe0DQ==","OutTradeNo":"1586324988","MchId":"7551000001","Attach":"测试","CertType":"0","OrganizationId":"55792171","MchCreateIp":"127.0.0.1","TimeStart":"20200407155525","EnterpriseNum":"QT330002","CustName":"张三","TotalFee":"1","CertNum":"330123131231313146","PhoneNum":"17758176904","NotifyUrl":"http://114.55.25.39:2837","Signature":"N/GbG+wCrC/pw6GhmG/igAecktcoktCyMVBloVTWgYo9jY2XiJ7To5EvcgXMOomRqPkT7FM1w8ESoZrq9ro8bLKV06/3fkZCMjqWJZrjF8chQ2sXEonmoPlJWUnwyv1n5M+hZ4SPSu7+enAWxpZoQhNl2jcdznZwj2W814wOE5Y=","Region":"000000","IsCheckIdentity":"0","Body":"车险缴费","CircPaymentNo":"12345678"}


print(base64_decrypt('eyJTdGF0dXMiOiIwIiwiRW50ZXJwcmlzZU51bSI6IlFUMzMwMDAyIiwiTm9uY2VTdHIiOiIxNTg2Mzk5MzIwNTQzIiwiUmV0dXJuTXNnIjoi6I635Y+W5LqM57u056CB5oiQ5YqfIiwiTWNoSWQiOiI3NTUxMDAwMDAxIiwiRkdUcmFkZU5vIjoiMjBRVDMzMDAwMjgwNDMyNzkzMDMxODAyODgiLCJTaWduYXR1cmUiOiJNRUhZeUZYbXc2MEJuSVZZRE9maWdsZ0lsY1hIcXBIRkZhSUU4bzd4cm5kcWVML2JZQU53MnJwU3dyNkJjajVMdThzZmphaXZ2VStHeWJHZGRuOFdveFp5Y1ZTb1lMbjByb3lEdXVVUXA0YUlNcUxmL2RyQWR4WDFJcnI5ZWFkWUhXcU54ZHd1VVZwQXowdWVMbzdOdm80WFc3VUVFRHlGV05vWWlCU290M2c9IiwiQ29kZUltZ1VybCI6Imh0dHBzOi8vcmhmd2ViYXBpdGVzdC5maW5nYXJkLmNuL2NvZGVJbWcvUVQzMzAwMDIvMjAyMDA0LzE1ODYzMjQ5ODgucG5nIiwiQ29kZVVybCI6Imh0dHBzOi8vaXBvcy5sYWthbGEuY29tL3EvbGtsMDMyY2VlYjdmMjUzNDJlN2I5ZDNjODZkYzIxZjZlMGQifQ=='))





