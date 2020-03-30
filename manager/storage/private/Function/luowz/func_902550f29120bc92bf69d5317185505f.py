def sign(jsonData=''):
import json
import hashlib
import time
	text = json.loads(jsonData)
	if 'TransDate' in text.keys():
		text['TransDate']=time.strftime('%Y%m%d', time.localtime(time.time()))
	if 'TransTime' in text.keys():
		text['TransTime']=time.strftime('%H%M%S', time.localtime(time.time()))
	if 'RdSeq' in text.get('IN')[0].keys():
		text['IN'][0]['RdSeq']='{0:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now())[:-3]
	if 'PaymentCode' in text.get('IN')[0].keys():
		text['IN'][0]['PaymentCode']='{0:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now())[:-3]
	if 'ExpireDate' in text.get('IN')[0].keys():
		text['IN'][0]['ExpireDate']=time.strftime('%Y%m%d', time.localtime(time.time()))+'235959'
	d_in = text.get('IN')[0]
	IN = list(text.get('IN')[0].keys())
	IN.sort()
	s=''
	for e in IN:
		s+=e+'='+d_in.get(e)+'&'
	sign_be=s+'key=1234567890'
	sign_af = hashlib.md5(sign_be.encode(encoding='UTF-8')).hexdigest()
	text['IN'][0].update({'S3Sign':sign_af})
	json_sign=json.dumps(text,ensure_ascii=False)
	return json_sign