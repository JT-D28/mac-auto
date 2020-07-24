from pymongo import MongoClient

from ME2.settings import MONGO_HOST, MONGO_PORT


class Mongo():
	host = MONGO_HOST
	port = MONGO_PORT
	mongocon = MongoClient(host, int(port))

	# self.con.authenticate("chy", "123456", source='test')
	@classmethod
	def tasktree(cls):
		print(cls.mongocon)
		return cls.mongocon.tasktree

	@classmethod
	def tasklog(cls):
		return cls.mongocon.tasklog

	@classmethod
	def taskinfo(cls):
		return cls.mongocon.taskinfo

	@classmethod
	def logspilt(cls):
		return cls.mongocon.logspilt

	@classmethod
	def taskreport(cls):
		return cls.mongocon.taskreport
