import json
import os
import re

from django.db import connection

from manager.context import Me2Log as logger
from ME2.settings import BASE_DIR
from manager.models import Order, Step, ResultDetail, Case, BusinessData


async def dealruninfo(planid, taskid, info=None, startnodeid=''):
    casesdata = []
    kind, nodeid = startnodeid.split("_")
    if kind == 'plan':
        orders = Order.objects.filter(kind='plan_case', main_id=planid).extra(
            select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
        caselist = [order.follow_id for order in orders]
    else:
        caselist = [get_node_case(startnodeid)]


    success = ResultDetail.objects.filter(result='success', taskid=taskid).count()
    total = ResultDetail.objects.filter(taskid=taskid).exclude(result='omit').count()
    info['successnum'] = success
    info['total'] = total
    info['rate'] = round(success * 100 / total, 2)

    # with connection.cursor() as cursor:
    #     cursor.execute('''SELECT CONCAT(success) AS success,CONCAT(total) AS total,
    # 	ROUND(CONCAT(success*100/total),1) AS rate FROM (SELECT sum(CASE WHEN result="success"
    # 	THEN 1 ELSE 0 END) AS success,sum(CASE WHEN result !="OMIT" THEN 1 ELSE 0 END) AS total
    # 	FROM manager_resultdetail WHERE taskid=%s) AS x''', [taskid])
    #     info['successnum'],info['total'],info['rate'] = cursor.fetchone()
    data = {'root': [], 'info': info}

    for caseid in caselist:
        case = Case.objects.get(id=caseid)
        if case.count not in [0, '0', None]:
            num, successnum = get_business_num(caseid, taskid=taskid)
            rate = round(successnum * 100 / num, 2) if num != 0 else 0
            data['root'].append({'id': case.id, 'name': case.description, 'hasChildren': 'true',
                                 'case_success_rate': rate,
                                 'success': successnum,
                                 'total': num, 'type': 'case', 'icon': 'fa icon-fa-folder'})
            getcasemap(caseid, data, taskid)
        else:
            data['root'].append({'id': case.id, 'name': case.description + '(不执行)',
                                 'type': 'case', 'icon': 'fa icon-fa-folder', 'state': 'omit'})
    dealogname = BASE_DIR + "/logs/taskinfo/" + taskid + ".log"
    with open(dealogname, 'a', encoding='UTF-8') as f:
        f.write(json.dumps(data))


def getcasemap(caseid, data, taskid):
    maps = Order.objects.values('main_id', 'kind', 'follow_id').filter(main_id=caseid, kind__contains='case_').extra(
        select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
    for map in maps:
        temp = data.get('case_' + str(map['main_id']), [])
        if temp == []:
            data['case_' + str(map['main_id'])] = []
        if map['kind'] == 'case_step':
            step = Step.objects.get(id=map['follow_id'])
            if step.count not in [0, '0', None]:
                bnum = ResultDetail.objects.filter(taskid=taskid, step_id=step.id).exclude(result='omit').count()
                # bnum = Order.objects.filter(main_id=map['follow_id'], kind__contains='step_business').count()
                getsuccess = '''SELECT count(DISTINCT businessdata_id) FROM `manager_resultdetail` where taskid=%s and result='success'  and step_id=%s '''
                with connection.cursor() as cursor:
                    cursor.execute(getsuccess, [taskid, map['follow_id']])
                    successnum = cursor.fetchone()[0]
                case_success_rate = round(successnum * 100 / bnum, 2) if bnum != 0 else 0
                data['case_' + str(map['main_id'])].append(
                    {'id': map['follow_id'], 'type': 'step', 'name': Step.objects.get(id=map['follow_id']).description,
                     'total': bnum,
                     'success': successnum, 'case_success_rate': case_success_rate, 'hasChildren': True,
                     'icon': 'fa icon-fa-file-o'})

                get_business_info(step.id, data, taskid)
            else:
                data['case_' + str(map['main_id'])].append(
                    {'id': map['follow_id'], 'type': 'step',
                     'name': Step.objects.get(id=map['follow_id']).description + "(不执行)",
                     'icon': 'fa icon-fa-file-o', 'state': 'omit'})

        elif map['kind'] == 'case_case':
            if Case.objects.get(id=map['main_id']).count not in [0, '0', None]:
                total, successnum = get_business_num(map['follow_id'], taskid)
                rate = round(successnum * 100 / total, 2) if total != 0 else 0
                data['case_' + str(map['main_id'])].append(
                    {'id': map['follow_id'], 'type': 'case', 'name': Case.objects.get(id=map['follow_id']).description,
                     'total': total,
                     'success': successnum, 'case_success_rate': rate, 'hasChildren': True,
                     'icon': 'fa icon-fa-folder'})
                getcasemap(map['follow_id'], data, taskid)
            else:
                data['case_' + str(map['main_id'])].append(
                    {'id': map['follow_id'], 'type': 'case',
                     'name': Case.objects.get(id=map['follow_id']).description + "(不执行)",
                     'icon': 'fa icon-fa-folder', 'state': 'omit'})


def get_business_info(stepid, data, taskid):
    orders = Order.objects.filter(main_id=stepid, kind__contains='step_business').extra(
        select={"value": "cast( substring_index(value,'.',-1) AS DECIMAL(10,0))"}).order_by("value")
    data['step_' + str(stepid)] = []
    for order in orders:
        businessdata = BusinessData.objects.get(id=order.follow_id)
        if businessdata.count not in [0, '0', None]:
            try:
                state = ResultDetail.objects.filter(taskid=taskid, businessdata_id=order.follow_id)[0].result
                data['step_' + str(stepid)].append(
                    {'id': businessdata.id, 'name': businessdata.businessname, 'hasChildren': False, 'type': 'business',
                     'icon': 'fa icon-fa-leaf', 'state': state})
            except:
                # print(traceback.format_exc())
                pass
        else:
            data['step_' + str(stepid)].append(
                {'id': businessdata.id, 'name': businessdata.businessname + '(不执行)', 'icon': 'fa icon-fa-leaf',
                 'state': 'zerocount'})


def get_business_num(id, taskid='', num=0, successnum=0, countnum=0):
    orders = Order.objects.filter(main_id=id, kind__contains='case_')
    for o in orders:
        kind = o.kind
        if kind == 'case_step':
            os = Order.objects.filter(main_id=o.follow_id, kind__contains='step_business')
            getsuccess = '''SELECT count(DISTINCT businessdata_id) FROM `manager_resultdetail` where taskid=%s and result='success'  and businessdata_id=%s '''
            getcount = '''SELECT count(DISTINCT businessdata_id) FROM `manager_resultdetail` where taskid=%s  and businessdata_id=%s and result!='omit' '''
            for o in os:
                with connection.cursor() as cursor:
                    cursor.execute(getsuccess, [taskid, o.follow_id])
                    successnum += cursor.fetchone()[0]
                    cursor.execute(getcount, [taskid, o.follow_id])
                    num += cursor.fetchone()[0]
        elif kind == 'case_case':
            num, successnum = get_business_num(o.follow_id, taskid, num, successnum, countnum)
    return num, successnum


async def dealDeBuginfo(taskid):
    logname = BASE_DIR + "/logs/" + taskid + ".log"
    dealogname = BASE_DIR + "/logs/deal/" + taskid + ".log"
    if os.path.exists(logname):
        logger.info('存在{}日志文件'.format(taskid))
        ma = []
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
                        tmep = log_text.replace('\n', '').replace(
                            "'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36', ",
                            '')
                        tmep1 = tmep1 + tmep
            temp2 = re.sub(
                r'\[(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])\s+(20|21|22|23|[0-1]\d):[0-5]\d:[0-5]\d\]', '',
                tmep1)
            # case_matchs = re.findall(r"开始执行用例.*?结束用例.*?结果.*?<br>", temp2)
            logger.info("开始处理日志------")
            bmatchs = re.findall(r"开始执行步骤.*?步骤执行.*?结果.*?<br>", temp2)
            with open(dealogname, 'a', encoding='UTF-8') as f:
                for b in bmatchs:
                    f.write(b.replace("        ", '\n') + '\n========\n')
            # for case in case_matchs:
            # 	step_matchs = re.findall(r"开始执行步骤.*?步骤执行.*?结果.*?<br>", case)
            # 	for step in step_matchs:
            # 		print('step:',step)
            # 		with open(dealogname, 'a', encoding='UTF-8') as f:
            # 			f.write(step.replace("        ", '\n') + '\n========\n')
            logger.info('处理日志完成------')


def get_node_case(nodeid):
    kind, id = nodeid.split("_")
    if kind == 'case':
        return id
    elif kind == 'step':
        return Order.objects.get(kind='case_step', follow_id=id).main_id
    elif kind == 'business':
        stepid = Order.objects.get(kind='step_business', follow_id=id).main_id
        return get_node_case('step_%s' % stepid)
