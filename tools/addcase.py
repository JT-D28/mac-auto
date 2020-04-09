#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-10-21 11:21:19
# @Author  : Blackstone
# @to      :

import xlrd, requests, requests, re

##

step_type = None
description = ''
url = ''
method = ''
header = ''
body = ''
content_type = ''
itf_check = ''
db_check = ''
tmp = ''
tagname = ''
author = ''

##
var_all = set()

var_replace = {
	'creator_id': 'admin_id',
	'account_state_1': 'account_state_new',
	'account_state_2': 'account_state_open',
	'account_detail_id': 'bank_detail_id',
	'directbank_code': 'direct_bank_code',
	'report_date': 'date',
	'date_opened': 'date',
	'post_date_time': 'time',
	'account_useage_code': 'account_type_code',
	'account_useage_name': 'account_type_name',
	'account_useage_id': 'account_type_id',
	'agreementid': 'agreement_id',
	'packagecode': 'package_code',
	'packageid': 'package_id',
	'packagename': 'package_name',
	'tenantcode': 'tenant_code',
	'tenantid': 'tenant_id',
	'tenantname': 'tenant_name',
	'banklocation_code': 'bank_location_code',
	'banklocation_id': 'bank_location_code',
	'banklocation_name': 'bank_location_name',
	'money_type_code': 'currency_code',
	'money_type_name': 'currency_name',
	'money_type_id': 'currency_id',
	'paytype_id': 'pay_type_id',
	'paytype_name': 'pay_type_name',
	'businesssystem_id': 'business_system_id',
	'businesssystem_name': 'business_system_name',
	'categoryrange_id': 'category_range_id',
	'recaccount_id': 'receive_account_id',
	'ownaccount_id': 'pay_account_id',
	'payconfig_id': 'pay_type_config_id',
	'paytype_config_id': 'pay_type_config_id',
	'paytype_code': 'pay_type_code',
	'defaultcapitalus_id': 'default_capitalus_id',
	'proc_id': 'proc_type_id',
	'proc_name': 'proc_type_name',
	'proc_parent_name': 'proc_type_parent_name',
	'proc_parent_id': 'proc_type_parent_id',
	'assign_id': 'agent_id',
	'assign_name': 'agent_name',
	'assign_code': 'agent_code',
	'apply_define_id': 'auto_up_config_id',
	'apply_define_id2': "auto_down_config_id",
	'fundapply_edit_urid': 'fundapply_id',
	'psselnums': "psselnum_id",
	'accountname': 'account_name',
	'accountnumber': 'account_number',
	'accountsUrid': 'account_id',
	'accounttypeUrid': 'account_type_id',
	'currencyUrid': 'currency_id',
	'orgCode': 'org_code',
	'packageUrid': "package_id",
	'roleCode': 'role_code',
	'roleUrid': 'role_id',
	'taskId': 'task_id',
	'tenantUrid': 'tenant_id',
	'userCode': 'user_code',
	'userName': 'user_name',
	'userUrid': 'user_id',
	'procInstId': 'prc_inst_id',
	'data': 'date',
	'dataf21': 'date_after_21'
	
}
functionnames = ['dbexecute', 'dbexecute2', 'sleep']


def floathandle(params):
	'''
	is打头key的值做int处理
	'''
	for k, v in params.items():
		
		if isinstance(v, (float)):
			params[k] = int(v)
	
	return params


def replace_var(varstr):
	var_pattern = ['{u,lv_(.*?)}']
	# target='{u,lv_k_t}'
	target = varstr
	for x in var_pattern:
		ms = re.findall(x, target)
		for m in ms:
			if m in var_replace:
				target = target.replace("{u,lv_%s}" % m, "{{%s}}" % var_replace.get(m))
				var_all.add(var_replace.get(m))
			else:
				target = target.replace("{u,lv_%s}" % m, "{{%s}}" % m)
				var_all.add(str(m))
	
	return target


##
tagname = 'ats7.0_san'
author = 'tester'
url_base = '{{base_url}}'
var_pattern = ['{u,lv_(.*?)}']

##用例
case_url = r'C:\Users\F\git\AutoTestFramework_openpyxl\src\TestCase\ats7.0-san.xlsx'
book = xlrd.open_workbook(case_url)  # 打开要读取的Excel
sheet = book.sheet_by_name('执行数据')  # 打开sheet页
rows = sheet.nrows  # sheet页里面的行数

###配置
config_url = r'C:\Users\F\git\AutoTestFramework_openpyxl\src\Config\Config(8).xlsx'
book2 = xlrd.open_workbook(config_url)
url_sheet = book2.sheet_by_name("Scripts")
url_sheet_rows = url_sheet.nrows
url_set = {}
for x in range(1, url_sheet_rows):
	rowobj = url_sheet.row_values(x)
	url_set[rowobj[0]] = rowobj[1].split(",")[0]

# print(url_set)


for i in range(1, rows):
	step_type = None
	description = ''
	url = ''
	method = ''
	header = ''
	body = ''
	content_type = ''
	itf_check = ''
	db_check = ''
	tmp = ''
	# tagname=''
	author = ''
	rowobj = sheet.row_values(i)
	# print(rowobj)#获取第几行的数据
	count = int(rowobj[3])
	if count < 1:
		continue
	description = rowobj[5]
	funcname = rowobj[4]
	casename = rowobj[5]
	route = rowobj[6]
	
	if funcname not in functionnames:
		# print("$name=>",route.split(":")[0])
		sheet_1 = book.sheet_by_name(route.split(":")[0])
		titles = sheet_1.row_values(0)
		# print(titles)
		rowindex = int(route.split(":")[1])
		# print(sheetname)
		
		rowobj_1 = sheet_1.row_values(rowindex)
		# print(rowobj_1)
		db_check = rowobj_1[2]
		itf_check = rowobj_1[4]
		
		step_type = 'interface'
		url = url_set.get(funcname, '')
		method = 'post'
		content_type = 'urlencode'
		header = '{"Authorization":"${auth}"}'
		
		params = {}
		index = 4
		# print(rowobj_1[5:])
		for p in rowobj_1[5:]:
			# print(p)
			index = index + 1
			key = titles[index]
			params[key] = p
		
		params = floathandle(params)
		body = replace_var(str(params))
	
	else:
		step_type = 'function'
	
	# 调用add接口
	itf_url = 'http://10.60.45.93:8000/manager/addstep/'
	data = {
		'step_type': step_type,
		'description': description,
		'url': url_base + url,
		'method': method,
		'headers': header,
		'body': body,
		'content_type': 'urlencode',
		'itf_check': itf_check,
		'db_check': db_check,
		'tmp': '',
		'tag': tagname,
		'username': 'tester'
		
	}
	
	print(data)
	# print(tagname)
	
	rps = requests.get(itf_url, params=data)
	print(description, rps.status_code, body)
# print(description,body)
# print('\n')

# print('描述=>',description)
# print("执行次数=>",int(count))
# print('url=>',url)
# print('header=>',header)
# print('body=>',params)
# print('method=>',method)
# print('content_type=>',content_type)
# print('db_check=>',db_check)
# print('itf_check=>',itf_check)
# print('--'*20)

print('*' * 20 + '\n')
a = list(var_all)
a.sort()
print(a)
