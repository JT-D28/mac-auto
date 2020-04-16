#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2020-03-10 14:31:32
# @Author  : Blackstone
# @to 

from manager.models import Template, TemplateField
from login.models import User
from ME2.settings import logme
import os, re
from ftplib import FTP
from collections import OrderedDict
from .core import TemplateEncoder, TemplateFieldEncoder, getpagedata
import traceback, json

from manager.context import Me2Log as logger


class MessageParser(object):
	'''
	报文解析器
	'''
	_SYMBOL = ('>=', '<=', '!=', '==', '>', '<', '$')
	
	def __init__(self, parse_format: dict, waitcheckmessage, expectlist: list):
		
		self._parse_format = parse_format
		self.message = waitcheckmessage
		self._expectlist = expectlist
		
		logger.info('=====解析器初始化=========')
		logger.info('字段配置=>', self._parse_format)
		logger.info('带校验消息=>', self.message)
		logger.info('期望匹配=>', self._expectlist)
		logger.info('================')
	
	def _get_f_value(self, fcode) -> tuple:
		'''
		获取指定字段的值
		'''
		
		text = self.message
		if not text:
			return ('error', '待校验文件内容为空.')
		kind = self._parse_format.get('kind')
		
		if kind is None or kind == 'sepator':
			sep = self._parse_format.get('sep')
			
			findex = self._parse_format.get(fcode, None)
			if findex is None:
				return ('error', '字段[%s]没有配置' % fcode)
			idx = self._parse_format.get(fcode)
			if idx is None:
				return ('error', '使用的报文模板没有配置该字段[%s]' % fcode)
			
			if idx < 1:
				return ('error', '字段排序从数字1开始')
			
			pf = text.split(sep)[idx - 1]
			logger.info('解析模板字段[%s] value=%s' % (fcode, pf))
			return ('success', pf)
		
		elif kind == 'length':
			start, end = self._parse_format.get(fcode, (None, None))
			if start is None or end is None:
				return ('error', '字段[%s]配置错误' % fcode)
			
			logger.info('解析模板字段[%s] value=%s' % (fcode, text[int(start - 1):int(end)]))
			return ('success', text[int(start - 1):int(end)])
	
	def _compute_expression(self, child_exp: str):
		'''输入期望子表达式
			输出能正常eval化的字符串
		'''
		res = ''
		count = len(re.findall('=', child_exp))
		if count == 1:
			status, value = self._get_f_value(child_exp.split('=')[0])
			if status is not 'success':
				return (status, value)
			
			res = ''' '%s'%s'%s'  ''' % (value, '==', child_exp.split('=')[1])
		
		
		elif child_exp.__contains__('$'):
			status, value = self._get_f_value(child_exp.split('$')[0])
			if status is not 'success':
				return (status, value)
			
			res = ''' '%s'.__contains__('%s') ''' % (value, child_exp.split('$')[1])
		
		
		else:
			for _a in self._SYMBOL:
				if child_exp.__contains__(_a):
					status, value = self._get_f_value(child_exp.split(_a)[0])
					if status is not 'success':
						return (status, value)
					res = ''' '%s'%s'%s'  ''' % (value, _a, child_exp.split(_a)[1])
			
			res = '非法比较符'
		
		try:
			logger.info('获取计算表达式=>', res)
			o = eval(res)
			return ('success', o) if o is True else ('fail', '表达式[%s]不成立' % child_exp)
		except:
			return ('error', '表达式异常[%s]' % child_exp)
	
	def compute(self):
		'''
		计算表达式结果
		约定子表达式左->fcode 右->期望值
		返回所有子表达计算结果
		'''
		_ret = OrderedDict()
		for ex in self._expectlist:
			status, msg = self._compute_expression(ex)
			_ret[ex] = (status, msg)
		
		return _ret
	
	@classmethod
	def add_template(cls, **tkws):
		'''
		新建报文模板
		'''
		
		try:
			t = Template()
			t.kind = tkws['kind']
			t.name = tkws['name']
			t.description = tkws['description']
			t.author = tkws['author']
			
			t.save()
			return {
				'code': 0,
				'msg': '新增模板成功[%s]' % t
			}
		
		except:
			err = traceback.format_exc()
			logger.info(err)
			return {
				'code': 4,
				'msg': '新增模板异常'
			}
	
	@classmethod
	def del_template(cls, ids):
		'''删除报文模板
		'''
		try:
			for _ in str(ids).split(','):
				
				t = Template.objects.get(id=_)
				fl = list(t.fieldinfo.all())
				try:
					[_.delete() for _ in fl]
				except:
					pass
				try:
					t.delete()
				except:
					pass
			
			return {
				'code': 0,
				'msg': '删除模板成功'
			}
		
		
		
		except:
			error = '删除模板异常'
			logger.info(error + traceback.format_exc())
			
			return {
				'code': 4,
				'msg': error
			}
	
	@classmethod
	def edit_template(cls, **tkws):
		'''
		编辑模板
		'''
		try:
			tid = tkws['tid']
			t = Template.objects.get(id=int(tid))
			t.kind = tkws['kind']
			t.name = tkws['name']
			t.description = tkws['description']
			
			t.save()
			
			return {
				'code': 0,
				'msg': '编辑模板成功'
			}
		
		except:
			error = '编辑模板异常'
			logger.info(error + traceback.format_exc())
			return {
				'code': 4,
				'msg': error
			}
	
	@classmethod
	def query_template_common(cls, tid):
		try:
			t = Template.objects.get(id=tid)
			jsonstr = json.dumps(t, cls=TemplateEncoder)
			return jsonstr
		
		except:
			msg = '查询模板通用属性异常'
			logger.info(msg + traceback.format_exc())
			return {
				'code': 4,
				'msg': msg
			}
	
	@classmethod
	def query_template_name_list(cls):
		try:
			return {
				'code': 0,
				'msg': '',
				'data': [{
					'name': x.name,
					'value': x.id
					
				} for x in list(Template.objects.all())]
			}
		
		except:
			msg = '获取模板下拉信息异常'
			return {
				
				'code': 4,
				'msg': msg
			}
	
	@classmethod
	def query_template_field(cls, **kws):
		try:
			tid = int(kws.get('tid'))
			page = kws.get('page')
			limit = kws.get('limit')
			t = Template.objects.get(id=tid)
			fieldlist = list(t.fieldinfo.all())
			s = kws.get('searchvalue', None)
			if s:
				fieldlist = [x for x in fieldlist if x.fieldcode.__contains__(s)]
			
			res, total = getpagedata(fieldlist, page, limit)
			
			jsonstr = json.dumps(res, cls=TemplateFieldEncoder, total=total)
			
			return jsonstr
		
		
		except:
			error = '查询模板字段异常'
			logger.info(error + traceback.format_exc())
			return {
				'code': 4,
				'msg': error
			}
	
	@classmethod
	def _get_next_order(cls, tid):
		'''
		计算报文模板下个字段的排序号
		'''
		try:
			tflist = list(TemplateField.objects.filter(template=Template.objects.get(id=tid)))
			orderlist = [tf.order for tf in tflist]
			orderlist.sort()
			return ('success', int(int(orderlist[-1]) + 1))
		except:
			return ('error', '计算排序号[模板id=%s]异常' % tid)
	
	@classmethod
	def add_field(cls, **fkws):
		try:
			tid = fkws['tid']
			kind = fkws['kind']
			
			t = Template.objects.get(id=tid)
			
			tf = TemplateField()
			tf.fieldcode = fkws['fieldcode']
			tf.description = fkws['description']
			if kind == 'length':
				if not fkws['start'] or not fkws['end']:
					return {
						'code': 2,
						'msg': '开始结束字段必填'
					}
				tf.start = fkws['start']
				tf.end = fkws['end']
				tf.index = -1
			else:
				if not fkws['index']:
					return {
						'code': 2,
						'msg': '序号必填'
					}
				tf.index = fkws['index']
				tf.start = -1
				tf.end = -1
			
			tf.save()
			
			t.fieldinfo.add(tf)
			
			return {
				'code': 0,
				'msg': '新增字段成功'
			}
		
		except:
			return {
				'code': 4,
				'msg': '新增字段异常=>' + traceback.format_exc()
			}
	
	@classmethod
	def del_field(cls, ids):
		try:
			for _ in str(ids).split(','):
				tf = TemplateField.objects.get(id=int(_))
				# tmpl=list(tf.template_set.all())
				# logger.info('待删除模板=>',tmpl)
				# [_.delete() for _ in tmpl]
				tf.delete()
			
			return {
				'code': 0,
				'msg': '删除字段成功.'
			}
		except:
			return {
				'code': 4,
				'msg': '删除字段异常=>' + traceback.format_exc()
			}
	
	@classmethod
	def edit_field(cls, **fkws):
		try:
			tf = TemplateField.objects.get(id=fkws['fid'])
			tf.fieldcode = fkws['fieldcode']
			tf.description = fkws['description']
			if fkws['index']:
				tf.index = fkws['index']
			if fkws['start']:
				tf.start = fkws['start']
			if fkws['end']:
				tf.end = fkws['end']
			tf.save()
			
			return {
				'code': 0,
				'msg': '编辑字段成功.'
			}
		except:
			return {
				'code': 4,
				'msg': '编辑字段异常=>' + traceback.format_exc()
			}
	
	@classmethod
	def query_field_detail(cls, fid):
		try:
			ft = TemplateField.objects.get(id=int(fid))
			return json.dumps(ft, cls=TemplateFieldEncoder)
		except:
			error = '查询字段异常'
			logger.info(error + traceback.format_exc())
			return {
				'code': 4,
				'msg': error
			}
	
	# @classmethod
	# def move_up_or_down(cls,fid,direction='up'):
	#     '''
	#     字段上下移动
	
	#     '''
	#     try:
	#         move_step=(lambda:-1 if direction=='up' else 1)()
	#         tf=TemplateField.objects.get(id=fid)
	#         cur_order=tf.order
	#         t=tf.template
	#         expected=list(TemplateField.objects.filter(template=t,order=(cur_order+move_step)))
	
	#         if len(expected)==0:
	#             return ('success','边界移动忽略.')
	
	#         else:
	#             tf.order=cur_order+move_step
	#             tf.save()
	
	#             tf0=expected[0]
	#             tf0.order=tf0.order-move_step
	#             tf0.save()
	
	#             return {
	#             'code':0,
	#             'msg':"%s成功"%((lambda:'上移' if direction=='up' else '下移')())
	#             }
	
	#     except:
	#         return {
	#         'code':4,
	#         'msg':'移动异常=>'+traceback.format_exc()
	#         }
	
	@classmethod
	def get_parse_config(cls, templatename):
		'''
		获取模板具体的解析配置

		'''
		res = {}
		try:
			t = Template.objects.get(name=templatename)
			res['kind'] = t.kind
			res['sep'] = '||'
			tflist = list(TemplateField.objects.filter(template=t).order_by('index', 'start'))
			for tf in tflist:
				if t.kind == 'sepator':
					res[tf.fieldcode] = tf.index
				else:
					res[tf.fieldcode] = (tf.start, tf.end)
			
			return ('success', res)
		except:
			logger.info(traceback.format_exc())
			return ('error', '获取模板[%s]解析配置异常' % templatename)


if __name__ == '__main__':
	f = {'kind': 0, 'sep': '|', 'A': {
		'start': 0,
		'end': 12,
		'index': 1
	}}
	c = {}
	expected = ['a=111']
	m = MessageParser(f, c, expected)
	m.compute()
