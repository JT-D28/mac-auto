#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2020-02-17 09:51:22
# @Author  : Blackstone
# @to      :


def user_operation_intercept(request):
	'''用户操作拦截
	'''


	##普通url拦截


	##拦截的url带指定参数

	##




	##


	return {
	'result':'block',
	'msg':''
	}



def web_el_intercept(request)
	'''
	页面元素拦截
	'''
	return{

	'result':'pass',
	'msg':''
	}







# from .manager.models import *
# import traceback
# def add_participant(product_id,p_id,kind='user'):
# 	L=[]

# 	if 'user'==kind:
# 		L=list(HumanResource.objects.filter(user_id=p_id,product_id=product_id,kind=kind))
# 	else:
# 		L=list(HumanResource.objects.filter(group_id=p_id,product_id=product_id,kind=kind))		

# 	if len(L)==0:
# 		h=HumanResource()
# 		h.product_id=product_id
# 		h.kind=kind
# 		if 'user'==kind:
# 			h.user_id=p_id
# 		else:
# 			h.group_id=p_id

# 		h.save()
# def del_participant(p_id,product_id,kind='user'):
# 	try:
# 		if 'user'==kind:
# 			HumanResource.objects.get(user_id=pid,kind=kind,product_id=product_id).delete()
# 		else:
# 			HumanResource.objects.get(group_id=pid,kind=kind,product_id=product_id).delete()

# 	except:
# 		print('删除参与者异常=>',traceback.format_exec())


# def can_view_product(user_id):
# 	pass



# def can_view_varibale(user_id):
# 	pass



# def can_view_function(user_id):
# 	pass



# def can_view_dbconnect(user_id):
# 	pass