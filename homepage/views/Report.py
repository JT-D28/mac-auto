import threading

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from ME2.settings import BASE_DIR
from manager.context import getRunningInfo
from manager.core import simplejson
from manager.operate.sendMail import MainSender
from manager.models import Plan, ResultDetail, MailConfig, User


@csrf_exempt
def sendreport(request):
	code = 0
	msg = ''
	info=''
	planid = request.POST.get('planid')
	plan = Plan.objects.get(id=planid)
	username = request.session.get("username", None)
	config_id = plan.mail_config_id
	taskid = getRunningInfo(planid, 'verify_taskid')
	if taskid == '':
		msg = "任务还没有运行过！"
	elif getRunningInfo(planid,'isrunning') in ['1','3']:
		msg = "任务运行中，请稍后！"
	else:
		config = MailConfig.objects.get(id=plan.mail_config_id)
		if config.is_send_mail=='close':
			info = '邮件发送没有开启;'
		if config.is_send_dingding == 'close':
			info += '钉钉发送没有开启;'

		threading.Thread(target=sendmail, args=(config_id, username, taskid)).start()
		msg = '发送中...<br> {}'.format(info)
	return JsonResponse(simplejson(code=code, msg=msg), safe=False)

def sendmail(config_id, username, taskid):
	if config_id:
		mail_config = MailConfig.objects.get(id=config_id)
		user = User.objects.get(name=username)
		MainSender.send(taskid, user, mail_config)
		MainSender.dingding(taskid, user, mail_config)
		
		
		
@csrf_exempt
def downloadReport(request):
	taskid = request.POST.get("taskid")
	text = MainSender.gethtmlcontent(taskid,'<meta charset="UTF-8">\n')
	response = HttpResponse(text)
	response['Content-Type'] = 'application/octet-stream'
	response['Content-Disposition'] = 'attachment;filename=%s.html' % request.POST.get('taskid')
	return response
