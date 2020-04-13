import os

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from manager.core import simplejson


@csrf_exempt
def downloadlog(request):
	logname = './logs/' + request.POST.get('taskid') + '.log'
	with open(logname, 'r', encoding='utf-8') as f:
		log_text = '<meta charset="UTF-8">\n' + f.read()
	# log_text = log_text.replace("<span style='color:#FF3399'>", '').replace("</xmp>", '').replace(
	# 	"<xmp style='color:#009999;'>", '').replace(
	# 	"<span class='layui-bg-green'>", '').replace("<span class='layui-bg-red'>", '').replace(
	# 	"<span class='layui-bg-orange'>", '').replace("</span>", '').replace(
	# 	"<span style='color:#009999;'>", '').replace('<br>', '').replace(
	# 	"'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36', ",
	# 	'')
	response = HttpResponse(log_text)
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
	logname = "./logs/" + taskid + ".log"
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