import os
import re

from django.db import connection


def doDebugInfo(request):
	type = request.POST.get("type")
	id = request.POST.get("id")
	taskid = request.POST.get("taskid")

	if type == 'info':
		sql = '''
        SELECT description as planname,max(manager_resultdetail.createtime) as time,taskid,is_running FROM manager_resultdetail 
        LEFT JOIN manager_plan on manager_plan.id=manager_resultdetail.plan_id where plan_id=%s
        '''
		with connection.cursor() as cursor:
			cursor.execute(sql, [id])
			desc = cursor.description
			row = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
		return row, 'info', '',row[0]['is_running']
	if type == 'plan':
		sql2 = '''
        SELECT description as title,case_id as id FROM manager_resultdetail r LEFT JOIN manager_case c on r.case_id=c.id 
        where plan_id=%s and taskid=%s and result in ('fail','error')
        '''
		with connection.cursor() as cursor:
			cursor.execute(sql2, [id, taskid])
			desc = cursor.description
			row = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
		case_row = []
		for i in list(row):
			if i not in case_row:
				case_row.append(i)
		return case_row, 'case', taskid,0
	if type == 'case':
		sql2 = '''
        SELECT description as title,step_id as id FROM manager_resultdetail r LEFT JOIN manager_step s 
        on r.step_id=s.id where case_id=%s and taskid=%s  and result in ('fail','error')
        '''
		with connection.cursor() as cursor:
			cursor.execute(sql2, [id, taskid])
			desc = cursor.description
			row = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
		step_row = []
		for i in list(row):
			if i not in step_row:
				step_row.append(i)
		return step_row, 'step', taskid,0
	if type == 'step':
		sql2 = '''
        SELECT businessname as title,businessdata_id AS id ,c.description as casename,s.description as stepname 
        from manager_resultdetail r , manager_businessdata b,manager_case c,manager_step s where r.businessdata_id=b.id 
        and r.step_id=%s AND r.taskid=%s AND r.result IN ('fail','error') and r.case_id=c.id 
        and s.id=r.step_id;
        '''
		with connection.cursor() as cursor:
			cursor.execute(sql2, [id, taskid])
			desc = cursor.description
			row = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
		businessdata_row = []
		for i in list(row):
			if i not in businessdata_row:
				businessdata_row.append(i)
		return businessdata_row, 'bussiness', taskid,0
	# if type == 'bussiness':
	#     res = ''
	#     sql2 = '''
	#     select c.description as casename,s.description as stepname,b.businessname as businessname,
	#     s.step_type,s.headers,s.body,s.url,s.method,s.content_type,b.itf_check,b.db_check,b.params,b.preposition,
	#     b.postposition,r.error,r.error from manager_case c, manager_resultdetail r,manager_step s,manager_businessdata b
	#     where r.businessdata_id=%s and r.taskid=%s and  r.step_id=s.id and r.businessdata_id=b.id and r.case_id=c.id
	#     '''
	#     with connection.cursor() as cursor:
	#         cursor.execute(sql2, [id, taskid])
	#         desc = cursor.description
	#         businessdata_row = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
	#     logname = "./logs/" + taskid + ".log"
	#     if os.path.exists(logname):
	#         with open(logname, 'r', encoding='utf-8') as f:
	#             tmep1 = ''
	#             while 1:
	#                 log_text = f.readline()
	#                 if '结束计划' in log_text:
	#                     break
	#                 else:
	#                     if '---------------' in log_text:
	#                         continue
	#                     else:
	#                         tmep = log_text.replace("<span style='color:#FF3399'>", '').replace("</xmp>", '').replace(
	#                             "<xmp style='color:#009999;'>", '').replace(
	#                             "<span class='layui-bg-green'>", '').replace("<span class='layui-bg-red'>", '').replace(
	#                             "<span class='layui-bg-orange'>", '').replace("</span>", '').replace(
	#                             "<span style='color:#009999;'>", '').replace('\n', '').replace(
	#                             "'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36', ",
	#                             '')
	#                         tmep1 = tmep1 + tmep
	#             temp2 = re.sub(
	#                 r'[1-9]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])\s+(20|21|22|23|[0-1]\d):[0-5]\d:[0-5]\d',
	#                 '', tmep1)
	#             tmep3 = temp2.split('开始执行用例')
	#             for i in range(len(tmep3)):
	#                 if businessdata_row[0]['casename'] and businessdata_row[0]['stepname'] in tmep3[i]:
	#                     spitdes = '测试点[' + businessdata_row[0]['businessname']
	#                     tmep4 = tmep3[i].split(spitdes)
	#                     if businessdata_row[0]['step_type'] == 'interface':
	#                         url = re.search(r"url=>.*?(?=<br>)", tmep4[1]).group().rstrip()
	#                         headers = re.search(r"headers.*?(?=<br>)", tmep4[1]).group().rstrip()
	#                         params = re.search(r"params.*?(?=<br>)", tmep4[1]).group().rstrip()
	#                         请求响应 = re.search(r"请求响应.*?(?=<br>)", tmep4[1]).group().rstrip()
	#                         前置操作 = re.search(r"前置操作.*?(?=<br>)", tmep4[0]).group().rstrip().replace(']',
	#                                                                                                 '：') if '前置操作' in \
	#                                                                                                         tmep4[
	#                                                                                                             0] else ''
	#                         后置操作 = re.search(r"后置操作.*?(?=<br>)", tmep4[1]).group().rstrip().replace(']',
	#                                                                                                 '：') if '后置操作' in \
	#                                                                                                         tmep4[
	#                                                                                                             1] else ''
	#                         res = [
	#                             {"id": "前置操作", "expect": businessdata_row[0]['preposition'], "real": 前置操作},
	#                             {"id": "headers", "expect": businessdata_row[0]['headers'], "real": headers},
	#                             {"id": "url", "expect": businessdata_row[0]['url'], "real": url},
	#                             {"id": "参数", "expect": businessdata_row[0]['params'], "real": params},
	#                             {"id": "后置操作", "expect": businessdata_row[0]['postposition'], "real": 后置操作},
	#                             {"id": "接口校验", "expect": businessdata_row[0]['itf_check'], "real": 请求响应},
	#                             {"id": "db校验", "expect": businessdata_row[0]['db_check'], "real": ''},
	#                             {"errer": businessdata_row[0]['error']}
	#                         ]
	#                     else:
	#                         前置操作 = re.search(r"前置操作.*?(?=<br>)", tmep4[0]).group().rstrip().replace(']',
	#                                                                                                 '：') if '前置操作' in \
	#                                                                                                         tmep4[
	#                                                                                                             0] else ''
	#                         后置操作 = re.search(r"后置操作.*?(?=<br>)", tmep4[1]).group().rstrip().replace(']',
	#                                                                                                 '：') if '后置操作' in \
	#                                                                                                         tmep4[
	#                                                                                                             1] else ''
	#                         调用函数 = re.search(r"调用函数.*?(?=<br>)", tmep4[1]).group().rstrip()
	#                         参数 = re.search(r"替换变量后的函数参数.*?(?=<br>)", tmep4[1]).group().rstrip() if '替换变量后的' in tmep4[
	#                             1] else ''
	#                         res = [
	#                             {"id": "前置操作", "expect": businessdata_row[0]['preposition'], "real": 前置操作},
	#                             {"id": "调用函数", "expect": businessdata_row[0]['body'], "real": 调用函数},
	#                             {"id": "参数", "expect": businessdata_row[0]['params'], "real": 参数},
	#                             {"id": "后置操作", "expect": businessdata_row[0]['postposition'], "real": 后置操作},
	#                             {"error": businessdata_row[0]['error']}
	#                         ]
	#
	#     return res, 'businessdata', taskid
	if type == 'bussiness':
		logname = "./logs/deal/" + taskid + ".log"
		if os.path.exists(logname):
			with open(logname, 'r', encoding='utf-8') as f:
				res = f.read()
			ress = res.split("========")
			pattern = re.compile('开始执行步骤.*?'+id.split(';')[2]+'.*?测试点\[.*?'+id.split(';')[0]+'.*?<br>')
			for i in ress:
				if pattern.search(i):
					return i, 'debuginfo', '',0
				else:
					res='未匹配到日志记录，你可以试试下载并且查看完整日志！'
		else:
			res = '请稍等！'
		return res, 'debuginfo', '',0


def dealDeBuginfo(taskid):
	logname = "./logs/" + taskid + ".log"
	dealogname = "./logs/deal/" + taskid + ".log"
	if os.path.exists(logname):
		ma = []
		with open(logname, 'r', encoding='utf-8') as f:
			tmep1 = ''
			while 1:
				log_text = f.readline()
				if '结束计划' in log_text:
					break
				else:
					if '---------------' in log_text:
						continue
					else:
						tmep = log_text.replace('\n', '').replace(
							"'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36', ",
							'')
						tmep1 = tmep1 + tmep
			temp2 = re.sub(
				r'[1-9]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])\s+(20|21|22|23|[0-1]\d):[0-5]\d:[0-5]\d', '',
				tmep1)
			case_matchs = re.findall(r"开始执行用例.*?结束用例.*?结果.*?<br>", temp2)
			print("开始处理日志------")
			for case in case_matchs:
				step_matchs = re.findall(r"开始执行步骤.*?步骤执行.*?结果.*?<br>", case)
				for step in step_matchs:
					with open(dealogname, 'a', encoding='UTF-8') as f:
						f.write(step.replace("        ", '\n') + '\n========\n')
			print('处理日志完成------')

