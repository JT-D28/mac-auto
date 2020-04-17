import os
import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection

from ME2.settings import BASE_DIR
from manager.context import getRunningInfo
from manager.core import getpagedata


@csrf_exempt
def plandebug(request):  # 调试日志
	res, type, taskid, code = doDebugInfo(request)
	return JsonResponse({"code": code, "type": type, "data": res, "taskid": taskid})


@csrf_exempt
def querybuglog(request):  # 历史缺陷
	gettime = request.POST.get("time")
	timestart = gettime.split(";")[0]
	timeend = gettime.split(";")[1]
	taskid = request.POST.get('taskid')
	res = []
	if taskid == 'omit':
		# 根据日期和任务id查询
		sql = '''
        SELECT r.taskid as '任务id', r.plan_id,r.createtime, b.id AS bussiness_id,p.description AS '计划名',c.description AS '用例名',
        s.description AS '步骤名',s.headers AS headers,s.body AS body,s.url AS url,
        b.businessname AS '测试点',b.itf_check AS '接口校验',b.db_check AS 'db校验',b.params AS '参数信息',
        r.error AS '失败原因' FROM manager_resultdetail r,manager_plan p,manager_case c,manager_step s,
        manager_businessdata b WHERE r.result IN ('error','fail') AND r.is_verify=1 AND r.plan_id=p.id AND r.case_id=c.id AND r.step_id=s.id
        AND r.businessdata_id=b.id AND  date_format(r.createtime,'%%Y-%%m-%%d')  BETWEEN %s and %s
        '''
		sql = sql if request.POST.get('planid') == '' else sql + 'and r.plan_id=' + \
		                                                   request.POST.get('planid').split("_")[1]
		with connection.cursor() as cursor:
			cursor.execute(sql, [timestart, timeend + '23:59:59'])
			desc = cursor.description
			rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
	else:
		# 根据taskid查找
		sql = '''
        select * from (SELECT r.taskid AS '任务id',r.plan_id,r.createtime,b.id AS bussiness_id,p.description AS '计划名',
        c.description AS '用例名',s.description AS '步骤名',s.headers AS headers,s.body AS body,s.url AS url,b.businessname
        AS '测试点',b.itf_check AS '接口校验',b.db_check AS 'db校验',b.params AS '参数信息',r.error AS '失败原因' FROM
        manager_resultdetail r,manager_plan p,manager_case c,manager_step s,manager_businessdata b WHERE r.result
        IN ('error','fail') AND r.is_verify=1 AND r.plan_id=p.id AND r.case_id=c.id AND r.step_id=s.id AND
        r.businessdata_id=b.id AND r.taskid=%s)  as k ORDER BY createtime
        '''
		with connection.cursor() as cursor:
			cursor.execute(sql, [taskid])
			desc = cursor.description
			rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
	for i in range(len(rows)):
		res.append(
			{'createtime': rows[i]['createtime'], '路径': rows[i]['用例名'] + '-' + rows[i]['步骤名'], '接口': rows[i]['url'],
			 '测试点': rows[i]['测试点'], '参数信息': rows[i]['参数信息'], '失败原因': rows[i]['失败原因'],
			 '任务id': rows[i]['任务id']})
	res, total = getpagedata(res, request.POST.get('page'), request.POST.get('limit'))
	
	return JsonResponse({"code": 0, 'count': total, "data": res})


def doDebugInfo(request):
	type = request.POST.get("type")
	id = request.POST.get("id")
	taskid = request.POST.get("taskid")
	
	if type == 'info':
		sql = '''
		SELECT p.description AS planname ,max(r.createtime) as time ,taskid,is_running from manager_plan p,
		manager_resultdetail r where p.id=r.plan_id and r.plan_id=%s  and r.is_verify=0 GROUP BY taskid ORDER BY time desc limit 1
		'''
		with connection.cursor() as cursor:
			cursor.execute(sql, [id])
			desc = cursor.description
			row = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
		is_debug_unning = '1' if getRunningInfo('', id, 'isrunning') == 'debug' else '0'
		return row, 'info', '', is_debug_unning
	
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
		return case_row, 'case', taskid, 0
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
		return step_row, 'step', taskid, 0
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
		return businessdata_row, 'bussiness', taskid, 0
	if type == 'bussiness':
		logname = BASE_DIR+"/logs/deal/" + taskid + ".log"
		if os.path.exists(logname):
			with open(logname, 'r', encoding='utf-8') as f:
				res = f.read()
			ress = res.split("========")
			pattern = re.compile('开始执行步骤.*?' + id.split(';')[2] + '.*?测试点\[.*?' + id.split(';')[0] + '.*?<br>')
			for i in ress:
				if pattern.search(i):
					return i, 'debuginfo', '', 0
				else:
					res = '未匹配到日志记录，你可以试试下载并且查看完整日志！'
		else:
			res = '请稍等！'
		return res, 'debuginfo', '', 0



