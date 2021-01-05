import re
import time

from manager.models import Order, Step, Case, BusinessData
from manager.operate.mongoUtil import Mongo


async def dealruninfo(planid, taskid, spendTime, runkind, info=None, startnodeid=''):
	kind, nodeid = startnodeid.split("_")
	await dealDeBuginfo(taskid)
	
	success = Mongo.logsplit(taskid).find({"result": "success"}).count()
	total = Mongo.logsplit(taskid).find().count()
	statistics = {
		"total": total,
		"success": success,
		"fail": Mongo.logsplit(taskid).find({"result": "fail"}).count(),
		"error": Mongo.logsplit(taskid).find({"result": "error"}).count(),
		"skip": Mongo.logsplit(taskid).find({"result": "skip"}).count(),
		"successrate": round(success * 100 / total, 2) if total != 0 else 0.00,
		"spend": spendTime
	}
	result = {'timestamp': int(time.time()), 'time': time.strftime("%m-%d %H:%M", time.localtime()),
	          "kind": int(runkind),
	          'info': info, 'taskid': taskid, 'planid': int(planid), "statistics": statistics}
	Mongo.taskResult().insert_one(result)
	
	if kind == 'plan':
		caselist = list(Order.objects.values_list('follow_id', flat=True).filter(kind='plan_case', main_id=planid,
		                                                                         isdelete=0).extra(
			select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value"))
	else:
		caselist = [get_node_case(startnodeid)]
	node = {"root": []}
	for caseid in caselist:
		case = Case.objects.get(id=caseid)
		if case.count not in [0, '0', None]:
			num, successnum = get_business_num(caseid, taskid=taskid)
			rate = round(successnum * 100 / num, 2) if num != 0 else 0
			node['root'].append({'id': 'case_%s' % case.id, 'name': case.description, 'haschildren': True,
			                     'rate': rate,
			                     'success': successnum,
			                     'total': num, 'type': 'case', 'icon': 'fa icon-fa-folder'})
			getcasemap(caseid, node, taskid)
	Mongo.taskRecords().insert_one({"taskid": taskid, "node": node})


def getcasemap(caseid, node, taskid):
	maps = Order.objects.values('main_id', 'kind', 'follow_id').filter(main_id=caseid, isdelete=0,
	                                                                   kind__contains='case_').extra(
		select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
	for map in maps:
		temp = node.get('case_' + str(map['main_id']), [])
		if temp == []:
			node['case_' + str(map['main_id'])] = []
		if map['kind'] == 'case_step':
			cid = map['main_id']
			sid = map['follow_id']
			bnum = Mongo.logsplit(taskid).find({"path.caseid": int(cid), "path.stepid": int(sid)}).count()
			if bnum == 0:
				continue
			step = Step.objects.get(id=sid)
			if step.count not in [0, '0', None]:
				successnum = Mongo.logsplit(taskid).find(
					{"result": "success", "path.caseid": int(cid), "path.stepid": int(sid)}).count()
				rate = round(successnum * 100 / bnum, 2) if bnum != 0 else 0
				node['case_%s' % cid].append(
					{'id': 'step_%s' % sid, 'type': 'step',
					 'name': step.description,
					 'total': bnum,
					 'success': successnum, 'rate': rate, 'haschildren': True,
					 'icon': 'fa icon-fa-file-o'})
				get_business_info(step.id, node, taskid)
		
		elif map['kind'] == 'case_case':
			pid = map['main_id']
			cid = map['follow_id']
			
			case = Case.objects.get(id=cid)
			if case.count not in [0, '0', None]:
				total, successnum = get_business_num(cid, taskid)
				rate = round(successnum * 100 / total, 2) if total != 0 else 0
				node['case_%s' % pid].append(
					{'id': 'case_%s' % cid, 'type': 'case',
					 'name': case.description,
					 'total': total,
					 'success': successnum, 'rate': rate, 'haschildren': True,
					 'icon': 'fa icon-fa-folder'})
				getcasemap(cid, node, taskid)


def get_business_info(stepid, node, taskid):
	orders = Order.objects.filter(main_id=stepid, kind__contains='step_business', isdelete=0).extra(
		select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
	node['step_%s' % stepid] = []
	for order in orders:
		bid = order.follow_id
		
		businessdata = BusinessData.objects.get(id=bid)
		if businessdata.count not in [0, '0', None]:
			try:
				binfo = Mongo.logsplit(taskid).find_one({"path.businessid": int(bid)})
				state = binfo['result']
				node['step_%s' % stepid].append(
					{'id': 'business_%s' % bid, 'name': binfo.get("path")['businessname'], 'haschildren': False,
					 'type': 'business',
					 'icon': 'fa icon-fa-leaf', 'state': state})
			except:
				pass


def get_business_num(id, taskid='', num=0, successnum=0, countnum=0):
	orders = Order.objects.filter(main_id=id, kind__contains='case_', isdelete=0)
	for o in orders:
		kind = o.kind
		if kind == 'case_step':
			successnum += Mongo.logsplit(taskid).find(
				{"result": "success", "caseid": str(o.main_id), "stepid": str(o.follow_id)}).count()
			num += Mongo.logsplit(taskid).find({"caseid": str(o.main_id), "stepid": str(o.follow_id)}).count()
		elif kind == 'case_case':
			num, successnum = get_business_num(o.follow_id, taskid, num, successnum, countnum)
	return num, successnum


async def dealDeBuginfo(taskid):
	list = []
	oldcount = 0
	try:
		while 1:
			newcount = Mongo.tasklog(taskid).count_documents({})
			if newcount != oldcount:
				res = Mongo.tasklog(taskid).find().limit(newcount - oldcount).skip(oldcount)
				for i in res:
					list.append(i['info'])
					if '结束计划' in i['info']:
						raise Exception
				oldcount = newcount
	except:
		pass
	
	temp2 = re.sub(r'\[(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])\s+(20|21|22|23|[0-1]\d):[0-5]\d:[0-5]\d\]', '',
	               ''.join(list))
	bmatchs = re.findall(r"开始执行步骤.*?步骤.*?执行结果.*?</span>.*?<br>", temp2, flags=re.S)
	for b in bmatchs:
		try:
			await insertBusinessInfo(b, taskid)
		except:
			pass
	for i in list:
		try:
			failbmatch = re.findall(
				r"步骤\[<span style='color:#FF3399' id='step_.*?</span>]=>测试点\[<span style='color:#FF3399' id='business_.*?</span>]=>执行结果<span id=.*? class='layui-bg-orange'>skip</span>      原因=>skip<br>",
				i)
			if failbmatch:
				b = failbmatch[0]
				await insertBusinessInfo(b, taskid)
		except:
			pass



async def insertBusinessInfo(str, taskid):
	error = re.findall("原因=>(.*?)<br>", str)
	error = error[0] if error else ''
	
	path = {
		"caseid": int(re.findall("caseid='(.*?)'", str)[0]),
		"casedes": re.findall("casedes='(.*?)'", str)[0],
		"stepid": int(re.findall("id='step_(.*?)'", str)[0]),
		"stepdes": re.findall("id='step_.*?'>(.*?)</span>", str)[0],
		"businessid": int(re.findall("id='business_(.*?)'>", str)[0]),
		"businessname": re.findall("id='business_.*?'>(.*?)</span>]", str)[0],
	}
	Mongo.logsplit(taskid).insert_one(
		{'path': path,
		 'result':  re.findall("=>执行结果.*?class='layui-bg.*?>(.*?)</span>", str)[0], 'info': str, 'error': error})


def get_node_case(nodeid):
	kind, id = nodeid.split("_")
	if kind == 'case':
		return id
	elif kind == 'step':
		return Order.objects.get(kind='case_step', follow_id=id, isdelete=0).main_id
	elif kind == 'business':
		stepid = Order.objects.get(kind='step_business', follow_id=id, isdelete=0).main_id
		return get_node_case('step_%s' % stepid)
