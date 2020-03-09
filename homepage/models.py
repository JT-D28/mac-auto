from django.db.models import *
from login import models as md


class Jacoco_report(Model):
	jenkinsurl = CharField(max_length=64,blank=True,null=True)
	jobname=TextField(blank=True,null=True)
	productid=CharField(max_length=12,blank=True)
	authname=CharField(max_length=24,blank=True,null=True)
	authpwd=CharField(max_length=24,blank=True,null=True)
	createtime = DateTimeField(auto_now_add=True)
