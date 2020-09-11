from django.conf.urls import url
from django.urls import path
from . import views

urlpatterns = [
	path('login/', views.login),
	path('getCsrfToken/', views.getCsrfToken),
	path('logout/', views.logout),
	path('userRoute/', views.userRoute),
	
	path('addaccount/', views.addaccount),
	path('delaccount/', views.delaccount),
	path('editaccount/', views.editaccount),
	path('queryaccount/', views.queryaccount),
	path('queryoneaccount/', views.queryoneaccount),
	
	path('queryRoles/', views.queryRoles),
	path('addRole/', views.addRole),
	path('editRole/',views.editRole),
	path('delRoles/', views.delRoles),
	path('queryOneRole/', views.queryOneRole),
	
	path('queryPermissions/', views.queryPermissions),
	path('addPermission/', views.addPermission),
	path('editPermission/', views.editPermission),
	path('delPermissions/',views.delPermissions),
	
	path('addMenu/', views.addMenu),
	path('editMenu/', views.editMenu),
	path('delMenu/', views.delMenu),
	path('queryMenus/', views.queryMenus),
	
	url(r'^getbusinessnum/(?P<id>.*?)/(?P<total>.*?)$', views.getbusinessnum),

]
