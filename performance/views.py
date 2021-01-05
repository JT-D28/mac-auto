import json
import threading
import time
import traceback

import consul
import requests
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.db import connection
from django.http import JsonResponse
from django.db import transaction
from pymongo import MongoClient

from ME2 import configs
from ME2.configs import Fabio_ADDR
from manager.context import Me2Log
from manager.operate.mongoUtil import Mongo
from manager.operate.redisUtils import RedisUtils, ConsulClient
from performance.models import *

iconMap = {
	"function": "fa icon-function",
	"plan": "fa icon-plan",
	"request": "fa icon-request",
	"transaction": "fa icon-transaction",
	"group": "fa icon-thread-group",
	"judge": "fa icon-judge",
	"beforehand": "fa icon-checkbox-unchecked",
}


def querySql(sql, args):
	List = []
	try:
		with connection.cursor() as cursor:
			cursor.execute(sql, args)
			desc = cursor.description
			List = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
	except:
		Me2Log.error(traceback.format_exc())
	return List


def getNodes(request):
	kind = request.POST.get("type")
	nodeList = []
	id = request.POST.get("id")
	
	with connection.cursor() as cursor:
		if kind == "root" or id == "-1":
			if kind == "root":
				nodeList.append({"id": -1, "name": "任务表", "kind": "root", "open": True})
			sql = """select id,name,kind,'fa icon-plan' AS textIcon,-1 as pId  from performance_node where kind='plan'"""
			cursor.execute(sql)
			desc = cursor.description
			for row in cursor.fetchall():
				nodeList.append(dict(zip([col[0] for col in desc], row)))
		else:
			childList = Node.objects.get(id=id).childs.split(",")
			for cid in childList:
				if cid != "":
					temp = Node.objects.values().get(id=cid)
					temp["textIcon"] = iconMap[temp.get("kind")]
					nodeList.append(temp)
	
	return JsonResponse({'code': 0, 'msg': "", "nodes": nodeList})


def getNodeInfo(request):
	id = request.POST.get("id")
	info = ""
	sql = """SELECT n.id,n.name,n.kind,i.data,n.condition FROM performance_nodeinfo i ,performance_node n where i.node_id=n.id and n.id=%s"""
	rows = querySql(sql, [id])
	if len(rows) == 1:
		info = rows[0]
	return JsonResponse({'code': 0, 'msg': "", "node": info})


def NodeAdd(request):
	try:
		name = request.POST.get("name")
		kind = request.POST.get("kind")
		condition = request.POST.get("condition") if kind == "judge" else ""
		pId = request.POST.get("pId")
		
		with transaction.atomic():
			node = Node(name=name, kind=kind, condition=condition, parent=pId)
			node.save()
			if pId != "-1":
				pNode = Node.objects.get(id=pId)
				if kind == "beforehand":
					pNode.childs = str(node.id) + ',' + pNode.childs if pNode.childs != "" else str(node.id)
				else:
					pNode.childs = pNode.childs + ',' + str(node.id) if pNode.childs != "" else str(node.id)
				pNode.save()
			
			config = request.POST.get("config", "")
			nodeInfo = NodeInfo(node_id=node.id, data=config)
			nodeInfo.save()
			
			data = {
				"code": 0,
				"msg": '新增[%s]成功' % name,
				"data": {
					"id": node.id,
					"pId": pId,
					"name": name,
					"kind": kind,
					"textIcon": iconMap[kind],
				}}
			return JsonResponse(data)
	except:
		Me2Log.error(traceback.format_exc())
		return JsonResponse({"code": 1, "msg": "新增失败[%s" % traceback.format_exc(), "data": ""})


def NodeEdit(request):
	try:
		name = request.POST.get("name")
		kind = request.POST.get("kind")
		condition = request.POST.get("condition") if kind == "judge" else ""
		id = request.POST.get("id")
		with transaction.atomic():
			node = Node.objects.get(id=id)
			node.name = name
			node.condition = condition
			node.save()
			
			config = request.POST.get("config", "")
			nodeInfo = NodeInfo.objects.get(node_id=id)
			nodeInfo.data = config
			nodeInfo.save()
			
			data = {
				"code": 0,
				"msg": '编辑[%s]成功' % name,
				"data": {
					"name": name,
				}}
			return JsonResponse(data)
	except:
		Me2Log.error(traceback.format_exc())
		return JsonResponse({"code": 1, "msg": "编辑失败[%s" % traceback.format_exc(), "data": ""})


