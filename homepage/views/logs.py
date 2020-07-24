import os

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ME2.settings import BASE_DIR
from manager.core import simplejson
from manager.operate.mongoUtil import Mongo


@csrf_exempt
def downloadlog(request):
	taskid = request.POST.get('taskid')
	oldcount = 0
	list = []
	try:
		while 1:
			newcount = Mongo.tasklog(taskid).count_documents({})
			if newcount != oldcount:
				res = Mongo.tasklog(taskid).find().limit(newcount - oldcount).skip(oldcount)
				for i in res:
					temp = i['info'].replace('\n', '').replace(
						"'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36', ",
						'')
					list.append(temp)
					if '结束计划' in temp:
						raise Exception
				oldcount = newcount
	except:
		pass


	response = HttpResponse(''.join(list))
	response['Content-Type'] = 'application/octet-stream'
	response['Content-Disposition'] = 'attachment;filename=%s.html' % request.POST.get('taskid')
	return response


@csrf_exempt
def process(request):
	taskid = request.POST.get('taskid')
	code = 0
	log_text = ''
	is_done = 'no'
	done_msg = '结束计划'
	logname = BASE_DIR+"/logs/" + taskid + ".log"
	try:
		if os.path.exists(logname):
			with open(logname, 'r', encoding='utf-8') as f:
				log_text = f.read()
		else:
			print("no log")
		if done_msg in log_text:
			is_done = 'yes'
			print('日志执行结束', is_done)
		print(log_text)
	except:
		code = 1
		msg = "出错了！"
	return JsonResponse(simplejson(code=code, msg=is_done, data=log_text), safe=False)