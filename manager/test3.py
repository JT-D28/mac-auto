import ast
from urllib import parse
def base64_encrypt(str_):
    import base64
    return base64.b64encode(str_.encode('utf-8')).decode()

a='''{
    "AppVersion": '1.0.0',
    "EnterpriseNum": "AC310008",
    "Flag": "1",
    "QueryType": "3",
    "PageIndex": "1",
    "PageSize": "10",
    "IMEI": "13065ffa4e3618dbbd1testetsttest2",
    "PhoneNum": "18012345678",
    "UserInfoURID": "ff808081685a7d1a01685a8545c80104",
    "Signature": "34F7535081E24744CC6952564088CDA90E8F7086A65CD2E5BF125AD1CF609D5E69B728662E9641B164021B75ED50D2CCB878A7085569776A23C08DC02640DDDE"
}'''

#a = parse.urlencode(ast.literal_eval(a.replace('\r', '').replace('\n', '').replace('\t', '')))
#print(body) 
a=a.replace('\n','').replace(' ','')         
print(base64_encrypt(a))