def NodeDel(request):
	id = request.POST.get("id")
	force = request.POST.get("force")
	pid = request.POST.get('pid')
	node = Node.objects.get(id=id)
	name = node.name
	try:
		with transaction.atomic():
			if force == '0':
				if node.childs.strip() == "":
					node.delete()
					NodeInfo.objects.get(node_id=id).delete()
				else:
					return JsonResponse({"code": 1, "msg": '删除[%s]失败，有子节点' % name})
			else:
				for i in node.childs.split(","):
					if i != "":
						delnode = Node.objects.filter(id=i)
						if delnode.first():
							delnode.delete()
						delnodeinfo = NodeInfo.objects.filter(node_id=i)
						if delnodeinfo.first():
							delnodeinfo.delete()
				node.delete()
				NodeInfo.objects.get(node_id=id).delete()
			
			if pid != "-1":
				pNode = Node.objects.get(id=pid)
				childs = "," + pNode.childs
				childs = childs.replace("," + id, "")
				if childs.startswith(","):
					childs = childs[1:]
				pNode.childs = childs
				pNode.save()
		return JsonResponse({"code": 0, "msg": '删除[%s]成功' % name})
	except:
		return JsonResponse({"code": 2, "msg": '删除[%s]成功,%s' % (name, traceback.format_exc())})


def NodeRun(request):
	pass


def generateReport(allData, interval):
	rspTime = {}
	tpsTemp = {}
	Bytes = {}
	timeAxis = []
	tpsLegend = []
	tpsSeries = []
	rspTimeLegend = []
	rspTimeSeries = []
	BytesLegend = []
	BytesSeries = []
	HitsSeries = []
	
	i = 0
	for data in allData:
		i += 1
		if i % interval != 0:
			continue
		if data.get("finally"):
			continue
		timeAxis.append(time.strftime("%H:%M:%S", time.localtime(data["time"])))
		HitsSeries.append(data.get("hitnums", 0))
		
		if data["curve"] is None:
			continue
		for obj in data["curve"]:
			if obj["name"] not in tpsTemp.keys():
				T = {"name": "", "type": "line", "smooth": False, "data": []}
				
				T["name"] = obj["name"]
				T["data"] = [obj["tps"]]
				tpsTemp[T["name"]] = T.copy()
				
				T["name"] = obj["name"] + "[成功]"
				T["data"] = [obj["successtps"]]
				tpsTemp[T["name"]] = T.copy()
				
				T["name"] = obj["name"] + "[失败]"
				T["data"] = [obj["failtps"]]
				tpsTemp[T["name"]] = T.copy()
				
				T["name"] = obj["name"]
				T["data"] = [obj["responsetime"]]
				rspTime[T["name"]] = T.copy()
				
				T["name"] = obj["name"] + "[发送]"
				T["data"] = [obj["sendbytes"]]
				Bytes[T["name"]] = T.copy()
				
				T["name"] = obj["name"] + "[接收]"
				T["data"] = [obj["receivedbytes"]]
				Bytes[T["name"]] = T.copy()
			
			else:
				tpsTemp[obj["name"]]["data"].append(obj["tps"])
				tpsTemp[obj["name"] + "[成功]"]["data"].append(obj["successtps"])
				tpsTemp[obj["name"] + "[失败]"]["data"].append(obj["failtps"])
				
				rspTime[obj["name"]]["data"].append(obj["responsetime"])
				Bytes[obj["name"] + "[发送]"]["data"].append(obj["sendbytes"])
				Bytes[obj["name"] + "[接收]"]["data"].append(obj["receivedbytes"])
	
	for key, value in tpsTemp.items():
		tpsSeries.append(value)
		tpsLegend.append(key)
	
	for key, value in rspTime.items():
		rspTimeLegend.append(key)
		rspTimeSeries.append(value)
	
	for key, value in Bytes.items():
		BytesLegend.append(key)
		BytesSeries.append(value)
	
	return {"tpsSeries": tpsSeries, "tpsLegend": tpsLegend, "rspTimeLegend": rspTimeLegend,
	        "rspTimeSeries": rspTimeSeries,
	        "BytesLegend": BytesLegend, "BytesSeries": BytesSeries, "xData": timeAxis, "HitsSeries": HitsSeries}


def runPerformance(request):
	runId = request.POST.get("id", "")
	kind = request.POST.get("kind")
	runKind = 1 if kind == "run" else 2
	try:
		if runId != "" or kind != "":
			r = requests.post("http://" + Fabio_ADDR + "/task/base/performance",
			                  data={"id": runId, "username": request.session.get('username'), "runKind": runKind,
			                        "from": configs.ID})
			Me2Log.info(r.request.body)
			try:
				Me2Log.info(r.json())
				return JsonResponse(r.json())
			except:
				return JsonResponse({"code": 1, "msg": r.text})
		else:
			return JsonResponse({"code": 1, "msg": "参数不正确"})
	except:
		return JsonResponse({"code": 1, "msg": traceback.format_exc()})


