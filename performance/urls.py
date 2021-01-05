from django.urls import path
import performance.views as views

urlpatterns = [
	path('getNodes', views.getNodes),
	path('getNodeInfo', views.getNodeInfo),
	path('nodeAdd', views.NodeAdd),
	path('nodeEdit', views.NodeEdit),
	path('nodeDel', views.NodeDel),
	path('nodeRun', views.NodeRun),
	path('runPerformance', views.runPerformance),
	path('queryNodeKind', views.queryNodeKind),
	path('queryPlan', views.queryPlan),
	path('queryTasks', views.queryTasks),
	path('nodeCopy', views.nodeCopy),
	path('nodeMove', views.nodeMove),
	path('queryTestResources',views.queryTestResources)
]
