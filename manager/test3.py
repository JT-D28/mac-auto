#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-08-29 08:43:52
# @Author  : Blackstone
# @to      :

import re

def md5_encrypt(str_):
	from hashlib import md5
	return md5(str_.encode('utf-8')).hexdigest()

# print(md5_encrypt('1'))
def _is_function_call(call_str):
	'''
	判断获取方式类别
	1.是否有空格
	2.是否带()
	'''
	try:
		m=re.findall("\((.*?)\)",call_str)
		for _ in m[0].split(','):
			try:
				eval(_)

			except:
				return False

				

		call_str=call_str.replace(m[0],'')
		prefix=call_str.split("()")[0]

		if prefix.__contains__(' '):
			return False

		call_str=call_str.replace(prefix, 'a')
		return True if 'a()'==call_str else False
	except:
		return False

L=[
'a()',
'a({{vv}})',
"a(1,2)",
"a(1,{{v}})",
"a('1',{{v}})",
"a('1')",

"a(k)"
"a k(1)",
"select id from A",
"select a.id from A a left join(select * from B)b on a.id=b.id"
]

for _ in L:
	print(_is_function_call(_))