def queryNodeKind(request):
	id = request.POST.get("id")
	return JsonResponse({"code": 0, "kind": Node.objects.get(id=id).kind})


def queryPlan(request):
	plans = Node.objects.values().filter(kind="plan")
	return JsonResponse({"code": 0, "data": list(plans)})


def queryTasks(request):
	id = request.POST.get("id", 0)
	res = list(Mongo.performanceTaskId().find({'planid': int(id)}, {'_id': 0}).sort('time', -1).limit(10))
	for i in res:
		i["time"] = time.strftime("%m-%d %H:%M:%S", time.localtime(i["time"]))
	
	return JsonResponse({"code": 0, "data": res})


class reportConsumer(WebsocketConsumer):
	def sendmsg(self, threadId):
		mongoCon = MongoClient(configs.MONGO_HOST, int(configs.MONGO_PORT))
		coll = mongoCon.load[self.taskid]
		try:
			oldcount = 0
			while self.nowId == threadId:
				newcount = coll.count_documents({})
				if newcount != oldcount:
					res = coll.find({}, {"_id": 0})  # .limit(newcount - oldcount).skip(oldcount)
					data = generateReport1(res, self.interval, self.kind)
					rows = coll.find({}, {"_id": 0}).sort('time', -1).limit(1)
					aggregate = next(rows).get("aggregate")
					
					r = mongoCon.plandata['loadTask'].find({"taskid": self.taskid}, {"_id": 0, "status": 1}).limit(1)
					oldcount = newcount
					if next(r).get("status") == 0:
						self.conKind = 0
					async_to_sync(get_channel_layer().send)(
						self.channel_name,
						{
							"type": "send.message",
							"charts": data,
							"aggregate": aggregate,
						}
					)
				time.sleep(1)
		except:
			pass
	
	def send_message(self, event):
		self.send(text_data=json.dumps({
			"charts": event["charts"],
			"aggregate": event["aggregate"],
		}))
	
	def receive(self, text_data):
		data = json.loads(text_data)
		self.taskid = data.get("taskid")
		self.interval = data.get("interval")
		self.kind = data.get("kind")
		self.nowId = data.get("kind") + str(self.interval)
		self.thread = threading.Thread(target=self.sendmsg, args=(self.nowId,))
		self.thread.start()
	
	def disconnect(self, code=None):
		self.con = 0


def nodeCopy(request):
	srcId = request.POST.get("srcId")
	targetId = request.POST.get("targetId")
	moveType = request.POST.get("moveType")
	if "" in [srcId, targetId]:
		return JsonResponse({"code": 1, "msg": "源节点和目标节点不能为空"})
	else:
		try:
			with transaction.atomic():
				copy(srcId, targetId, moveType)
		except:
			Me2Log.warn(traceback.format_exc())
			return JsonResponse({"code": 1, "msg": "复制出错：" + traceback.format_exc()})
	return JsonResponse({"code": 0, "msg": "复制成功"})


def copy(srcId, targetId, moveType):
	srcNode = Node.objects.get(id=srcId)
	if moveType == "inner":
		targetNode = Node.objects.get(id=targetId)
	else:
		targetNode = Node.objects.get(id=Node.objects.get(id=targetId).parent)
	
	copyNode = Node(name=srcNode.name, kind=srcNode.kind, condition=srcNode.condition, parent=targetNode.id)
	copyNode.save()
	
	childs = targetNode.childs.split(",")
	
	print(copyNode.id)
	
	if moveType == "inner":
		childs.append(str(copyNode.id))
	elif moveType == "prev":
		childs.insert(childs.index(targetId), str(copyNode.id))
	elif moveType == "next":
		childs.insert(childs.index(targetId) + 1, str(copyNode.id))
	
	targetNode.childs = ",".join(childs)
	targetNode.save()
	
	info = NodeInfo.objects.get(node_id=srcId)
	newInfo = NodeInfo(node_id=copyNode.id, data=info.data)
	newInfo.save()
	
	clist = []
	for child in srcNode.childs.split(","):
		if child != "":
			cid = copy(child, copyNode.id, "inner")
			clist.append(cid)
	copyNode.childs = ",".join(clist)
	copyNode.save()
	return str(copyNode.id)


