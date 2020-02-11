from .manager.models import *
import traceback
def add_participant(product_id,p_id,kind='user'):
	L=[]

	if 'user'==kind:
		L=list(HumanResource.objects.filter(user_id=p_id,product_id=product_id,kind=kind))
	else:
		L=list(HumanResource.objects.filter(group_id=p_id,product_id=product_id,kind=kind))		

	if len(L)==0:
		h=HumanResource()
		h.product_id=product_id
		h.kind=kind
		if 'user'==kind:
			h.user_id=p_id
		else:
			h.group_id=p_id

		h.save()
def del_participant(p_id,product_id,kind='user'):
	try:
		if 'user'==kind:
			HumanResource.objects.get(user_id=pid,kind=kind,product_id=product_id).delete()
		else:
			HumanResource.objects.get(group_id=pid,kind=kind,product_id=product_id).delete()

	except:
		print('删除参与者异常=>',traceback.format_exec())


def can_view_product(user_id):
	pass



def can_view_varibale(user_id):
	pass



def can_view_function(user_id):
	pass



def can_view_dbconnect(user_id):
	pass