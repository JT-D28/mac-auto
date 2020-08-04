from .Homepage import homepage
from .Product import queryproduct,queryProductAndPlan,queryProductSet,editProductSet
from .Plan import queryallplan, queryplan,queryPlanState,planforceStop,queryplanlist
from .charts import reportchart, badresult, jacocoreport,initbugcount
from .Jenkins import jenkinsJobRun,runforJacoco
from .logs import downloadlog,process
from .Report import sendreport,downloadReport
from .Taskid import querytaskid,query_third_call,gettaskidplan
from .others import globalsetting,restart
from .statisticalAnalysis import statisticalAnalysis,get_task_data,getnodes,geterrorinfo
from .runstatus import runstatus,runnodes,stauteofbusiness,getlog
from .planReport import *