def nodeMove(request):
	srcId = request.POST.get("srcId")
	targetId = request.POST.get("targetId")
	moveType = request.POST.get("moveType")
	
	try:
		with transaction.atomic():
			node = Node.objects.get(id=srcId)
			srcPNode = Node.objects.get(id=node.parent)
			IdList = srcPNode.childs.split(",")
			IdList.remove(srcId)
			srcPNode.childs = ",".join(IdList)
			srcPNode.save()
			childs = []
			targetNode = None
			if moveType == "inner":
				targetNode = Node.objects.get(id=targetId)
				childs = targetNode.childs.split(",")
				childs.append(srcId)
			elif moveType == "prev":
				targetNode = Node.objects.get(id=Node.objects.get(id=targetId).parent)
				childs = targetNode.childs.split(",")
				childs.insert(childs.index(targetId), srcId)
			elif moveType == "next":
				targetNode = Node.objects.get(id=Node.objects.get(id=targetId).parent)
				childs = targetNode.childs.split(",")
				i = childs.index(targetId) + 1
				childs.insert(i, srcId)
			targetNode.childs = ",".join(childs)
			targetNode.save()
			node.parent = targetNode.id
			node.save()
	except:
		Me2Log.warn(traceback.format_exc())
		return JsonResponse({"code": 1, "msg": "移动出错：" + traceback.format_exc()})
	return JsonResponse({"code": 0, "msg": "移动成功"})


def generateReport1(allData, interval, kind):
	Temp = {}
	i = 0
	source = []
	timeList = ["time"]
	for data in allData:
		i += 1
		if i % interval != 0:
			continue
		
		if data["curve"] is None:
			continue
		
		timeList.append(time.strftime("%H:%M:%S", time.localtime(data["time"])))
		if kind == "Hits":
			if Temp.get("点击率"):
				Temp['点击率'].append(data.get("hitnums", 0))
			else:
				Temp['点击率'] = [data.get("hitnums", 0)]
		
		else:
			for obj in data["curve"]:
				if kind == "Tps":
					if Temp.get(obj["name"]):
						Temp[obj["name"]].append(obj["tps"])
						Temp[obj["name"] + "[失败]"].append(obj["failtps"])
						Temp[obj["name"] + "[成功]"].append(obj["successtps"])
					else:
						Temp[obj["name"]] = [obj["tps"]]
						Temp[obj["name"] + "[失败]"] = [obj["failtps"]]
						Temp[obj["name"] + "[成功]"] = [obj["successtps"]]
				if kind == "ResponseTime":
					if Temp.get(obj["name"]):
						Temp[obj["name"]].append(obj["responsetime"])
					else:
						Temp[obj["name"]] = [obj["responsetime"]]
				if kind == "ThroughPut":
					if Temp.get(obj["name"] + "[发送]"):
						Temp[obj["name"] + "[发送]"].append(obj["sendbytes"])
						Temp[obj["name"] + "[接收]"].append(obj["receivedbytes"])
					else:
						Temp[obj["name"] + "[发送]"] = [obj["sendbytes"]]
						Temp[obj["name"] + "[接收]"] = [obj["receivedbytes"]]
	
	legend = []
	source.append(timeList)
	for name, value in Temp.items():
		legend.append(name)
		list = [name]
		list.extend(value)
		source.append(list)
	return {"source": source, "legend": legend}


def queryTestResources(request):
	(index, services_tags) = ConsulClient().catalog.services(index=1)
	services_names = services_tags.keys()
	# service_exclude = ["consul","fabio"]
	services_names = [i for i in services_names if i.startswith("MEE-")]
	ip = []
	for i in services_names:
		ip.append(i.split("-")[1])
	return JsonResponse({"code": 0, "data": ip})

def get_other_instance_result(service_name, prefix_url):
    # 调用consul api
    consul_service = consulClient.catalog.service(service_name)
    print(consul_service)
    consul_service_instances = []
    # 获取实例的真实ip
    if len(consul_service[1]) > 0:
        instance_address_infos = consul_service[1]
        for instance_address_info in instance_address_infos:
            consul_service_instances.append(
                "http://" + instance_address_info["ServiceTaggedAddresses"]["lan_ipv4"]["Address"] + ":" +
                str(instance_address_info["ServiceTaggedAddresses"]["lan_ipv4"]["Port"]) + "/")
    else:
        return "no instance"
    # 随机返回一个可用实例
    instance_url = choice(consul_service_instances)
    print(instance_url)
    try:
        # 发起请求
        result = requests.get(instance_url + prefix_url).text
    except Exception as e:
        result = "ERROR:" + str(e)
    return result