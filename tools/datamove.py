# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# # @Date    : 2019-12-03 11:21:19
# # @Author  : Blackstone
# # @to      :
# import xlrd,datetime,traceback
# from .manager.core import EncryptUtils,getbuiltin
# from .manager.models import *
# from .login.models import *

# class A:
# 	def es(self):
# 		print('es say..')

# class Transformer:

# 	_businessid_cache=dict()

# 	def __init__(self,callername,byte_list,content_type):
# 		print('【Transformer工具初始化】')
# 		self._set_content_type_flag(content_type)

# 		self._before_transform_check_flag=[]
# 		self._difference_config_file(byte_list)

# 		self.transform_id=EncryptUtils.md5_encrypt(str(datetime.datetime.now()))
# 		self.callername=callername
# 		self.act_data=self._get_workbook_sheet_cache(self.data_workbook,'执行数据')
# 		self.var_data=self._get_workbook_sheet_cache(self.data_workbook,'变量定义')
# 		self.is_xml=is_xml
# 		self.is_json=is_json


# 	def _difference_config_file(self,byte_list):
# 		'''
# 		区分配置文件&用例文件
# 		'''
# 		try:
# 			for byte in byte_list:
# 				cur_workbook=xlrd.open_workbook(file_contents=byte)
# 				global_sheet=cur_workbook.sheet_by_name('Global')
# 				if global_sheet:
# 					self.config_workbook=cur_workbook
# 				else:
# 					if self.data_workbook is None:
# 						self.data_workbook=[]
# 					else:
# 						self.data_workbook.append(cur_workbook)


# 			##校验文件

# 			if self.config_workbook is None:
# 				return ('fail','没上传配置文件 请检查')

# 			if self.data_workbook is None or len(self.data_workbook)==0:
# 				return ('fail','没上传用例文件 请检查')

# 			return('success','')

# 		except:
# 			return ('error','区分配置文件和用例文件发生异常=>%s'%traceback.format_exc())


# 	def _check_file_valid(self):
# 		"""
# 		检查文件是否合法
# 		"""
# 		for flag in self._before_transform_check_flag:
# 			if flag.get(0,None)!='success':
# 				return flag

# 		return ('success','')


# 	def _set_content_type_flag(self,kind):
# 		#kind=('json','xml','urlencode','not json','not xml','not urlencode')
# 		if kind=='json':
# 			self.is_json=True
# 			self.is_xml=False
# 		elif kind=='xml':
# 			self.is_xml=True
# 			self.is_json=False
# 		elif kind=='urlencode':
# 			self.is_xml=False
# 			self.is_json=False
# 		elif kind=='not_json':
# 			self.is_json=False
# 		elif kind=='not_xml':
# 			self.is_xml=False
# 		elif kind=='not_urlencode':
# 			self.is_json=True
# 			self.is_xml=True

# 	def _get_itf_basic_conifg(self):
# 		'''
# 		获取config init基本配置
# 		'''
# 		init_cache=self._get_workbook_sheet_cache(self.config_workbook,'Init')
# 		for rowdata in init_cache:
# 			if rowdata['默认对象']=='Y' and rowdata['对象类型']=='interface':
# 				pv=rowdata['参数']
# 				if self.isxml:
# 					return {
# 					'host':pv.split(',')[0],
# 					'port':pv.split(',')[1],

# 					}
# 				else:
# 					return {
# 					'host':pv.split(',')[0]

# 					}


# 	def _get_itf_detail_config(self):
# 		'''	
# 		获取接口具体配置信息

# 		'''
# 		res={}

# 		script_cache=self._get_workbook_sheet_cache(self.config_workbook, 'Scripts')
# 		for rowdata in script_cache:
# 			rowdatalist=rowdata['脚本全称'].split(',')

# 			path=rowdatalist[0]
# 			method=rowdatalist[1]
# 			content_type='urlencode'

# 			if len(rowdatalist)>2:
# 				content_type=rowdatalist[2]


