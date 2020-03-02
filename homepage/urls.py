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
from django.contrib import admin
from django.urls import path

from . import views
from manager import views as mv

urlpatterns = [
    # path('login/',views.login),
    path('', views.homepage),
    path('queryproduct/', views.queryproduct),
    path('queryplan/', views.queryplan),
    path('querytaskid/', views.querytaskid),
    path('process/',views.process),
    path('globalsetting/', views.globalsetting),
    path('restart/', views.restart),
    path('sendreport/',views.sendreport),
    path('reportchart/', views.reportchart),
    path('badresult/',views.badresult),
    path('plandebug/', views.plandebug),
    path('buglog/',views.querybuglog),
    path('initbugcount/',views.initbugcount),
    path('downloadlog/',views.downloadlog),
    path('jacocoreport/',views.jacocoreport),
    path('queryProductSet/',views.queryProductSet),
    path('editProductSet/',views.editProductSet),
    path('downloadReport/',views.downloadReport),
    path('queryPlanState/',views.queryPlanState),
    path('planforceStop/',views.planforceStop),
    path('query_third_call/',views.query_third_call)
]
