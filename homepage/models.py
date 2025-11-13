from django.db.models import *
from login import models as md


class Jenkins(Model):
	jenkinsurl = CharField(max_length=128, blank=True, null=True)
	jobname = TextField(blank=True, null=True)
	productid = CharField(max_length=12, blank=True)
	authname = CharField(max_length=24, blank=True, null=True)
	authpwd = CharField(max_length=24, blank=True, null=True)
	createtime = DateTimeField(auto_now_add=True)
	clearjob = CharField(max_length=128, blank=True, null=True)
	buildplans=TextField(blank=True)
	projectjob = TextField(blank=True, null=True)
	gitlaburl =  CharField(max_length=128, blank=True, null=True)
	gitlabtoken = CharField(max_length=64, blank=True, null=True)
	gitpath = CharField(max_length=64, blank=True, null=True)
	gitbranch = CharField(max_length=64, blank=True, null=True)


class Jacoco_data(Model):
	jobname = CharField(max_length=128)
	jobnum = CharField(max_length=32)
	coverydata = TextField(blank=True)
	time = CharField(blank=True,max_length=32)
	# branchCoverage = CharField(max_length=128)
	# classCoverage = CharField(max_length=128)
	# complexityScore = CharField(max_length=128)
	# instructionCoverage = CharField(max_length=128)
	# lineCoverage = CharField(max_length=128)
	# methodCoverage = CharField(max_length=128)
