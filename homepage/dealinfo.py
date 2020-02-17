import os
import re

from django.db import connection


def doDebugInfo(request):
    type = request.POST.get("type")
    id = request.POST.get("id")
    taskid = request.POST.get("taskid")

    if type == 'info':
        sql = '''
        SELECT description as planname,max(manager_resultdetail.createtime) as time,taskid FROM manager_resultdetail 
        LEFT JOIN manager_plan on manager_plan.id=manager_resultdetail.plan_id where plan_id=%s
        '''
        with connection.cursor() as cursor:
            cursor.execute(sql, [id])
            desc = cursor.description
            row = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
        return row, 'info', ''
    if type == 'plan':
        sql2 = '''
        SELECT description as title,case_id as id FROM manager_resultdetail r LEFT JOIN manager_case c on r.case_id=c.id 
        where plan_id=%s and taskid=%s and result in ('fail','error')
        '''
        with connection.cursor() as cursor:
            cursor.execute(sql2, [id, taskid])
            desc = cursor.description
            row = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
        case_row = []
        for i in list(row):
            if i not in case_row:
                case_row.append(i)
        return case_row, 'case', taskid
    if type == 'case':
        sql2 = '''
        SELECT description as title,step_id as id FROM manager_resultdetail r LEFT JOIN manager_step s 
        on r.step_id=s.id where case_id=%s and taskid=%s  and result in ('fail','error')
        '''
        with connection.cursor() as cursor:
            cursor.execute(sql2, [id, taskid])
            desc = cursor.description
            row = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
        step_row = []
        for i in list(row):
            if i not in step_row:
                step_row.append(i)
        return step_row, 'step', taskid
    if type == 'step':
        sql2 = '''
        SELECT businessname as title,businessdata_id as id FROM manager_resultdetail r 
        LEFT JOIN manager_businessdata b on r.businessdata_id=b.id where step_id=%s and taskid=%s and result in ('fail','error');
        '''
        with connection.cursor() as cursor:
            cursor.execute(sql2, [id, taskid])
            desc = cursor.description
            row = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
        businessdata_row = []
        for i in list(row):
            if i not in businessdata_row:
                businessdata_row.append(i)
        return businessdata_row, 'bussiness', taskid
    if type == 'bussiness':
        sql2 = '''
        select c.description as casename,s.description as stepname,b.businessname as businessname, 
        s.step_type,s.headers,s.body,s.url,s.method,s.content_type,b.itf_check,b.db_check,b.params,b.preposition,
        b.postposition,r.error from manager_case c, manager_resultdetail r,manager_step s,manager_businessdata b 
        where r.businessdata_id=%s and r.taskid=%s and  r.step_id=s.id and r.businessdata_id=b.id and r.case_id=c.id
        '''
        with connection.cursor() as cursor:
            cursor.execute(sql2, [id, taskid])
            desc = cursor.description
            businessdata_row = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
        logname = "./logs/" + taskid + ".log"
        if os.path.exists(logname):
            with open(logname, 'r', encoding='utf-8') as f:
                tmep1 = ''
                while 1:
                    log_text = f.readline()
                    if '结束计划' in log_text:
                        break
                    else:
                        if '---------------' in log_text:
                            continue
                        else:
                            tmep = log_text.replace("<span style='color:#FF3399'>", '').replace("</xmp>", '').replace(
                                "<xmp style='color:#009999;'>", '').replace(
                                "<span class='layui-bg-green'>", '').replace("<span class='layui-bg-red'>", '').replace(
                                "<span class='layui-bg-orange'>", '').replace("</span>", '').replace(
                                "<span style='color:#009999;'>", '').replace('\n', '').replace(
                                "'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36', ",
                                '')
                            tmep1 = tmep1 + tmep
                temp2 = re.sub(
                    r'[1-9]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])\s+(20|21|22|23|[0-1]\d):[0-5]\d:[0-5]\d',
                    '', tmep1)
                tmep3 = temp2.split('开始执行用例')
                for i in range(len(tmep3)):
                    if businessdata_row[0]['casename'] and businessdata_row[0]['stepname'] in tmep3[i]:
                        print(businessdata_row[0]['businessname'])
                        tmep4 = tmep3[i].split(businessdata_row[0]['businessname'])
                        itfcheck = re.search(r"接口校验配置.*?(?=<br>)", tmep4[1]).group().rstrip()
                        dbcheck = re.search(r"数据校验配置.*?(?=<br>)", tmep4[1]).group().rstrip()
                        url = re.search(r"url=>.*?(?=<br>)", tmep4[1]).group().rstrip()
                        method = re.search(r"method.*?(?=<br>)", tmep4[1]).group().rstrip()
                        headers = re.search(r"headers.*?(?=<br>)", tmep4[1]).group().rstrip()
                        params = re.search(r"params.*?(?=<br>)", tmep4[1]).group().rstrip()
                        请求响应 = re.search(r"请求响应.*?(?=<br>)", tmep4[1]).group().rstrip()
                        判断表达式 = re.search(r"判断表达式.*?(?=<br>)", tmep4[1]).group().rstrip()
                        执行结果 = re.search(r"执行结果.*?(?=<br>)", tmep4[1]).group().rstrip()
        if businessdata_row[0]['step_type'] == 'interface':
            res = [
                {"id": "前置操作", "expect": businessdata_row[0]['preposition'], "real": itfcheck},
                {"id": "headers", "expect": businessdata_row[0]['headers'], "real": headers},
                {"id": "content-type", "expect": businessdata_row[0]['content_type'], "real": headers},
                {"id": "url", "expect": businessdata_row[0]['url'], "real": url},
                {"id": "参数", "expect": businessdata_row[0]['params'], "real": params},
                {"id": "后置操作", "expect": businessdata_row[0]['postposition'], "real": params},
                {"id": "接口校验", "expect": businessdata_row[0]['itf_check'], "real": itfcheck},
                {"id": "db校验", "expect": businessdata_row[0]['db_check'], "real": dbcheck},
            ]
        elif businessdata_row[0]['step_type'] == 'function':
            res = [
                {"id": "前置操作", "expect": businessdata_row[0]['preposition'], "real": businessdata_row[0]['db_check']},
                {"id": "调用函数", "expect": businessdata_row[0]['body'], "real": businessdata_row[0]['db_check']},
                {"id": "参数", "expect": businessdata_row[0]['params'], "real": businessdata_row[0]['db_check']},
                {"id": "后置操作", "expect": businessdata_row[0]['postposition'], "real": businessdata_row[0]['db_check']},
            ]

        return res, 'businessdata', taskid
