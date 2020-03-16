
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

urlpatterns = [

	path('help/',views.help),
	path('index/',views.index),

    path('datamove/',views.datamove),
    path('upload/',views.upload),
    path('querymovedata/',views.querymovedata),

    path('import/',views.dataimport),
    path('export/',views.dataexport),
    path('movein/',views.datamovnin),

    path('var/',views.var),
    path('queryvar/',views.queryvar),
    path('queryonevar/',views.queryonevar),
    path('addvariable/',views.addvar),
    path('delvar/',views.delvar),
    path('editvariable/',views.editvar),

    path('step/',views.step),
    path('queryonestep/',views.queryonestep),
    path('querystep/',views.querystep),
    path('addstep/',views.addstep),
    path('delstep/',views.delstep),
    path('editstep/',views.editstep),


    path('itf/',views.itf),
    path('addinterface/',views.additf),
    path('delitf/',views.delitf),
    path('queryitf/',views.queryitf),
    path('editinterface/',views.edititf),

    path('case/',views.case),
    path('addcase/',views.addcase),
    path('delcase/',views.delcase),
    path('queryonecase/',views.queryonecase),
    path('querycase/',views.querycase),
    path('editcase/',views.editcase),

    path('transform/',views.transform),
    path('third_party_call/',views.third_party_call),
    path('plan/',views.plan),
    path('mailcontrl/',views.mailcontrol),
    path('runplan',views.runtask),
    path('addplan/',views.addplan),
    path('delplan/',views.delplan),
    path('queryoneplan/',views.queryoneplan),
    path('queryplan/',views.queryplan),
    path('editplan/',views.editplan),
    path('queryplantaskid/',views.queryplantaskid),

    path('resultdetail/',views.resultdetail),
    path('delresultdetail/',views.delresultdetail),
    path('queryresultdetail/',views.queryresultdetail),

    path('function/',views.func),
    path('queryonefunc/',views.queryonefunc),
    path('queryfunc/',views.queryfunc),
    path('addfunction/',views.addfunc),
    path('delfunc/',views.delfunc),
    path('editfunction/',views.editfunc),
    path('updatefunc/',views.updatefunc),
    path('queryfunclist/',views.queryfunclist),

    path("queryafteradd/",views.queryafteradd),
    path("queryafterdel/",views.queryafterdel),
    
    path("testgenorder/",views.testgenorder),
    path("changepos/",views.changepos),
    path("aftergroup/",views.aftergroup),

    path('dbcon/',views.dbcon),
    path('testdbcon/',views.testdbcon),
    path('querydb/',views.querydb),
    path('queryonedb/',views.queryonedb),
    path('adddbcon/',views.addcon),
    path('delcon/',views.delcon),
    path('editdbcon/',views.editcon),
    path('querydblist/',views.querydblist),
    path('querydblistdefault/',views.querydblistdefault),

    path('mailconfig/',views.mailconfig),
    path('querymailconfig/',views.querymailconfig),
    path('editmailconfig/',views.editmailconfig),
    path('queryonemailconfig/',views.queryonemailconfig),

    path('querytaskdetail/',views.querytaskdetail),

    #
    path('querybusinessdata/',views.querybusinessdata),
    path('queryonebusiness/',views.queryonebusiness),
    path('queryonebusinessdata/',views.queryonebusinessdata),
    path('querybusinessdatalist/',views.querybusinessdatalist),

    #
    path('tag/',views.tag),
    path('querytaglist/',views.querytaglist),
    path('addtag/',views.addtag),
    path('deltag/',views.deltag),
    path('querytag/',views.querytag),

    #
    path('template/', views.template),
    # path('querytemplate/',),

    
    path('queryoneproduct/',views.queryoneproduct),
    path('tree/',views.treetest),
    path('querytreelist/',views.querytreelist),
    path('treecontrol/',views.treecontrol),

    #test
    path('addsteprelation/',views.addsteprelation),
    path('getfulltree/',views.getfulltree),
    path('update/',views.update),



]
