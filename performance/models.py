from django.db.models import *


class Node(Model):
	"""
	节点
	"""
	name = CharField(max_length=64, null=False)
	kind = CharField(max_length=32, null=False)
	childs = CharField(max_length=256, null=False, blank=True)
	condition = CharField(max_length=256, null=False, blank=True)
	parent = IntegerField(null=False)


class NodeInfo(Model):
	node_id = IntegerField( unique=True, null=False)
	data = TextField(null=False, blank=True)
	# loop_number = IntegerField(max_length=255, unique=True, null=False)