# 			res[rowdata['脚本简称']]={
# 			'path':path,
# 			'method':method,
# 			'content_type':content_type
# 			}

# 		return res

# 	def _get_workbook_sheet_cache(self,workbook,sheetname):
# 		"""
# 		获取sheet键值数据
# 		"""

# 		cache=[]

# 		sheet=workbook.sheet_by_name(sheetname)
# 		sheet_rows=sheet.nrows
# 		titles=sheet.row_values(0)
# 		title_order_map={}
# 		for index in range(len(titles)):
# 			title_order_map[str(index)]=str(titles[index])
# 		# print('titles=>',title_order_map)


# 		for rowindex in range(1, sheet_rows):
# 			row_map={}
# 			row=sheet.row_values(rowindex)
# 			for cellindex in range(len(row)):
# 				row_map[title_order_map[cellindex]]=row[cellindex]

# 			cache.append(row_map)


# 		# print(kv_map)
# 		return cache

# 	def _get_business_sheet_cache(self):
# 		'''
# 		获取业务数据缓存
# 		'''
# 		cache={}
# 		sheets=self.data_workbook.sheet_names()
# 		for sheetname in sheets and sheetname not in ('变量定义','执行数据'):
# 			cache[sheetname]=self._get_workbook_sheet_cache(self.data_workbook, sheetname)

# 		return cache


# 	def transform(self):
# 		print('【准备数据转化】')

# 		status,msg=self._check_file_valid()
# 		print('【上传文件校验】status=%s msg=%s'%(status,msg))
# 		if status!='success':
# 			return (status,msg)

# 		print('【接收的数据集 开始转换】[%s,%s]'%(self.data_workbook,self.config_workbook))

# 		resultlist=[]

# 		f1=self.add_var()

# 		f2=self.addbusinessdata()

# 		f3=self.addstepdata()

# 		f4=self.add_case()

# 		f5=self.add_plan()

# 		resultlist.append(f1)
# 		resultlist.append(f2)
# 		resultlist.append(f3)
# 		resultlist.append(f4)
# 		resultlist.append(f5)

# 		for res in resultlist:
# 			print(res)

# 			if res[0]!='success':
# 				return res

# 		return ('success','转换成功')


# 	def addbusinessdata(self):
# 		'''
# 		插入业务数据
# 		'''
# 		try:
# 			print('【开始添加业务数据】')
# 			_meta=['测试点','DB检查数据','UI检查数据','接口检查数据','数据编号']
# 			_m={
# 			'测试点':'businessname',
# 			'DB检查数据':'db_check',
# 			'UI检查数据':'',
# 			'接口检查数据':'itf_check',
# 			'数据编号':''

# 			}
# 			for sheetname,cache in self._get_business_sheet_cache().items():
# 				rowindex=0
# 				for rowdata in cache:

# 					business=BusinessData()
# 					params={}
# 					for filedname,value in rowdata.items():
# 						if fieldname  in _m:
# 							if fieldname =='测试点':
# 								business.businessname=value
# 								continue
# 							elif fieldname=='DB检查数据':
# 								business.db_check=value
# 								continue
# 							elif fieldname=='接口检查数据':
# 								business.itf_check=value
# 								continue
# 						else:
# 							params[filedname]=value

# 					##没测试点列 业务名称取值
# 					if not  business.businessname:
# 						business.businessname='%s%s'%(sheetname,rowindex+1)

# 					if not self.is_json:
# 						params=params.get('json','{}')

# 					business.params=str(params)
# 					business.save()
# 					self._businessid_cache['%s:%s'%(sheetname,rowindex+1)]=business.id
# 					rowindex=rowindex+1

# 			return('success','')


# 		except:
# 			return ('error','插入业务数据异常=>%s'%traceback.format_exc())


# 	def _get_step_names(self):
# 		return [x for x in self.data_workbook.sheet_names() if x not in('变量定义','执行数据')]

