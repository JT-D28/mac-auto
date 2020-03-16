from django.contrib import admin

from . import models
# Register your models here.
admin.site.register(models.Interface)
admin.site.register(models.Step)
admin.site.register(models.Case)
admin.site.register(models.Plan)
admin.site.register(models.Variable)
# admin.site.register(models.Result)
admin.site.register(models.Function)
admin.site.register(models.ResultDetail)
admin.site.register(models.Tag)
admin.site.register(models.Order)