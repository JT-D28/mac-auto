import json

from django.db import transaction

from manager.models import Variable, Tag, Product, Plan, Varspace, Order


# select * from (SELECT var_id,count(*) as t FROM `manager_tag` GROUP BY var_id)b  where t>1
def varUpdate():
	if not Varspace.objects.filter(name="全局").first():
		Varspace(name="全局").save()
	
	for var in Variable.objects.all():
		print(var.id)
		judgetag = Tag.objects.filter(var_id=var.id)
		if not judgetag.first():
			var.delete()
			continue
		tag = judgetag.first()
		planids = eval(tag.planids)
		tempPlanids = eval(tag.planids)
		for k, v in planids.items():
			plan = Plan.objects.filter(id=v[1])
			if not plan.exists():
				if len(planids.keys()) == 1:
					tag.delete()
					var.delete()
					continue
				else:
					del tempPlanids[k]
					tag.planids = json.dumps(tempPlanids, ensure_ascii=False)
					tag.save()
			tag.planids = json.dumps(tempPlanids, ensure_ascii=False)
			tag.save()
			if plan.exists():
				p = plan[0]
				print("计划  ", p.id)
				oex = Order.objects.filter(follow_id=p.id, kind='product_plan').exists()
				if not oex:
					p.delete()
					var.delete()
					continue
				
				spacename = p.description + "_%s" % Product.objects.get(
					id=Order.objects.get(follow_id=p.id, kind='product_plan').main_id).description
				if not Varspace.objects.filter(name=spacename, planid=p.id).exists():
					vs = Varspace(name=spacename, planid=p.id)
					vs.save()
					p.varspace = vs.id
					p.save()
	
	gsid = Varspace.objects.get(name="全局").id
	
	for var in Variable.objects.all():
		judgetag = Tag.objects.filter(var_id=var.id)
		if not judgetag.first():
			var.delete()
			continue
		tag = judgetag.first()
		if tag.customize != "Tag object (None)":
			list = []
			for i in tag.customize.split(";"):
				if i != '':
					list.append(i)
			var.label = ",".join(list)
		else:
			var.label = ""
		planids = eval(tag.planids)
		if tag.isglobal == 1 and len(planids.keys()) == 0:
			var.space_id = gsid
			var.save()
		else:
			if len(planids.keys()) > 1:
				for k, v in planids.items():
					plan = Plan.objects.get(id=v[1])
					
					spacename = plan.description + "_%s" % Product.objects.get(
						id=Order.objects.get(follow_id=plan.id, kind='product_plan').main_id).description
					
					newVar = Variable()
					newVar.description = var.description
					newVar.key = var.key
					newVar.value = var.value
					newVar.gain = var.gain
					newVar.is_cache = var.is_cache
					newVar.createtime = var.createtime
					newVar.author_id = var.author_id
					newVar.space_id = Varspace.objects.get(name=spacename).id
					newVar.label = var.label
					newVar.save()
				var.delete()
			
			else:
				for k, v in planids.items():
					plan = Plan.objects.get(id=v[1])
					spacename = plan.description + "_%s" % Product.objects.get(
						id=Order.objects.get(follow_id=plan.id, kind='product_plan').main_id).description
					var.space_id = Varspace.objects.get(name=spacename).id
					var.save()


def spaceUpdate():
	vs = Varspace.objects.exclude(name="全局")
	
	for v in vs:
		if Variable.objects.filter(space_id=v.id).count() == 0:
			v.delete()
			continue
		planname = v.name.split("_")[0]
		productname = v.name.replace(planname+"_","")
		print(planname,productname)
		spaces = Varspace.objects.filter(name__istartswith=planname)
		if len(spaces)>1:
			v.name = planname+'[%s]'%productname
		else:
			v.name = planname
		v.save()
		