# 	def addstepdata(self):
# 		'''
# 		添加step
# 		'''
# 		try:
# 			print('【开始添加步骤数据】')
# 			all_function=list(Function.objects.all())+getbuiltin()
# 			all_function_name=[x.name for x  in all_function]
# 			for rowdata in self.act_data:
# 				step=Step()
# 				step.author=User.objects.get(name=self.callername)

# 				func_field_value=rowdata['函数名称']
# 				if func_field_value  not in all_function_name:
# 					#接口
# 					basic_config=self._get_itf_basic_conifg()
# 					detail_config=self._get_itf_detail_config()
# 					step.step_type='interface'
# 					step.description=rowdata['参数值'].split(':')[0]
# 					step.content_type=detail_config.get('content_type','')
# 					step.method=detail_config.get('method', '')

# 					if self.is_xml:
# 						step.url='%s:%s'%(basic_config.get('host',''),basic_config.get('port',''))
# 					else:
# 						step.url="http://%s%s"%(basic_config.get('host',''),detail_config.get('path',''))

# 				else:
# 					#函数
# 					step.step_type='function'
# 					step.body=func_field_value
# 					step.description=rowdata['测试要点概要']
# 					step.related_id=Step.objects.get(name=step.body.strip()).id
# 				step.save()
# 		except:
# 			return ('error','添加步骤异常')

# 	def add_step_business_relation(self,step_id,business_id):
# 		'''
# 		步骤关联业务数据
# 		'''
# 		print('【步骤关联业务数据】')
# 		step=Step.objects.get(id=step_id)
# 		business=BusinessData.objects.get(id=business_id)
# 		step.businessdatainfo.add(business)

# 	def add_plan(self):
# 		try:
# 			print('【添加计划】')
# 			plan=Plan()
# 			plan.description='计划_%s_%s'%(self.callername,self.transform_id)
# 			plan.author=User.objects.get(name=self.callername)
# 			plan.save()
# 			return ('success','')

# 		except:
# 			return ('error','添加计划异常=>%s'%traceback.format_exc())

# 	def add_case(self):
# 		try:
# 			print('【添加用例】')
# 			case=Case()
# 			case.description='用例_%s_%s'%(self.callernames,self.transform_id)
# 			case.author=User.objects.get(naem=self.callername)
# 			case.save()

# 			return ('success','')

# 		except:
# 			return ('error','添加用例异常=>%s'%traceback.format_exc())

# 	def add_plan_case_relation(self,plan_id,case_id):
# 		print('【关联计划和用例】')
# 		plan=Plan.objects.get(id=plan_id)
# 		case=Case.objects.get(id=case_id)
# 		plan.cases.add(case)

# 		order=Order()
# 		order.kind='case'
# 		order.main_id=plan_id
# 		order.follow_id=case_id
# 		order.save()

# 	def add_case_businss_relation(self,case_id,business_id):
# 		print('【关联用例和业务数据】')
# 		case=Case.objects.get(id=case_id)
# 		business=BusinessData.objects.get(id=business_id)
# 		case.businessdatainfo.add(business)

# 		order=Order()
# 		order.kind='step'
# 		order.main_id=case_id
# 		order.follow_id=business_id
# 		order.save()

# 	def add_var(self):
# 		try:
# 			print('【开始添加变量】')
# 			var_cache=self._get_workbook_sheet_cache(self.data_workbook, '变量定义')
# 			for var in var_cache:
# 				description=var['变量说明']
# 				gain=var['获取方式']
# 				key=var['变量名称']
# 				value=var['值']
# 				# is_cache=False
# 				var=Variable()
# 				var.description=description
# 				var.key=key
# 				var.gain=gain
# 				if not gain:
# 					var.value=value
# 				var.save()
# 				return ('success','')
# 		except:
# 			return ('error','添加变量异常=>%s'%traceback.format_exc())


# 	def _rollback(self):
# 		"""
# 		转换失败回滚操作
# 		"""
# 		pass
