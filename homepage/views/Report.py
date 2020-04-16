import os
import threading

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from manager.core import simplejson
from manager.invoker import MainSender
from manager.models import Plan, ResultDetail, MailConfig, User


@csrf_exempt
def sendreport(request):
	code = 0
	msg = ''
	planid = request.POST.get('planid')
	plan = Plan.objects.get(id=planid)
	username = request.session.get("username", None)
	detail = list(ResultDetail.objects.filter(plan=plan, is_verify=1).order_by('-createtime'))
	config_id = plan.mail_config_id
	if detail is None:
		msg = "任务还没有运行过！"
	elif plan.is_running in ('1', 1):
		msg = "任务运行中，请稍后！"
	else:
		taskid = detail[0].taskid
		threading.Thread(target=sendmail, args=(config_id, username, taskid)).start()
		msg = '发送中...'
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)

def sendmail(config_id, username, taskid):
	if config_id:
		mail_config = MailConfig.objects.get(id=config_id)
		user = User.objects.get(name=username)
		MainSender.send(taskid, user, mail_config)
		MainSender.dingding(taskid, user, mail_config)
		
		
		
@csrf_exempt
def downloadReport(request):
	reportname = BASE_DIR+'/logs/local_reports/report_' + request.POST.get("taskid") + '.html'
	if os.path.exists(reportname):
		with open(reportname, 'r', encoding='gbk') as f:
			text = '<meta charset="UTF-8">\n' + f.read()
		response = HttpResponse(text)
		response['Content-Type'] = 'application/octet-stream'
		response['Content-Disposition'] = 'attachment;filename=%s.html' % request.POST.get('taskid')
		return response
	else:
		return JsonResponse({'msg': ''})
