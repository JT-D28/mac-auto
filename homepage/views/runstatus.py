import json
import os
import threading
import time

from channels.layers import get_channel_layer
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json

from ME2.settings import BASE_DIR
from manager import cm
from manager.consumer import logConsumer
from manager.context import getRunningInfo
from manager.models import Case, Order, BusinessData, Plan, Step, ResultDetail
from manager.operate.mongoUtil import Mongo


def runstatus(request):
	return render(request, 'runstatus.html', locals())


@csrf_exempt
def runnodes(request):
	data = []
	id = request.POST.get('id')
	taskid = request.POST.get('taskid')
	type = request.POST.get('type')
	data = _get_pid_data(id, type)
	return JsonResponse({'data': data})


def _get_pid_data(idx, type):
	data = []
	if type == 'plan':
		cases = cm.getchild('plan_case', idx)
		for case in cases:
			if case.count not in (0, '0'):
				data.append({
					'id': 'case_%s' % case.id,
					'pId': 'plan_%s' % idx,
					'name': case.description,
					'type': 'case',
					'textIcon': 'fa icon-fa-folder',
				})

	elif type == 'case':
		orders = Order.objects.filter(kind__contains='case_', main_id=idx, isdelete=0).extra(
			select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
		for order in orders:
			try:
				nodekind = order.kind.split('_')[1]
				nodeid = order.follow_id
				obj = eval("%s.objects.values('description','count').get(id=%s)" % (nodekind.capitalize(), nodeid))
				if obj['count'] not in (0, '0'):
					textIcon = 'fa icon-fa-file-o' if nodekind == 'step' else 'fa icon-fa-folder'
					data.append({
						'id': '%s_%s' % (nodekind, nodeid),
						'pId': 'case_%s' % idx,
						'name': obj['description'],
						'type': nodekind,
						'textIcon': textIcon,
					})
			except Exception as e:
				print(e)

	elif type == 'step':
		businesslist = cm.getchild('step_business', idx)
		for business in businesslist:
			bname = business.businessname
			if business.count not in (0, '0'):
				data.append({
					'id': 'business_%s' % business.id,
					'pId': 'step_%s' % idx,
					'name': bname,
					'type': 'business',
					'textIcon': 'fa icon-fa-leaf',
				})
	return data


@csrf_exempt
def stauteofbusiness(request):
	type = request.POST.get('type')
	id = request.POST.get('id')
	planid = request.POST.get('planid')
	taskid = request.POST.get('taskid')
	info = '未执行'
	if type == 'business':
		r = ResultDetail.objects.get(taskid=taskid, plan_id=planid, businessdata_id=id)
		if r:
			info = '跳过执行'
	return JsonResponse({'info': info})


class getlog(WebsocketConsumer):
	def sendmsg(self, taskid):
		try:
			oldcount = 0
			while self.con == 1:
				newcount = Mongo.tasklog(taskid).count_documents({})
				if newcount != oldcount:
					res = Mongo.tasklog(taskid).find({}, {"info": 1, "_id": 0}).limit(newcount - oldcount).skip(
						oldcount)
					list = [i['info'] for i in res]
					async_to_sync(get_channel_layer().send)(
						self.channel_name,
						{
							"type": "send.message",
							"message": list
						}
					)
					oldcount = newcount
					for i in list:
						if '结束计划' in i:
							raise Exception
				time.sleep(0.05)
		except:
			pass

	def send_message(self, event):
		self.send(text_data=json.dumps({
			"message": event["message"]
		}))

	def receive(self, text_data):
		self.con = 1
		self.taskid = text_data
		self.thread = threading.Thread(target=self.sendmsg, args=(text_data,))
		self.thread.setDaemon(True)
		self.thread.start()

	def disconnect(self, code=None):
		self.con = 0
		print("%s 的日志打印结束" % self.taskid)
