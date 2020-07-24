from pymongo import MongoClient

from ME2.settings import MONGO_HOST, MONGO_PORT


class Mongo():
	host = MONGO_HOST
	port = MONGO_PORT
	mongocon = MongoClient(host, int(port))

	# self.con.authenticate("chy", "123456", source='test')
	@classmethod
	def tasktree(cls,taskid):
		return cls.mongocon.tasktree[taskid]

	@classmethod
	def tasklog(cls,taskid):
		return cls.mongocon.tasklog[taskid]

	@classmethod
	def taskinfo(cls,taskid):
		return cls.mongocon.taskinfo[taskid]

	@classmethod
	def logspilt(cls,taskid):
		return cls.mongocon.logspilt[taskid]

	@classmethod
	def taskreport(cls,taskid):
		return cls.mongocon.taskreport[taskid]
