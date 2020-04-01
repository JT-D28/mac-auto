#a='''{"requestHead":{"enterpriseNum":"19999","method":"insurance","orderNo":"de12345566677777","version":"1","sign":"$[getRequestDataWithsignKey({'requestHead': {'enterpriseNum': '19999', 'method': 'insurance', 'orderNo': 'de12345566677777', 'version': '1'}, 'requestBody': {'commonInfo': {'productCode': '0010001', 'planCode': '0010001000258', 'appInsRelation': '0', 'callBackUrl': 'http://baoezt.com/InsuranceCon/BRCourtCallback'}, 'applicant': {'policyCustomerName': '保融科技', 'policyIdNo': '91330100563013163K', 'policyIdType': '1', 'policyPartyCategory': '2', 'policyAddress': '浙江省杭州市西湖区', 'phone': '13333333333', 'email': '123@fingard.com'}, 'abinsuredList': [], 'extendInfo': {'effectiveDate': '2020-05-1200:00:00', 'expiryDate': '2021-05-1123:59:59', 'squareArea': '3800', 'invoiceInfo': {'customerType': '1', 'invoiceType': '3', 'taxPayerNo': '91330100563013163K', 'taxPayerType': '1'}}}})]"},"requestBody":{"commonInfo":{"productCode":"0010001","planCode":"0010001000258","appInsRelation":"0","callBackUrl":"http://baoezt.com/InsuranceCon/BRCourtCallback"},"applicant":{"policyCustomerName":"保融科技","policyIdNo":"91330100563013163K","policyIdType":"1","policyPartyCategory":"2","policyAddress":"浙江省杭州市西湖区","phone":"13333333333","email":"123@fingard.com"},"abinsuredList":[],"extendInfo":{"effectiveDate":"2020-05-1200:00:00","expiryDate":"2021-05-1123:59:59","squareArea":"3800","invoiceInfo":{"customerType":"1","invoiceType":"3","taxPayerNo":"91330100563013163K","taxPayerType":"1"}}}}'''

import re


# $[handle_params({'a':1,'b':2})]


a='''{
'a':'$[handle_params({})]',
'b':'$[handle_params({})]'

}'''
print(a)
print('-'*200)
print(re.findall('\$\[(.*?)\((.*?)\)\]',a))

