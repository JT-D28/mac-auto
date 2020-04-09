#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2020-02-17 09:51:22
# @Author  : Blackstone
# @to      :权限管理

import os, traceback
from login.models import *
from django.db.models import Q


class Grant(object):
	
	@classmethod
	def _isconfig():
		return 'NO'
	
	@classmethod
	def _add_ui_control_user(cls, ucid, userlist):
		try:
			for userstr in userlist:
				uir = User_UI_Relation()
				uir.kind = userstr.split('_')[0]
				uir.uc_id = ucid
				uir.user_id = userstr.split('_')[1]
				uir.save()
		
		except:
			print(traceback.format_exc())
			raise RuntimeError('ui权限关联用户异常.')
	
	@classmethod
	def _update_ui_control_user(cls, ucid, updateuserlist):
		try:
			has_user = dict()
			L = list(User_UI_Relation.objects.filter(uc_id=ucid))
			for u in L:
				has_user[u.id] = '%s_%s' % (u.kind, u.user_id)
			
			need_add = [x for x in updateuserlist if x not in list(has_user.values())]
			need_del = [x for x in list(has_user.values()) if x not in updateuserlist]
			
			for x in need_add:
				uir = User_UI_Relation()
				uir.uc_id = ucid
				uir.kind = x.split('=')[0]
				uir.user_id = x.split('=')[1]
				uir.save()
			
			for x in need_add:
				uir = User_UI_Relation.objects.get(kind=x.split('=')[0], user_id=x.split('=')[1])
		except:
			raise RuntimeError('更新视图控制用户信息异常')
	
	@classmethod
	def add_ui_control(cls, **config):
		try:
			uc = UIControl()
			uc.code = config['code']
			uc.description = config['description']
			uc.is_config = cls._isconfig()
			uc.author = config['creater']
			uc.save()
			cls._add_ui_control_user(uc.id, config['userstrs'].split(','))
			
			return {
				'code': 0,
				'msg': '新增权限[%s]成功' % uc.description
			}
		
		except:
			err = traceback.format_exc()
			print(err)
			return {
				'code': 4,
				'msg': '新增权限异常[%s]' % err
			}
	
	@classmethod
	def del_ui_control(cls, ucid):
		try:
			uc = UIControl.objects.get(code=ucid)
			dl = list(User_UI_Relation.objects.filter(ucid=uc.id))
			for x in dl:
				x.delete()
			
			uc.delete()
			return {
				'code': 0,
				'msg': '删除权限[%s]成功' % uc.description
			}
		
		except:
			err = traceback.format_exc()
			print(err)
			return {
				'code': 4,
				'msg': '删除权限异常[%s]' % err
			}
	
	@classmethod
	def edit_ui_control(cls, **config):
		try:
			uc = UIControl.objects.get(id=config['cid'])
			uc.code = config['code']
			uc.description = config['description']
			uc.is_config = cls._isconfig()
			uc.save()
			
			cls._update_ui_control_user(uc.id, config['userstrs'].split(','))
			return {
				'code': 0,
				'msg': '编辑权限[%s]成功' % uc.description
			}
		
		except:
			err = traceback.format_exc()
			print(err)
			return {
				'code': 4,
				'msg': '编辑权限异常[%s]' % err
			}
	
	@classmethod
	def query_ui_grant_table(cls, searchvalue=None):
		try:
			data = list()
			uicall = []
			if searchvalue:
				uicall = list(
					UIControl.objects.filter(Q(code__icontains=searchvalue) | Q(description__icontains=searchvalue)))
			else:
				uicall = UIControl.objects.all()
			for x in uicall:
				datax = dict()
				datax['code'] = x.code
				datax['description'] = x.description
				datax['author'] = x.author
				
				userstr = []
				uirlist = list(User_UI_Relation.objects.filter(uc_id=x.id))
				for y in uirlist:
					userstr.append('%s_%s' % (y.kind, y.user_id))
				
				datax['user'] = ','.join(userstr)
				datax['isconfig'] = cls._isconfig()
				data.append(datax)
			
			return {
				'code': 0,
				'msg': '',
				'data': data
			}
		except:
			return {
				'code': 4,
				'msg': 'UI权限表查询异常[%s]' % traceback.format_exc()
			}
