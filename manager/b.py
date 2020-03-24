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

'1.新框架所有页面 编辑删除[100% 删除没做依赖检查后面加]',
'2.测试邮件配置分任务[15% 做了部分接口和数据模型调整]',
'3.迁移脚本优化',
'4.迁移用例',
'5.优化',
'a.所有接口的session失效跳转',
'b.一些重要bug修复 如步骤和用例调序bug修复',
'c.删除依赖检查',
'd.增加测试步骤测试用例时的批量操作',
'e.增加文本验证规则',
'f.@字符数据库关联查询 变量输入快捷键'
'g.详情查看'


# ]


@classmethod
def _format_addr(cls, s):
	name, addr = parseaddr(s)
	return formataddr((Header(name, 'utf-8').encode(), addr))


# @classmethod
# def getworkcontent(cls):
#   msg=''
#   for line in cls.workcontent:
#       msg+="<p>%s</p>"%line
#   return msg
@classmethod
def gethtmlcontent(cls, taskid, rich_text):
	data = gettaskresult(taskid)
	
	# cls.subject='%s自动化测试报告-%s'%(data['planname'],str(datetime.datetime.now())[0:10])
	cls.subject = '%s自动化测试报告-%s' % (data['planname'], '2019-10-31')
	cssstr = '<style type="text/css">body{font-family:Microsoft YaHei}.success{color:#093}.fail{color:#f03}.skip{color:#f90}.error{color:#f0f}table{width:95%;margin:auto}th{background-color:#39c;color:#fff}td{background-color:#eee;text-align:center}</style>'
	bodyhtml = ''
	# bodyhtml='<span style="float:right;font-size:1px;font-color:#eee;">%s-%s</span>'%(data['taskid'],data['planid'])
	bodyhtml += '<h2 style="text-align: center;">[%s]接口测试报告</h2>' % data['planname']
	bodyhtml += "<p class='attribute'><strong>测试结果</strong></p>"
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
				print('nnufa=>', step)
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
		
		rich_text_rp = _replace_property(user, mail_config.rich_text)
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
		description_rp = _replace_property(user, description)
		if description_rp[0] is 'success':
			description_rv = _replace_variable(user, description_rp[1], taskid=taskid)
			if description_rv[0] is 'success':
				subject = description_rv[1] + ' 发送时间:' + str(time.strftime("%m-%d %H:%M"))
			else:
				ret = 1
				error = '变量替换异常,检查变量是否已定义'
		
		else:
			ret = 1
			error = '属性替换异常 可用属性'
		
		htmlcontent = cls.gethtmlcontent(taskid, rich_text)
		msg = MIMEText(htmlcontent, 'html', 'utf-8')
		msg['From'] = formataddr([sender_nick, sender_name])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
		msg['To'] = '%s' % ','.join(
			[cls._format_addr('<%s>' % to_addr) for to_addr in list(to_receive.split(','))])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
		# msg['Subject']=cls.subject          # 邮件的主题，也可以说是标题
		msg['Subject'] = subject
		server = smtplib.SMTP_SSL(smtp_host, smtp_port)  # 发件人邮箱中的SMTP服务器，端口是25
		server.login(sender_name, sender_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
		server.sendmail(sender_name, list(to_receive.split(',')), msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
		server.quit()  # 关闭连接
	
	
	
	
	
	
	except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
		print(traceback.format_exc())
		ret = 2
		error = traceback.format_exc()
	
	return cls._getdescrpition(mail_config.to_receive, ret, error)


@classmethod
def gen_report(cls, taskid, htmlcontent):
	print('==本地缓存测试报告')
	with open('./local_reports/report_%s.html' % taskid, 'w') as f:
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
			res = gettaskresult(taskid)
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
