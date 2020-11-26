import json

import consul
from django.conf.urls import url
from django.urls import path, include

from ME2 import configs
from ME2.DataUpdate import varUpdate, spaceUpdate
from login import views
from rpc4django.views import serve_rpc_request
from xmlrpc.client import ServerProxy
urlpatterns = [
	path('account/', include('login.urls')),
	path('manager/', include('manager.urls')),
	path('homepage/', include('homepage.urls')),
	path('performance/',include('performance.urls')),
	url(r'^file/(?P<filename>.*?)$', views.getfile),
	url(r'^RPC$', serve_rpc_request),

]


# 启动时执行
try:
	from manager.operate.cron import Cron
	from tools.test import TreeUtil
	Cron.recovertask()
	TreeUtil.clear_cache()
except:
	pass

c = consul.Consul(host=configs.Consul_ADDR,port=int(configs.Consul_PORT),scheme='http')
c.kv.put(configs.ID,json.dumps(configs.WorkerInfo,ensure_ascii=False))

# varUpdate()
#
# spaceUpdate()