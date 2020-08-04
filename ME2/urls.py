"""ME2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve

from ME2.settings import STATIC_ROOT
from ME2.settings import DEBUG
from login import views

urlpatterns = [
	url(r'^static/(?P<path>.*)$', serve, {'document_root': STATIC_ROOT}),
	path('admin/', admin.site.urls),
	path('', views.index),
	path('account/', include('login.urls')),
	path('manager/', include('manager.urls')),
	path('homepage/', include('homepage.urls')),
	url(r'^file/(?P<filename>.*?)$', views.getfile),
	path('test_expression/', views.testexpress),
	path('test_expression1/', views.testexpress1),
	path('test_expression2/', views.testexpress2),
	path('test_xml/', views.testxml),
	path('mocktimeout/', views.mocktimeout),
	path('updateauth/', views.updateroledata),
	path('test_hz/',views.query_test_count_info),
	# path('',views.index),

]

if DEBUG:
	import debug_toolbar
	urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))


try:
	from manager.operate.cron import Cron
	Cron.recovertask()
except:
	pass

# handler404 = views.page_not_found
# handler500 = views.page_error
