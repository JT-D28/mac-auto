#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-11-01 15:39:20
# @Author  : Blackstone
# @to      :

from django.shortcuts import HttpResponseRedirect
from django.http import HttpResponse, JsonResponse
from manager import models
from manager.core import simplejson
import re, os, traceback

try:
	from django.utils.deprecation import MiddlewareMixin  # Django 1.10.x
except ImportError:
	MiddlewareMixin = object  # Django 1.4.x - Django 1.9.x


class Interceptor(MiddlewareMixin):
	
	def _repeat_check(self, request):
		"""
		字段重复校验

		"""
		# print('==字段重复校验====')
		_meta = {
			'Function': 'name',
			'Interface': 'name',
			'Tag': 'name',
			# 'Variable': 'key',
			'DBCon': 'description',
			'Step': 'description',
			'Case': 'description',
			'Plan': 'description',
			'RemoteLog': 'description'
		}
		_m1 = {
			'Function': '函数',
			'Interface': '接口',
			# 'Variable': '变量',
			'DBCon': '数据连接',
			'Step': '步骤',
			'Case': '用例',
			'Plan': '计划',
			'RemoteLog': '远程日志',
			'Tag': '标签'
		}
		_m2 = {
			'name': '名称',
			'description': '描述',
			'key': '键名'
		}
		# op=None
		tmp = request.path.split('?')[0]
		# tmp=tmp.replace(tmp[-1],'')
		simplename = tmp.split('/')[-2]
		# print('simplename=>',simplename)
		
		flag1 = simplename.startswith('add')
		flag2 = simplename.startswith('edit')
		
		# print('flag=>',flag1,flag2)
		
		if flag1:
			key = simplename.replace('add', '').lower()
			# print('key=>',key)
			mkey = getkey(_meta, key)
			if mkey:
				actionV = request.POST.get(_meta[mkey])
				callstr = "list(models.%s.objects.filter(%s='%s'))" % (mkey, _meta[mkey], actionV)
				if mkey == 'Function':
					callstr = "list(models.Function.objects.filter(name='%s'))" % \
					          re.findall('def (.*?)\(.*?\)', request.POST.get('body'))[0]
				
				qssize = len(eval(callstr))
				print('callstr=>%s size=%s' % (callstr, qssize))
				print('url[%s]字段[%s]重复验证 已存在[%s]条' % (request.path, _meta[mkey], qssize))
				if qssize == 0:
					return ('success', '')
				else:
					return ('fail', "%s%s重复" % (_m1[mkey], _m2[_meta[mkey]]))
			
			else:
				return ('success', '')
		
		elif flag2:
			
			repeatid = None
			call_str = ''
			try:
				key = simplename.replace('edit', '').lower()
				# print('key=>',key)
				mkey = getkey(_meta, key)
				if mkey:
					actionV = request.POST.get(_meta[mkey])
					call_str = "models.%s.objects.get(%s='%s').id" % (mkey, _meta[mkey], actionV)
					print('callstr=>', call_str)
					call_id = request.POST.get('id')
					repeatid = eval(call_str)
					
					print('repeatid=>', repeatid)
					
					if str(call_id) == str(repeatid):
						return ('success', '')
					else:
						if repeatid:
							return ('fail', "%s%s重复" % (_m1[mkey], _m2[_meta[mkey]]))
				else:
					return ('success', '')
			except:
				print(traceback.format_exc())
				return ('success', '')
		
		else:
			return ('success', '')
	
	def _session_check(self, request):
		'''
		session校验
		'''
		_meta = ('/account/login/', '/manager/querytaskdetail/', '/test_expression/', '/test_expression1/',
		         '/manager/third_party_call/')
		if request.path not in _meta and not request.path.startswith('/captcha/image/'):
			if request.session.get('username', None):
				return True
			else:
				print('session校验不通过 跳到登录页面')
				return False
		
		return True
	
	def _print_call_msg(self, request):
		print("=============================调用[%s]===============" % request.path)
		a = dict(request.GET)
		b = dict(request.POST)
		print({**a, **b})
	
	def process_request(self, request):
		
		# print('==进入拦截器==')
		
		self._print_call_msg(request)
		
		session_check_result = self._session_check(request)
		repeat_check_result = self._repeat_check(request)
		# field_common_check_result=self._field_common_check(request)
		username = request.session.get('username')
		if session_check_result == False:
			return HttpResponseRedirect('/account/login/')
		
		if repeat_check_result[0] is not 'success':
			return JsonResponse(simplejson(code=101, msg=repeat_check_result[1]), safe=False)


def getkey(d, key):
	for k in d:
		if key.lower() == k.lower():
			return k
	return None
