from django.db import models
from login import models as md


class Jacoco_report(models.Model):
    jenkinsurl = models.CharField(max_length=64,blank=True,null=True)
    jobname=models.CharField(max_length=32,blank=True,null=True)
    productid=models.CharField(max_length=12,blank=True)
    authname=models.CharField(max_length=24,blank=True,null=True)
    authpwd=models.CharField(max_length=24,blank=True,null=True)
    createtime = models.DateTimeField(auto_now_add=True)
