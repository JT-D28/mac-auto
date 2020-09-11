import json
import os
import smtplib
import traceback
import time, datetime
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from email.header import Header

import requests

from ME2 import configs, settings
from ME2.settings import BASE_DIR
from login.models import User
from manager.context import Me2Log as logger, viewcache

from manager.models import ResultDetail, BusinessData, Order, MailConfig, Case
from manager.operate.mongoUtil import Mongo


def processSendReport(taskid, config_id, callername):
	# 	1.从数据库中获取该次任务的结果数据集合存到db中
	gettaskresult(taskid)
	if config_id:
		_save_builtin_property(taskid, callername)
		mail_config = MailConfig.objects.get(id=config_id)
		user = User.objects.get(name=callername)
		mail_res = MainSender.send(taskid, user, mail_config)
		dingding_res = MainSender.dingding(taskid, user, mail_config)
		# logger.info("发送邮件 结果[%s]" % mail_res)
		viewcache(taskid,mail_res)
		# logger.info("发送钉钉通知 结果[%s]" % dingding_res)
		viewcache(taskid, dingding_res)


def _save_builtin_property(taskid, username):
	'''
	测试报告可用内置属性
	 ${TASK_ID}
	 ${TASK_REPORT_URL}
	 ${PLAN_ID}
	 ${PLAN_NAME}
	 ${PLAN_RESULT}
	 ${PLAN_CASE_TOTAL_COUNT}
	 ${PLAN_CASE_SUCCESS_COUNT}
	 ${PLAN_CASE_FAIL_COUNT}
	 ${PLAN_STEP_TOTAL_COUNT}
	 ${PLAN_STEP_SUCCESS_COUNT}
	 ${PLAN_STEP_FAIL_COUNT}
	 ${PLAN_STEP_SKIP_COUNT}
	 #${PLAN_SUCCESS_RATE}
	'''
	detail = Mongo.taskreport().find_one({"taskid":taskid})
	if not detail:
		logger.info('==内置属性赋值提前结束，执行结果表无数据')
		return
	from manager.invoker import save_data, _tempinfo
	base_url = settings.BASE_URL
	url = "%s/manager/querytaskdetail/?taskid=%s" % (base_url, taskid)
	save_data(username, _tempinfo, 'TASK_ID', detail['taskid'])
	save_data(username, _tempinfo, 'TASK_REPORT_URL', url)
	save_data(username, _tempinfo, 'PLAN_ID', detail['planid'])
	save_data(username, _tempinfo, 'PLAN_NAME', detail['planname'])
	save_data(username, _tempinfo, 'PLAN_RESULT',
	          (lambda: 'success' if int(float(detail['success_rate'])) == 1 else 'fail')())
	save_data(username, _tempinfo, 'PLAN_CASE_TOTAL_COUNT', str(len(detail['cases'])))
	save_data(username, _tempinfo, 'PLAN_STEP_TOTAL_COUNT', detail['total'])
	save_data(username, _tempinfo, 'PLAN_STEP_SUCCESS_COUNT', detail['success'])
	save_data(username, _tempinfo, 'PLAN_STEP_FAIL_COUNT', detail['fail'])
	save_data(username, _tempinfo, 'PLAN_STEP_SKIP_COUNT', detail['skip'])
	save_data(username, _tempinfo, 'PLAN_SUCCESS_RATE', detail['success_rate'])


