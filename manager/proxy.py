#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-09-02 11:11:43
# @Author  : Blackstone
# @to      :

import mitmproxy.http,json,requests
from mitmproxy import ctx
from collections import namedtuple
import redis

__filter=('jpg','json','ico','txt','css')




class Proxy:
	def __init__(self):
		self.con=redis.Redis(host = '127.0.0.1',port = '6379')



	def pushqueue(self,queue,data):
		queue.put(data)

	def request(self, flow: mitmproxy.http.HTTPFlow):

		headers="||".join([ '%s=%s'%(k,v) for (k,v) in flow.request.headers.items()])
		#headers=(str(flow.request.headers))
		#url='%s:%s:%s'%(flow.request.url,flow.request.port,flow.request.path)
		# headers=flow.request.headers
		# _getheader(headers)
		url=flow.request.url
		method=flow.request.method
		scheme=flow.request.scheme
		# body=flow.request.get_text()
		body=str(flow.request.get_text())
		version=''
		itf=Interface(scheme=scheme,url=url,method=method,headers=headers,body=body,version=version)
		data=json.dumps(itf._asdict())
		if(_is_avariable(itf.url)):
			# re=redis.Redis(host = '127.0.0.1',port = '6379')
			self.con.lpush('list',data)
			ctx.log.info('队列长度='+str(self.con.llen('list')))
			ctx.log.info(data)
			ctx.log.info('-'*100)


addons = [Proxy()]


def _getheader(headers):
	for h in headers:
		print(h)


def _is_avariable(url):
	for x in __filter:
		if url.endswith(x):
			return False
	return True





Interface=namedtuple('Interface', ['scheme','method','url','body','version','headers'])

