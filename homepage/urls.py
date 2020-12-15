from django.urls import path
import homepage.views as views

urlpatterns = [
	path('queryPlanState/', views.queryPlanState),
	path('runnodes/', views.runnodes),
	path('getBusinessLog', views.getBusinessLog),
	path('getnodes/', views.getnodes),
	path('gettaskdata/', views.get_task_data),
	path('gettaskidplan/', views.gettaskidplan),
	path('queryproduct/', views.queryproduct),
	path('queryplan/', views.queryplan),
	path('queryProductSet/', views.queryProductSet),
	path('planforceStop/', views.planforceStop),
	path('query_third_call/', views.query_third_call),
	path('editProductSet/', views.editProductSet),
	path('sendreport/', views.sendreport),
	path('querytaskid/', views.querytaskid),
	path('reportchart/', views.reportchart),
	path('jacocoreport/', views.jacocoreport),
	path('runforJacoco/', views.runforJacoco),
	path('queryProductAndPlan/', views.queryProductAndPlan),
	
	path('', views.homepage),
	path('queryplanlist/', views.queryplanlist),
	path('queryallplan/', views.queryallplan),
	path('globalsetting/', views.globalsetting),
	path('restart/', views.restart),
	path('initbugcount/', views.initbugcount),
	path('downloadlog/', views.downloadlog),
	path('downloadReport/', views.downloadReport),
	path('jenkinsJobRun/', views.jenkinsJobRun),
	path('runstatus/', views.runstatus),
	path('stauteofbusiness/', views.stauteofbusiness),

	path('HasJacoco/', views.HasJacoco),
	path('HasGit/', views.HasGit),
	path('queryCoveryInfo/', views.queryCoveryInfo),
	path('queryGitCommit/', views.queryGitCommit),
	path('queryJenkinsUpdatetimes/', views.queryJenkinsUpdatetimes),
	
	path('queryApiTaskRangeDate',views.queryApiTaskRangeDate),
	path('queryApiTestReportByTaskId',views.queryApiTestReportByTaskId),
	path('deleteTask',views.deleteTask),
	path('queryFailBusiness',views.queryFailBusiness),
	path('getPlanExportData',views.getPlanExportData)
]