def gettaskresult(taskid):
	##区分迭代次数
	bset = set()
	bmap = {}
	##
	from manager.cm import getchild
	detail = {}
	spend_total = 0
	res = ResultDetail.objects.filter(taskid=taskid).order_by('createtime')

	# logger.info(res)
	reslist = list(res)
	if len(reslist) == 0:
		return detail

	plan = reslist[0].plan
	planname = plan.description
	planid = plan.id

	has_ = []

	caseids = []

	for r in list(res):
		if r.case.id not in has_:
			has_.append(r.case.id)
			caseids.append(r.case.id)

		else:
			pass

	##修复set乱序

	cases = [Case.objects.get(id=caseid) for caseid in caseids]

	# logger.info('cases=>')
	# logger.info(cases)
	report_url = 'http://%s/manage/report_%s.html' % (configs.ME2_URL, taskid)
	detail['local_report_address'] = report_url
	detail['planname'] = planname
	detail['planid'] = planid
	detail['taskid'] = taskid
	detail['cases'] = []
	detail['success'] = 0
	detail['fail'] = 0
	detail['skip'] = 0
	detail['error'] = 0
	detail['min'] = 99999
	detail['max'] = 0
	detail['average'] = 0

	for d in cases:
		caseobj = {}
		case = d
		casename = case.description
		caseid = case.id
		# caseobj['casename']=casename
		caseobj['casename'] = _get_full_case_name(caseid, casename)
		if caseobj.get("steps", None) is None:
			caseobj['steps'] = {}
		caseid = case.id
		# logger.info('taskid=>%s case_id=>%s'%(taskid,case))
		step_query = list(ResultDetail.objects.filter(taskid=taskid, case=case))
		##case_step
		for x in step_query:
			# rblist=list(ResultDetail.objects.filter(taskid=taskid,plan=plan,case=case,step=stepinst,businessdata=business))
			# for rb in rblist:
			businessobj = {}
			business = x.businessdata
			# logger.info('c=>%s'%business.id)
			status, step = BusinessData.gettestdatastep(business.id)
			# logger.info('a=>%s b=>%s'%(case.id,step.id))
			if isinstance(step, (str,)): continue;
			step_weight = Order.objects.get(main_id=case.id, follow_id=step.id, kind='case_step', isdelete=0).value

			business_index = \
				Order.objects.get(main_id=step.id, follow_id=business.id, kind='step_business', isdelete=0).value.split(
					'.')[1]
			businessobj['num'] = '%s_%s' % (step_weight, business_index)

			stepname = business.businessname
			result = x.result
			if 'omit' != result:
				if 'success' == result:
					detail['success'] = detail['success'] + 1

				elif 'fail' == result:
					detail['fail'] = detail['fail'] + 1

				elif 'skip' == result:
					detail['skip'] = detail['skip'] + 1

				elif 'error' == result:
					detail['error'] = detail['error'] + 1
				error = x.error
				businessobj['businessname'] = x.businessdata.businessname

				##
				businessobj['result'] = result
				businessobj['error'] = error
				# businessobj['api']=re.findall('\/(.*?)[?]',step.url)[0] or step.body
				stepinst = None
				error, stepinst = BusinessData.gettestdatastep(business.id)
				if stepinst.url:

					# logger.info('%s=>%s,%s'%(business.id,error,stepinst))
					businessobj['stepname'] = stepinst.description
					matcher = [a for a in stepinst.url.split('/') if
					           not a.__contains__("{{") and not a.__contains__(':')]
					api = '/'.join(matcher)
					if not api.startswith('/'):
						api = '/' + api
					businessobj['api'] = api
				else:
					businessobj['stepname'] = stepinst.description
					businessobj['api'] = stepinst.body.strip()

				businessobj['itf_check'] = business.itf_check
				businessobj['db_check'] = business.db_check
				# businessobj['spend']=ResultDetail.objects.get(taskid=taskid,plan=plan,case=case,step=stepinst,businessdata=business).spend
				businessobj['spend'] = x.spend
				spend_total += int(businessobj['spend'])
				if int(businessobj['spend']) <= int(detail['min']):
					detail['min'] = businessobj['spend']

				if int(businessobj['spend']) > int(detail['max']):
					detail['max'] = businessobj['spend']

				# caseobj.get('steps').append(businessobj)

				##计算当前迭代次数
				if x.businessdata.id in bset:
					bcount = bmap.get(str(x.businessdata.id), 0)
					bcount = bcount + 1
					bmap[str(x.businessdata.id)] = bcount
					L = caseobj.get('steps').get(str(bcount), [])
					L.append(businessobj)
					caseobj['steps'][str(bcount)] = L

				else:
					bset.add(x.businessdata.id)
					bcount = bmap.get(str(x.businessdata.id), 0)
					bcount = bcount + 1
					bmap[str(x.businessdata.id)] = bcount
					L = caseobj.get('steps').get(str(bcount), [])
					L.append(businessobj)
					caseobj['steps'][str(bcount)] = L

		##case_case map

		detail.get("cases").append(caseobj)

	detail['total'] = detail['success'] + detail['fail'] + detail['skip'] + detail['error']
	if detail['success'] == detail['total']:
		detail['result'] = 'pass'
	else:
		detail['result'] = 'fail'

	try:
		detail['average'] = int(spend_total / detail['total'])
	except:
		detail['average'] = '-1'

	try:
		detail['success_rate'] = str("%.2f" % (detail['success'] / detail['total']))
	except:
		detail['success_rate'] = '-1'
	detail["reporttime"] = time.strftime("%m-%d %H:%M", time.localtime())

	logger.info("==报告数据生成成功==")
	Mongo.taskreport().insert_one(detail)


