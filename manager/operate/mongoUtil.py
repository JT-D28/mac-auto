from pymongo import MongoClient

from ME2 import configs


class Mongo():
	host = configs.MONGO_HOST
	port = configs.MONGO_PORT
	mongocon = MongoClient(host, int(port))

##############################################
	#这个库存放原始日志文件和匹配分割以后的日志文件，因为单个任务内容比较多，每个任务对应一个集合，可以定期删除（1个月） 返回的对象是库中名为taskid的集合
	@classmethod
	def tasklog(cls,taskid):
		return cls.mongocon.log[taskid]

##############################################
	# 这个库存放匹配分割以后的日志文件，每个任务对应一个集合，可以定期删除（1个月） 主要用作中间临时过渡，生成一份统计数据 返回的对象是库中名为taskid的集合
	@classmethod
	def logsplit(cls,taskid):
		return cls.mongocon.logsplit[taskid]

##############################################
	# 这个集合 plandata 存放计划历史的每次任务汇总数据（成功率，总数。。。），全放在一张表里面返回的对象是 taskinfo 集合
	@classmethod
	def taskResult(cls):
		return cls.mongocon.apiTest['result']

	# 这个集合 plandata 存放计划历史的每次任务汇总数据（成功率，总数。。。），全放在一张表里面返回的对象是 taskreport 集合
	@classmethod
	def taskreport(cls):
		return cls.mongocon.apiTest['report']
	
	@classmethod
	def taskRecords(cls):
		return cls.mongocon.apiTest['records']
	
	@classmethod
	def taskid(cls):
		return cls.mongocon.apiTest['taskid']
	
	@classmethod
	def performanceTaskId(cls):
		return cls.mongocon.plandata['loadTask']