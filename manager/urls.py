from django.urls import path
from . import views

urlpatterns = [
    path('querytreelist/', views.querytreelist),
    path('queryoneproduct/', views.queryoneproduct),
    path('queryoneplan/', views.queryoneplan),
    path('queryonecase/', views.queryonecase),
    path('treecontrol/', views.treecontrol),
    path('queryDbScheme/', views.queryDbScheme),
    path('querydblist/', views.querydblist),
    path('getStepKind/', views.getStepKind),
    path('queryonestep/', views.queryonestep),
    path('queryonebusiness/', views.queryonebusiness),
    path('editStepByExtract/', views.editStepByExtract),
    path('queryfunclist/', views.queryfunclist),
    path('querydb/', views.querydb),
    path('adddbcon/', views.addcon),
    path('delcon/', views.delcon),
    path('editdbcon/', views.editcon),
    path('copyDbCon/', views.copyDbCon),
    path('editfile/', views.editfile),
    path('addmenu/', views.addmenu),
    path('querywinrm/', views.querywinrm),
    path('queryspacemenu/', views.queryspacemenu),
    path('queryspacefiles/', views.queryspacefiles),
    path('getfiledetail/', views.getfiledetail),
    path('editpathname/', views.editpathname),
    path('delfile/', views.delfile),
    path('checkfilename/', views.checkfilename),
    path('queryonefunc/', views.queryonefunc),
    path('queryfunc/', views.queryfunc),
    path('addfunction/', views.addfunc),
    path('delfunc/', views.delfunc),
    path('editfunction/', views.editfunc),
    path('updatefunc/', views.updatefunc),
    path('runplan', views.runtask),
    path('editmailconfig/', views.editmailconfig),
    path('queryonemailconfig/', views.queryonemailconfig),
    path('querytaskdetail/', views.querytaskdetail),
    path('addtemplate/', views.addtemplate),
    path('deltemplate/', views.deltemplate),
    path('edittemplate/', views.edittemplate),
    path('querytemplate/', views.querytemplate),
    path('querytemplatefield/', views.querytemplatefield),
    path('addtemplatefield/', views.addtemplatefield),
    path('deltemplatefield/', views.deltemplatefield),
    path('edittemplatefield/', views.edittemplatefield),
    path('queryfielddetail/', views.queryfielddetail),
    path('queryUser/', views.queryUser),
    path('queryvar/', views.queryvar),
    path('querytaglist/', views.querytaglist),
    path('delvar/', views.delvar),
    path('querytags/', views.querytags),
    path('queryonevar/', views.queryonevar),
    path('addvariable/', views.addvar),
    path('editvariable/', views.editvar),
    path('copyvar/', views.copyVar),
    path('testdbcon/', views.testdbcon),
    path('upload/', views.upload),
    path('third_party_call/', views.third_party_call),






    
    path('help/', views.help),
    path('index/', views.index),

    path('datamove/', views.datamove),
    path('uploadfile/', views.uploadfile),


    path('var/', views.var),

    path('editmultivar/', views.editmultivar),



    path('transform/', views.transform),
    path('plan/', views.plan),





    path('function/', views.func),


    path('dbcon/', views.dbcon),
    path('queryonedb/', views.queryonedb),

    path('editmultidbcon/', views.editmultidbcon),
    path('querydblistdefault/', views.querydblistdefault),
    path('queryDbSchemebyVar/', views.queryDbSchemebyVar),
    path('varSqltest/', views.varSqltest),


    #
    path('querybusinessdatalist/', views.querybusinessdatalist),
    path('queryrole/', views.queryrole),
    path('queryonerole/', views.queryonerole),
    path('addrole/', views.addrole),
    path('delrole/', views.delrole),
    path('updaterole/', views.updaterole),
    path('queryroleusers/', views.query_transfer_data),

    # #
    path('tag/', views.tag),
    path('addtag/', views.addtag),
    path('deltag/', views.deltag),
    path('querytag/', views.querytag),
    path('varBatchEdit/', views.varBatchEdit),
    # #
    path('template/', views.template),
    path('querytemplatecommon/', views.querytemplatecommon),

    path('querytemplatelist/', views.querytemplatelist),

    path('templatefield/', views.templatefield),


    path('queryuserfile/', views.queryuserfile),

    path('downloadfile/', views.downloadfile),

    path('authcontrol/', views.authcontrol),
    path('queryuicontrol/', views.queryuicontrol),
    path('queryoneuicontrol/', views.queryoneuicontrol),
    path('deluicontrol/', views.deluicontrol),
    path('adduicontrol/', views.adduicontrol),
    path('updateuicontrol/', views.updateuicontrol),
    path('queryalluicontrolusers/', views.queryalluicontrolusers),
    path('updateuicontrolstatus/', views.updateuicontrolstatus),
    # #
    path('tree/', views.treetest),

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
    path('recyclenode/', views.recyclenode),

    path('link/', views.link),
    path('test/',views.test)

]