def _get_full_case_name(case_id, curent_case_name):
	'''
	对于case_case结构的tree节点 报告中用例名显示为 casename0_casename1
	'''

	case0 = Case.objects.get(id=case_id)
	# fullname=case0.description
	olist = list(Order.objects.filter(follow_id=case_id, kind='case_case', isdelete=0))
	if len(olist) == 0:
		return curent_case_name

	else:
		cname = Case.objects.get(id=olist[0].main_id).description
		curent_case_name = "%s_%s" % (cname, curent_case_name)
		return _get_full_case_name(olist[0].main_id, curent_case_name)


class MainSender:
	'''
	测试报告工具类
	'''

	# my_sender='971406187@qq.com'    # 发件人邮箱账号
	# my_pass = 'mafkywyadboibfbj'              # 发件人邮箱密码
	# my_receive={
	# # 'hujj':'15157266151@126.com',
	# # 'hujj2':'971406187@qq.com',
	# 'hujj3':'hujj@fingard.com',
	# # 'chl':"chenhy@fingard.com",
	# # 'fhp':'fuhp@fingard.com',
	# # 'syc':'shanyc@fingard.com',
	# # 'xsl':'xuesl@fingard.com',
	# # 'zby':'zhengby@fingard.com',
	# # 'zjr':'zhanjr@fingard.com'
	# }
	# subject=""
	# workcontent=[

	# '1.新框架所有页面 编辑删除[100% 删除没做依赖检查后面加]',
	# '2.测试邮件配置分任务[15% 做了部分接口和数据模型调整]',
	# '3.迁移脚本优化',
	# '4.迁移用例',
	# '5.优化',
	# 'a.所有接口的session失效跳转',
	# 'b.一些重要bug修复 如步骤和用例调序bug修复',
	# 'c.删除依赖检查',
	# 'd.增加测试步骤测试用例时的批量操作',
	# 'e.增加文本验证规则',
	# 'f.@字符数据库关联查询 变量输入快捷键'
	# 'g.详情查看'

	# ]

	@classmethod
	def _format_addr(cls, s):
		name, addr = parseaddr(s)
		return formataddr((Header(name, 'utf-8').encode(), addr))

	@classmethod
	def gethtmlcontent(cls, taskid, rich_text):

		data = Mongo.taskreport().find_one({"taskid":taskid})

		if not data:
			return '<html>无运行数据..</html>'

		# cls.subject='%s自动化测试报告-%s'%(data['planname'],str(datetime.datetime.now())[0:10])
		cls.subject = '%s自动化测试报告-%s' % (data['planname'], '2019-10-31')
		cssstr = '<style type="text/css">body{font-family:Microsoft YaHei}.success{color:#093}.fail{color:#f03}.skip{color:#f90}.error{color:#f0f}table{width:95%;margin:auto}th{background-color:#39c;color:#fff}td{background-color:#eee;text-align:center}</style>'
		bodyhtml = ''
		# bodyhtml='<span style="float:right;font-size:1px;font-color:#eee;">%s-%s</span>'%(data['taskid'],data['planid'])
		bodyhtml += '<h2 style="text-align: center;">[%s]接口测试报告</h2>' % data['planname']
		bodyhtml += "<p class='attribute'><strong>测试结果</strong></p><button class='layui-btn btn' id='querybtn'>查询</button>"
		bodyhtml += "<table><tr><th>#Samples</th><th>Failures</th><th>Success Rate</th><th>Average Time</th><th>Min Time</th><th>Max Time</th></tr><tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr></table>" % (
			data['total'], data['fail'], data['success_rate'], data['average'], data['min'], data['max'])
		bodyhtml += "<strong>测试详情</strong>"

		for case in data['cases']:
			bodyhtml += '<p style="text-indent:2em;" >用例名[%s]</p>' % (case['casename'])

			# bodyhtml+='<table>'
			# bodyhtml+="<tr><th>执行序号</th><th>结果</th><th>耗时(ms)</th><th>步骤名称</th><th>api</th><th>接口验证</th><th>数据验证</th><th>消息</th></tr>"
			steps_iterator = case['steps']
			for iter_index, vs in steps_iterator.items():
				bodyhtml += '<p>第%s次迭代</p>' % iter_index

				bodyhtml += '<table>'
				bodyhtml += "<tr><th>执行序号</th><th>结果</th><th>耗时(ms)</th><th>步骤名称</th><th>api</th><th>接口验证</th><th>数据验证</th><th>消息</th></tr>"
				for step in vs:
					# logger.info('nnufa=>', step)
					bodyhtml += '<tr>'
					bodyhtml += '<td style="width:100px;">%s</td>' % step['num']
					bodyhtml += '<td style="width:100px;" class="%s">%s</td>' % (step['result'], step['result'])
					bodyhtml += '<td style="width:100px;">%s</td>' % step['spend']
					bodyhtml += '<td style="width:200px;" title="%s">%s</td>' % (step['stepname'], step['stepname'])
					bodyhtml += '<td style="width:200px;">%s</td>' % step['api']
					bodyhtml += '<td style="width:100px;">%s</td>' % step['itf_check']
					bodyhtml += '<td style="width:100px;">%s</td>' % step['db_check']
					bodyhtml += '<td>%s</td>' % step['error']
					bodyhtml += '</tr>'

				bodyhtml += '</table>'

		return cssstr + rich_text + '<br/>' + bodyhtml

	@classmethod
	def send(cls, taskid, user, mail_config):
		from manager.invoker import _replace_property, _replace_variable
		ret = 0
		error = ''
		try:
			is_send_mail = mail_config.is_send_mail
			if is_send_mail == 'close':
				return '=========发送邮件功能没开启 跳过发送================='
			sender_name = configs.EMAIL_HOST_USER
			sender_nick = configs.EMAIL_sender_nick
			sender_pass = configs.EMAIL_HOST_PASSWORD
			to_receive = mail_config.to_receive

			rich_text_rp = _replace_property(taskid, mail_config.rich_text)
			rich_text = ''
			if rich_text_rp[0] is 'success':
				rich_text_rv = _replace_variable(user, rich_text_rp[1], taskid=taskid)
				if rich_text_rv[0] is 'success':
					rich_text = rich_text_rv[1]
				else:
					ret = 1
					error = '变量替换异常,检查变量是否已定义'
			else:
				ret = 1
				error = '属性替换异常 可用属性'

			smtp_host = configs.EMAIL_HOST  # "smtp.qq.com"
			smtp_port = configs.EMAIL_PORT  # 465
			subject = ''
			description = mail_config.description
			description_rp = _replace_property(taskid, description)
			if description_rp[0] is 'success':
				description_rv = _replace_variable(user, description_rp[1], taskid=taskid)
				if description_rv[0] is 'success':
					subject = description_rv[1] + '————' + str(time.strftime("%m-%d %H:%M", time.localtime()))
				else:
					ret = 1
					error = '变量替换异常,检查变量是否已定义'

			else:
				ret = 1
				error = '属性替换异常 可用属性'

			htmlcontent = cls.gethtmlcontent(taskid, rich_text)
			msg = MIMEText(htmlcontent, 'html', 'utf-8')
			msg['From'] = formataddr([sender_nick, sender_name])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
			msg['To'] = '%s' % ','.join([cls._format_addr('<%s>' % to_addr) for to_addr in
			                             list(to_receive.split(','))])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
			# msg['Subject']=cls.subject          # 邮件的主题，也可以说是标题
			msg['Subject'] = subject
			server = smtplib.SMTP_SSL(smtp_host, smtp_port)  # 发件人邮箱中的SMTP服务器，端口是25
			server.login(sender_name, sender_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
			server.sendmail(sender_name, list(to_receive.split(',')), msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
			server.quit()  # 关闭连接

		except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
			logger.info(traceback.format_exc())
			ret = 2
			error = traceback.format_exc()

		return cls._getdescrpition(mail_config.to_receive, ret, error)

	@classmethod
	def gen_report(cls, taskid, htmlcontent):
		logger.info('==本地缓存测试报告')

		filepath = '%s/logs/local_reports/report_%s.html' % (BASE_DIR, taskid)
		if os.path.exists(filepath):
			with open(filepath, 'w') as f:
				f.write(htmlcontent)

	@classmethod
	def _getdescrpition(cls, to_receive, send_result, error=None):
		res = None
		if send_result is 0:
			res = '发送成功'
		elif send_result is 1:
			res = '发送成功 但邮件内容可能有小问题[%s]' % error

		elif send_result is 2:
			res = '发送失败[%s]' % error

		return '========================发送邮件 收件人:%s 结果：%s' % (to_receive, res)

	@classmethod
	def dingding(cls, taskid, user, mail_config):
		try:
			is_send_dingding = mail_config.is_send_dingding
			if is_send_dingding == 'close':
				return '=========发送钉钉功能没开启 跳过发送================='
			dingdingtoken = mail_config.dingdingtoken
			if dingdingtoken == '' or dingdingtoken is None:
				return '=========钉钉token为空 跳过发送================='
			else:
				url = 'https://oapi.dingtalk.com/robot/send?access_token=' + dingdingtoken
				res = Mongo.taskreport().find_one({"taskid":taskid})
				pagrem = {
					"msgtype": "markdown",
					"markdown": {
						"title": "自动化测试报告",
						"text": "计划【%s】的测试报告已生成：\n\n" % (res["planname"]) +
						        "> ***测试结果*** :\n\n" +
						        ">          用例总数：%s\n\n" % (res["total"]) +
						        ">          失败数量：%s\n\n" % (res["fail"]) +
						        ">          成功率：%s\n\n" % (res["success_rate"]) +
						        "> ###### %s [详情](%s) \n" % (time.strftime('%m-%d %H:%M', time.localtime(time.time())),
						                                     settings.BASE_URL + "/manager/querytaskdetail/?taskid=" + taskid)
					},
					"at": {
						"isAtAll": True
					}
				}
				headers = {
					'Content-Type': 'application/json'
				}
				requests.post(url, data=json.dumps(pagrem), headers=headers)

				send_result = 0
		except:
			send_result = 1
		return cls._getdingding(mail_config.dingdingtoken, send_result)

	@classmethod
	def _getdingding(cls, dingdingtoken, send_result):
		if send_result == 0:
			res = '发送钉钉消息成功'
		elif send_result == 1:
			res = '发送钉钉消息失败'
		return '=========发送钉钉通知 结果：%s=================' % (res)
