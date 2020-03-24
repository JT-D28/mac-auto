import re


class JSONParser():
	
	def __init__(self, data):
		
		# print("传入=>",data)
		self.obj = eval(self._apply_filter(data))
		
		# 兼容不同的系统 有些系统喜欢返回JSON字符串 有些json
		for i in range(5):
			if isinstance(self.obj, (str,)):
				self.obj = eval(self.obj)
		
		# print('==JSONParser 数据转字典=>',self.obj,type(self.obj))
		
		# print("待匹配数据=>",self.obj)
	
	def _apply_filter(self, msg):
		# print("leix=",type(msg))
		msg = msg.replace("true", "True").replace("false", "False").replace("null", "None")
		# print(msg)
		return msg
	
	def translate(self, chainstr):
		
		def is_ok(chainstr):
			stages = chainstr.split(".")
			for x in stages:
				if len(re.findall("^[0-9]\d+$", x)) == 1:
					return False
			return True
		
		if is_ok(chainstr) == True:
			h = ''
			if isinstance(self.obj, (list,)):
				if chainstr.startswith('response.json'):
					startindex = re.findall('response.json\[(.*?)\]', chainstr)[0]
					h = "[%s]" % startindex
					chainstr = chainstr.replace('response.json%s.' % h, '')
			
			stages = chainstr.split(".")
			return "self.obj%s." % h + ".".join(
				["get('%s')[%s" % (stage.split("[")[0], stage.split("[")[1]) if "[" in stage else "get('%s')" % stage
				 for stage in stages])
		
		else:
			return False
	
	def getValue(self, chainstr):
		errms = '解析数据链[%s]失败 数据链作为值返回' % chainstr
		xpath = self.translate(chainstr)
		if xpath:
			print('==当前数据类型=>%s' % type(self.obj))
			# try:
			
			#     print('flag=>',self.obj.get('data','None'))
			# except:
			#     pass
			print("==xpath查询=>%s" % xpath)
			try:
				r = eval(xpath)
				return r
			except:
				print(errms)
				return chainstr
		else:
			print(errms)
			return chainstr


_m = [
	"{'code':1,'a':[{'k':1},{'j':''}]}",

]

_m2 = {
	"[{'code':1},{'code':2,'vk':'et'}]"
}

for _ in _m2:
	print(100 * '=')
	p = JSONParser(_)
	print(p.getValue('response.json[1].vk'))
	# print(p.getValue('a[0].j'))
