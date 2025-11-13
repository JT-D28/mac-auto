import json
import os
import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ME2.settings import BASE_DIR
from manager.core import simplejson


@csrf_exempt
def globalsetting(request):
	code = 0
	msg = ''
	if request.method == 'POST':
		me2url = request.POST.get('me2url')
		redisurl = request.POST.get('redisurl')
		p = re.compile(
			'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)\:([0-9]|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{4}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])$')
		if p.match(me2url) and p.match(redisurl):
			data = {
				'me2url': me2url,
				'redisip': redisurl.split(':')[0],
				'redisport': redisurl.split(':')[1]
			}
			try:
				config = open("config", "w")
				config.write(json.dumps(data))
				config.close
				msg = "保存成功！"
			except:
				code = 1
				msg = '出错了！'
		else:
			code = 1
			msg = "请检查填写的地址是否正确！"
		return JsonResponse(simplejson(code=code, msg=msg), safe=False)
	else:
		try:
			config = open("config", "r")
			configtext = config.read()
			config.close
		except:
			code = 1
			msg = '出错了！'
		return JsonResponse(simplejson(code=code, msg=msg, data=json.loads(configtext)), safe=False)


def restart(request):
	taskid = request.POST.get('taskid')
	code = 0
	log_text = ''
	is_done = 'no'
	done_msg = '结束计划'
	logname = BASE_DIR+"/logs/" + taskid + ".log"
	try:
		if os.path.exists(logname):
			with open(logname, 'r') as f:
				log_text = f.read()
				f.close()
		if done_msg in log_text:
			is_done = 'yes'
	except:
		code = 1
		msg = "出错了！"
	return JsonResponse(simplejson(code=code, msg=is_done, data=log_text), safe=False)



