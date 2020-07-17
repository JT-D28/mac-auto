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

    path('help/', views.help),
    path('index/', views.index),

    path('datamove/', views.datamove),
    path('checkfilename/', views.checkfilename),
    path('uploadfile/', views.uploadfile),
    # path('delfile/', views.delfiles),
    path('upload/', views.upload),
    path('querymovedata/', views.querymovedata),

    path('import/', views.dataimport),
    path('export/', views.dataexport),
    path('movein/', views.datamovnin),

    path('var/', views.var),
    path('queryvar/', views.queryvar),
    path('queryonevar/', views.queryonevar),
    path('addvariable/', views.addvar),
    path('delvar/', views.delvar),
    path('editvariable/', views.editvar),
    path('editmultivar/', views.editmultivar),
    path('copyvar/', views.copyVar),

    path('queryonestep/', views.queryonestep),

    path('queryonecase/', views.queryonecase),

    path('transform/', views.transform),
    path('third_party_call/', views.third_party_call),
    path('plan/', views.plan),
    path('mailcontrl/', views.mailcontrol),
    path('runplan', views.runtask),
    path('queryoneplan/', views.queryoneplan),

    path('queryplantaskid/', views.queryplantaskid),

    path('queryplaninfo/', views.queryplaninfo),

    path('resultdetail/', views.resultdetail),
    path('delresultdetail/', views.delresultdetail),
    path('queryresultdetail/', views.queryresultdetail),

    path('function/', views.func),
    path('queryonefunc/', views.queryonefunc),
    path('queryfunc/', views.queryfunc),
    path('addfunction/', views.addfunc),
    path('delfunc/', views.delfunc),
    path('editfunction/', views.editfunc),
    path('updatefunc/', views.updatefunc),
    path('queryfunclist/', views.queryfunclist),

    path('dbcon/', views.dbcon),
    path('queryDbScheme/', views.queryDbScheme),
    path('testdbcon/', views.testdbcon),
    path('querydb/', views.querydb),
    path('queryonedb/', views.queryonedb),
    path('adddbcon/', views.addcon),
    path('delcon/', views.delcon),
    path('editdbcon/', views.editcon),
    path('editmultidbcon/', views.editmultidbcon),
    path('querydblist/', views.querydblist),
    path('querydblistdefault/', views.querydblistdefault),
    path('copyDbCon/', views.copyDbCon),
    path('queryDbSchemebyVar/', views.queryDbSchemebyVar),
    path('varSqltest/', views.varSqltest),

    path('editmailconfig/', views.editmailconfig),
    path('queryonemailconfig/', views.queryonemailconfig),

    path('querytaskdetail/', views.querytaskdetail),
    #
    path('queryonebusiness/', views.queryonebusiness),
    path('querybusinessdatalist/', views.querybusinessdatalist),
    path('queryUser/', views.queryUser),
    path('queryrole/', views.queryrole),
    path('queryonerole/', views.queryonerole),
    path('addrole/', views.addrole),
    path('delrole/', views.delrole),
    path('updaterole/', views.updaterole),
    path('queryroleusers/', views.query_transfer_data),

    # #
    path('tag/', views.tag),
    path('querytaglist/', views.querytaglist),
    path('querytags/', views.querytags),
    path('addtag/', views.addtag),
    path('deltag/', views.deltag),
    path('querytag/', views.querytag),
    path('varBatchEdit/', views.varBatchEdit),
    # #
    path('template/', views.template),
    path('querytemplatecommon/', views.querytemplatecommon),
    path('addtemplate/', views.addtemplate),
    path('deltemplate/', views.deltemplate),
    path('edittemplate/', views.edittemplate),
    path('querytemplate/', views.querytemplate),
    path('querytemplatelist/', views.querytemplatelist),

    path('templatefield/', views.templatefield),
    path('querytemplatefield/', views.querytemplatefield),
    path('addtemplatefield/', views.addtemplatefield),
    path('deltemplatefield/', views.deltemplatefield),
    path('edittemplatefield/', views.edittemplatefield),
    path('queryfielddetail/', views.queryfielddetail),

    path('queryuserfile/', views.queryuserfile),
    path('queryspacemenu/', views.queryspacemenu),
    path('queryspacefiles/', views.queryspacefiles),
    path('getfiledetail/', views.getfiledetail),
    path('editpathname/', views.editpathname),
    path('delfile/', views.delfile),
    path('addmenu/',views.addmenu),
    path('downloadfile/', views.downloadfile),
    path('editfile/',views.editfile),

    path('authcontrol/', views.authcontrol),
    path('queryuicontrol/', views.queryuicontrol),
    path('queryoneuicontrol/', views.queryoneuicontrol),
    path('deluicontrol/', views.deluicontrol),
    path('adduicontrol/', views.adduicontrol),
    path('updateuicontrol/', views.updateuicontrol),
    path('queryalluicontrolusers/', views.queryalluicontrolusers),
    path('updateuicontrolstatus/', views.updateuicontrolstatus),
    # #
    path('queryoneproduct/', views.queryoneproduct),
    path('tree/', views.treetest),
    path('querytreelist/', views.querytreelist),
    path('treecontrol/', views.treecontrol),
    path('getfulltree/', views.getfulltree),

    # #
    path('changemode/', views.changemode),
    ##
    path('simpletest/', views.simpletest),
    path('querysimpletest/', views.querysimpletest),
    path('querysteptype/', views.querysteptype),
    path('regentest/', views.regentest),
    path('updatesimpletest/', views.updatesimpletest),
    path('opensimpletest/', views.opensimpletest),
    path('openstepmock/', views.openstepmock),

    ##
    path('getusernews/', views.getusernews),
    path('getusernewsflag/', views.getusernewsflagstatus),
    path('hasread/', views.hasread),

    path('grab/', views.record),
    path('stoprecord/', views.stoprecord),

    path('getParamfromFetchData/', views.getParamfromFetchData),
    path('recycle/', views.recycle),
    path('queryrecyclelist/', views.queryrecyclelist),
    path('recyclenode/', views.recyclenode)

]
