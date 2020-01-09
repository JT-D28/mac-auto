import requests,re,json

url='http://172.17.1.43/recon/reconbankdetail/bankDetailMatch/reviseFailReconStatus.do'
headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36', 'Content-Type': 'application/json;charset=UTF-8'}

body={'pageNum': 1, 'pageSize': 50, 'sortName': 'TRANS_NO', 'sortType': 'asc', 'entNum': 'AS330106_1', 'entChannelCode': '102_1', 'bankDetailReconciles': '', 'accountingDateStart': '2019-11-11', 'accountingDateEnd': '2019-11-11', 'accountNum': '', 'moneyWay': '', 'amountStart': '', 'amountEnd': '', 'bankReturnState': '', 'batchAllSelected': False, 'batchDetailAllSelectedList': [], 'singleAllSelected': False, 'batNoList': [], 'singleList': [{'urid': 'liulintest20191121001', 'version': '3'}], 'batchDetailList': [], 'accountingDate': '20191111', 'failReconStatus': '4'}
body=json.dumps(body)

body1="{'pageNum': 1, 'pageSize': 50, 'sortName': 'TRANS_NO', 'sortType': 'asc', 'entNum': 'AS330106_1', 'entChannelCode': '102_1', 'bankDetailReconciles': '', 'accountingDateStart': '2019-11-11', 'accountingDateEnd': '2019-11-11', 'accountNum': '', 'moneyWay': '', 'amountStart': '', 'amountEnd': '', 'bankReturnState': '', 'batchAllSelected': False, 'batchDetailAllSelectedList': [], 'singleAllSelected': False, 'batNoList': [], 'singleList': [{'urid': 'liulintest20191121001', 'version': '3'}], 'batchDetailList': [], 'accountingDate': '20191111', 'failReconStatus': '4'}"
body1=json.dumps(eval(body1))

# print(body)
# print(body1)
rps=requests.post(url,data=body1,headers=headers)
print(rps.status_code,rps.text)
print(rps.headers['Content-Type'])


