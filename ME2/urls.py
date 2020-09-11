from django.conf.urls import url
from django.urls import path, include
from login import views

urlpatterns = [
	path('account/', include('login.urls')),
	path('manager/', include('manager.urls')),
	path('homepage/', include('homepage.urls')),
	url(r'^file/(?P<filename>.*?)$', views.getfile),

]

try:
	from manager.operate.cron import Cron
	from tools.test import TreeUtil
	Cron.recovertask()
	TreeUtil.clear_cache()
except:
	pass


