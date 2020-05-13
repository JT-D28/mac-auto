import datetime

from django.http import JsonResponse

from login.models import User
from manager.context import Me2Log as logger
from manager.core import simplejson, EncryptUtils, getbuiltin, Fu
from manager.models import *


class DataMove:
    '''
    计划导入导出 兼容ME2老版本转成新版本
    '''

    def _init_tmp(self):
        self._data = {

            ##实体数据
            'entity': {
                'schemename': '',
                'plan': {},
                'cases': [],
                'steps': [],
                'businessdatas': [],
                'dbcons': [],
                'vars': [],
                'funcs': [],
                'authors': []

            },

            ##依赖关系
            'relation': {
                'plan_case': {

                },
                'step_business': {

                },
                'case_step': {

                },
                'case_case': {

                }

            }}

    def __init__(self):
        self._init_tmp()

    def export_plans(self, planids):
        pass

    def export_plan(self, planid, export_flag, version=2):

        # logger.info(version,type(version),version==2)
        return self._export_plan_new(planid, export_flag) if version == 2 else self._export_plan_old(planid,
                                                                                                     export_flag)

    def _add_author(self, authorname):
        namelist = [author.get('name') for author in self._data['entity']['authors']]
        if authorname not in namelist:
            author = User.objects.get(name=authorname)
            self._data['entity']['authors'].append({

                'name': author.name,
                'password': author.password,
                'email': author.email,
                'sex': author.sex,
            })

    def _add_dbcon(self, gain, dbid=None, scheme=None):
        namelist = [x.get('description') for x in self._data['entity']['dbcons']]
        try:
            if dbid is not None:
                dbcon = DBCon.objects.get(id=dbid)
                logger.info()
            else:
                sep = gain.split('@')
                if sep[-1] in namelist:
                    return
                dbcon = DBCon.objects.get(scheme=scheme, description=sep[-1])
        except:
            logger.info('库中没找到连接 略过')

        self._data['entity']['dbcons'].append({
            'id': dbcon.id,
            'dbname': dbcon.dbname,
            'description': dbcon.description,
            'host': dbcon.host,
            'port': dbcon.port,
            'username': dbcon.username,
            'password': dbcon.password,
            'authorname': dbcon.author.name,
            'kind': dbcon.kind,
            'scheme': dbcon.scheme
        })

    def _add_var(self, key, planid):
        namelist = [x.get('key') for x in self._data['entity']['vars']]
        if key not in namelist:
            try:
                vars = Variable.objects.filter(key=key)
                for var in vars:
                    planids = Tag.objects.get(var=var).planids
                    logger.info("okokokokokok", var, planids)
                    if Plan.objects.get(id=planid).description in planids and planid in planids:
                        usevar = var
                    else:
                        usevar = Tag.objects.get(var=var, isglobal=1).var
                    self._data['entity']['vars'].append({
                        'id': usevar.id,
                        'description': usevar.description,
                        'key': usevar.key,
                        'value': usevar.value,
                        'gain': usevar.gain,
                        'is_cache': usevar.is_cache,
                        'authorname': usevar.author.name,
                        'customize': Tag.objects.get(var=usevar).customize if Tag.objects.get(
                            var=usevar).customize is not None else '',
                    })

                    ##gain中含变量 这里只处理两层嵌套 多的会有问题
                    gainvars = re.findall("{{(.*?)}}", usevar.gain)
                    for va in gainvars:
                        vs = Variable.objects.filter(key=va)
                        for v in vs:
                            planids = Tag.objects.get(var=v).planids
                            if Plan.objects.get(id=planid).description in planids and planid in planids:
                                self._data['entity']['vars'].append({
                                    'id': v.id,
                                    'description': v.description,
                                    'key': v.key,
                                    'value': v.value,
                                    'gain': v.gain,
                                    'is_cache': v.is_cache,
                                    'authorname': v.author.name
                                })
            except:
                logger.info('库中没找到变量 略过=>', key)

    def _get_bussiness_id(self):
        return '%s_%s' % ('vid', EncryptUtils.md5_encrypt(str(datetime.datetime.now())))

    def _add_case_relation_data(self, case):
        from manager.cm import getchild

        ##1.用例挂步骤场景
        steplist = getchild('case_step', case.id)
        for step in steplist:
            exist_step_ids = [step.get('id') for step in self._data['entity']['steps']]
            if step.id in exist_step_ids:
                continue

            stepd = {}
            stepd['id'] = step.id
            stepd['step_type'] = step.step_type
            stepd['method'] = step.method
            stepd['description'] = step.description
            stepd['headers'] = step.headers if step.headers is not None else ''
            stepd['body'] = step.body if step.body is not None else ''
            stepd['url'] = step.url if step.url is not None else ''
            stepd['content_type'] = step.content_type
            stepd['tmp'] = step.temp
            stepd['authorname'] = step.author.name
            self._add_author(step.author.name)
            stepd['db_id'] = step.db_id
            if step.db_id != '':
                try:
                    dbid = DBCon.objects.get(scheme=self._data['entity']['schemename'], description=step.db_id).id
                    logger.info('234', dbid)
                    self._add_dbcon('', dbid=dbid)
                except:
                    pass
            self._data['entity']['steps'].append(stepd)

            c = self._data['relation']['case_step'].get(str(case.id), [])
            ordervalue = Order.objects.get(kind='case_step', main_id=case.id, follow_id=step.id).value
            c.append((str(step.id), ordervalue))
            self._data['relation']['case_step'][str(case.id)] = list(set(c))

            # logger.info('%s=>%s'%(step.description,step.step_type))

            businesslist = getchild('step_business', step.id)

            for business in businesslist:
                ###########
                businessd = {}
                businessd['id'] = business.id
                businessd['businessname'] = business.businessname

                itf_check = business.itf_check if business.itf_check is not None else ''
                db_check = business.db_check if business.db_check is not None else ''
                params = business.params if business.params is not None else ''
                logger.info("123iijij", business, params)
                businessd['itf_check'] = itf_check
                businessd['db_check'] = db_check
                businessd['params'] = params
                varnames = re.findall('{{(.*?)}}', str(itf_check) + str(db_check) + str(params))

                self._varkeys = self._varkeys + varnames

                logger.info('bname=>', businessd['businessname'])
                busnamelist = [business.get('businessname') for business in self._data['entity']['businessdatas']]
                ##
                if businessd['businessname'] not in busnamelist:
                    self._data['entity']['businessdatas'].append(businessd)
                    b = self._data['relation']['step_business'].get(str(step.id), [])
                    ordervalue = Order.objects.get(kind='step_business', main_id=step.id, follow_id=business.id).value
                    b.append((str(business.id), ordervalue))
                    self._data['relation']['step_business'][str(step.id)] = list(set(b))
                    headers = step.headers if step.headers is not None else ''
                    url = step.url if step.url is not None else ''
                    varnames = re.findall('{{(.*?)}}', str(headers) + str(url))
                    self._varkeys = self._varkeys + varnames

                if step.step_type == 'function':
                    funcname = step.body.strip()
                    builtinmethods = [x.name for x in getbuiltin()]
                    builtin = (funcname in builtinmethods)

                    if builtin is False:
                        status, res = BusinessData.gettestdataparams(business.id)  ###????????????????
                        logger.info('%s=>%s' % (business.businessname, business.params))
                        if status is not 'success':
                            return JsonResponse(simplejson(code=3, msg=str(res)))

                        params = ','.join(res)
                        call_str = '%s(%s)' % (step.body.strip(), params)
                        flag = Fu.tzm_compute(call_str, '(.*?)\((.*?)\)')
                        logger.info('1call_str=>', call_str)
                        # logger.info('falg=>',flag)
                        funcs = list(Function.objects.filter(flag=flag))
                        if len(funcs) > 1:
                            return JsonResponse(simplejson(code=44, msg='找到多个匹配的自定义函数 请检查'))

                        stepd['related_id'] = funcs[0].id

                        # 导出使用的函数
                        func = Function.objects.get(id=funcs[0].id)
                        self._data['entity']['funcs'].append({
                            'id': func.id,
                            'kind': func.kind,
                            'name': func.name,
                            'description': func.description,
                            'flag': func.flag,
                            'body': func.body,
                            'authorname': func.author.name
                        })
                        self._add_author(func.author.name)

        ##2.用例嵌套场景
        caselist0 = getchild('case_case', case.id)
        for case0 in caselist0:
            cased = {}
            cased['id'] = case0.id
            cased['description'] = case0.description
            cased['authorname'] = case0.author.name
            cased['db_id'] = case0.db_id
            if case0.db_id != '':
                try:
                    dbid = DBCon.objects.get(scheme=self._data['schemename'], description=case0.db_id).id
                    self._add_dbcon('', dbid=dbid)
                except:
                    pass
            self._data['entity']['cases'].append(cased)
            d = self._data['relation']['case_case'].get(str(case.id), [])
            ordervalue = Order.objects.get(kind='case_case', main_id=case.id, follow_id=case0.id).value
            d.append((str(case0.id), ordervalue))
            self._data['relation']['case_case'][str(case.id)] = list(set(d))
            self._add_case_relation_data(case0)

    def _export_plan_new(self, planid, export_flag):
        from manager.cm import getchild
        self._data['version'] = 2.0
        self._varkeys = []
        try:
            planid = planid.split('_')[1]
            plan = Plan.objects.get(id=planid)
            schemename = plan.schemename
            dbdescription = plan.db_id
            self._data['entity']['schemename'] = schemename
            self._data['entity']['plan']['id'] = plan.id
            self._data['entity']['plan']['description'] = plan.description
            self._data['entity']['plan']['authorname'] = plan.author.name
            self._add_author(plan.author.name)
            self._data['entity']['plan']['runtype'] = plan.run_type
            # self._data['entity']['plan']['runvalue']=plan.run_value
            self._data['entity']['plan']['db_id'] = plan.db_id

            # caselist=list(plan.cases.all())
            caselist = getchild('plan_case', plan.id)
            if dbdescription != '':
                try:
                    dbid = DBCon.objects.get(scheme=schemename, description=dbdescription).id
                    self._add_dbcon('', dbid=dbid)
                except:
                    pass
            for case in caselist:
                cased = {}
                cased['id'] = case.id
                cased['description'] = case.description
                cased['db_id'] = case.db_id
                cased['authorname'] = case.author.name
                self._add_author(case.author.name)
                self._data['entity']['cases'].append(cased)
                if case.db_id != '':
                    try:
                        dbid = DBCon.objects.get(scheme=schemename, description=case.db_id).id
                        self._add_dbcon('', dbid=dbid)
                    except:
                        pass
                a = self._data['relation']['plan_case'].get(str(planid), [])
                ordervalue = Order.objects.get(kind='plan_case', main_id=plan.id, follow_id=case.id).value
                a.append((str(case.id), ordervalue))
                self._data['relation']['plan_case'][str(planid)] = list(set(a))
                self._add_case_relation_data(case)

            logger.info('123', self._varkeys)
            # 统一导出变量
            for key in self._varkeys:
                self._add_var(key, planid)
                try:
                    var = Variable.objects.get(key=key)
                    self._add_author(var.author.name)
                    self._add_dbcon(var.gain, None, self._data['entity']['schemename'])
                except:
                    pass
            return ('success', self._data)
        except:
            return ('error', '导出转换过程发生异常[%s]' % traceback.format_exc())

    def _get_vid(self):
        return 'vid_%s' % (EncryptUtils.base64_encrypt(str(datetime.datetime.now())))

    def _export_plan_old(self, planid, export_flag):
        self._data['version'] = 1.0
        varkeys = []
        try:
            plan = Plan.objects.get(id=planid)
            self._data['entity']['plan']['id'] = plan.id
            self._data['entity']['plan']['description'] = plan.description
            self._data['entity']['plan']['authorname'] = plan.author.name
            self._add_author(plan.author.name)
            self._data['entity']['plan']['runtype'] = plan.run_type
            # self._data['entity']['plan']['runvalue']=plan.run_value
            self._data['entity']['plan']['db_id'] = ''

            caselist = list(plan.cases.all())
            for case in caselist:
                cased = {}
                cased['id'] = case.id
                cased['description'] = case.description
                cased['db_id'] = ''
                cased['authorname'] = case.author.name
                self._add_author(case.author.name)
                self._data['entity']['cases'].append(cased)

                a = self._data['relation']['plan_case'].get(str(planid), [])
                ordervalue = Order.objects.get(kind='case', main_id=plan.id, follow_id=case.id).value

                a.append((str(case.id), ordervalue))
                self._data['relation']['plan_case'][str(planid)] = list(set(a))

                steplist = list(case.steps.all())
                for step in steplist:
                    bid = self._get_vid()

                    businessd = {}
                    businessd['id'] = bid  ##????
                    businessd['businessname'] = '测试点1(pl%s)' % step.id
                    businessd['itf_check'] = step.itf_check
                    businessd['db_check'] = step.db_check
                    if step.step_type == 'interface':
                        businessd['params'] = step.body
                    else:
                        businessd['params'] = re.findall('\((.*?)\)', step.body)[0]

                    varnames = re.findall('{{(.*?)}}', step.itf_check + step.db_check + step.body)
                    varkeys = varkeys + varnames
                    busnamelist = [business.get('businessname') for business in self._data['entity']['businessdatas']]
                    if businessd['businessname'] not in busnamelist:
                        self._data['entity']['businessdatas'].append(businessd)

                        b = self._data['relation']['case_business'].get(str(case.id), [])
                        ordervalue = Order.objects.get(kind='step', main_id=case.id, follow_id=step.id).value
                        b.append((str(bid), ordervalue))  ###?????
                        self._data['relation']['case_business'][str(case.id)] = list(set(b))

                        exist_step_ids = [step.get('id') for step in self._data['entity']['steps']]
                        if step.id in exist_step_ids:
                            continue

                        stepd = {}
                        # step=step[1]
                        stepd['id'] = step.id
                        stepd['step_type'] = step.step_type
                        stepd['method'] = step.method
                        stepd['description'] = step.description
                        stepd['headers'] = step.headers
                        # stepd['body']=step.body
                        stepd['url'] = step.url
                        stepd['content_type'] = step.content_type
                        stepd['tmp'] = step.temp
                        stepd['authorname'] = step.author.name
                        self._add_author(step.author.name)
                        stepd['db_id'] = ''
                        self._data['entity']['steps'].append(stepd)

                        varnames = re.findall('{{(.*?)}}', step.headers + step.url)
                        varkeys = varkeys + varnames
                        c = self._data['relation']['step_business'].get(str(step.id), [])
                        c.append(str(bid))  ####???????????
                        self._data['relation']['step_business'][str(step.id)] = list(set(c))

                        if step.step_type == 'function':
                            stepd['body'] = re.findall("(.*?)\(", step.body)[0]
                            funcname = re.findall("(.*?)\(", step.body.strip())[0]

                            builtinmethods = [x.name for x in getbuiltin()]
                            builtin = (funcname in builtinmethods)

                            if builtin is False:
                                call_str = step.body.strip()
                                flag = Fu.tzm_compute(call_str, '(.*?)\((.*?)\)')
                                funcs = list(Function.objects.filter(flag=flag))
                                if len(funcs) > 1:
                                    return JsonResponse(simplejson(code=44, msg='找到多个匹配的自定义函数 请检查'))

                                stepd['related_id'] = funcs[0].id
                                # 导出使用的函数
                                func = Function.objects.get(id=funcs[0].id)
                                self._data['entity']['funcs'].append({
                                    'id': func.id,
                                    'kind': func.kind,
                                    'name': func.name,
                                    'description': func.description,
                                    'flag': func.flag,
                                    'body': func.body,
                                    'authorname': func.author.name
                                })
                                self._add_author(func.author.name)

            # 统一导出变量
            for key in varkeys:
                self._add_var(key)
                try:
                    var = Variable.objects.get(key=key)
                    self._add_author(var.author.name)
                    self._add_dbcon(var.gain)
                except:
                    pass
            return ('success', self._data)
        except:
            return ('error', '导出转换过程发生异常[%s]' % traceback.format_exc())

    def _hanlde_repeat_name(self, filterstr, classstr, flag, ex=None):

        _M = {
            'Variable': '变量',
            'DBCon': '数据连接',
            'Step': '步骤'
        }
        key = filterstr.split('=')[0]
        oldvalue = filterstr.split('=')[1].strip()
        if classstr == 'Variable':
            tags = Tag.objects.filter(planids=ex)
            for tag in tags:
                if tag.var.key == oldvalue:
                    return 'fail', '变量%s已存在 略过导入' % oldvalue
            return ('success', oldvalue)
        elif classstr == 'DBCon':
            callstr = "len(list(DBCon.objects.filter(description='%s',scheme='%s')))" % (oldvalue, ex)
        else:
            callstr = "len(list(%s.objects.filter(%s='%s')))" % (classstr, key, oldvalue)
        length = eval(callstr)
        if length > 0:
            logger.info('9999999', classstr)
            if classstr in ('Variable', 'DBCon'):
                return 'fail', '%s[%s]已存在 略过导入请手动调整' % (_M.get(classstr, ''), oldvalue)

            elif classstr == 'BusinessData':
                # logger.info('yes=>',classstr)
                return ('success', oldvalue)
            else:
                # final='%s#%s'%(oldvalue,flag)
                final = oldvalue
                logger.info('%s重复处理=>%s' % (_M.get(classstr), final))
                return ('success', final)
        else:
            return ('success', oldvalue)

    def import_plan(self, product_id, content_byte_list, callername):
        _cache = {}
        _msg = []
        b = b''
        for byte in content_byte_list:
            b = b + byte
        bs = b.decode()
        bl = eval(bs)
        logger.info('【开始导入数据】 ')
        # 导入实体类
        scheme = bl['entity']['schemename']
        plan = bl['entity']['plan']
        cases = bl['entity']['cases']
        steps = bl['entity']['steps']
        businessdatas = bl['entity']['businessdatas']
        dbcons = bl['entity']['dbcons']
        vs = bl['entity']['vars']
        funcs = bl['entity']['funcs']
        authors = bl['entity']['authors']

        ##plan
        plano = Plan()
        _cache['plan_%s' % plan.get('id')] = plano
        plano.description = plan.get('description')
        plano.description = (plano.description + str(datetime.datetime.now()).split('.')[0]).replace(' ', '').replace(
            ':', '')

        plano.run_type = plan.get('runtype')
        plano.db_id = plan.get('db_id')
        plano.schemename = scheme
        try:
            author = User.objects.get(name=plan.get('authorname'))
            plano.author = author
            plano.save()

            ##
            order = Order()
            order.kind = 'product_plan'
            order.main_id = product_id
            order.follow_id = plano.id
            order.value = '1.1'
            try:
                author = User.objects.get(name=callername)
                order.author = author
                order.save()
            except:
                author = [author for author in authors if author.get('name') == callername][0]
                authoro = User()
                authoro.name = author.get('name')
                authoro.password = author.get('password')
                authoro.email = author.get('email')
                authoro.sex = author.get('sex')
                authoro.save()
                order.author = authoro
                order.save()


        except:
            author = [author for author in authors if author.get('name') == plan.get('authorname')][0]
            authoro = User()
            authoro.name = author.get('name')
            authoro.password = author.get('password')
            authoro.email = author.get('email')
            authoro.sex = author.get('sex')
            authoro.save()
            plano.author = authoro
            plano.save()

        flag = 'im%s' % plano.id
        # case
        for case in cases:
            caseo = Case()
            _cache['case_%s' % case.get('id')] = caseo
            logger.info('=缓存case=>', 'case_%s' % case.get('id'))
            status, caseo.description = self._hanlde_repeat_name("description=%s" % case.get('description'), 'Case',
                                                                 flag)
            caseo.db_id = case.get('db_id')

            try:
                author = User.objects.get(name=case.get('authorname'))
                caseo.author = author
                caseo.save()
            except:
                author = [author for author in authors if author.get('name') == plan.get('authorname')][0]
                authoro = User()
                authoro.name = author.get('name')
                authoro.password = author.get('password')
                authoro.email = author.get('email')
                authoro.sex = author.get('sex')
                authoro.save()
                caseo.author = authoro
                caseo.save()

        ##step
        for step in steps:
            stepo = Step()
            _cache['step_%s' % step.get('id')] = stepo
            stepo.step_type = step.get('step_type')
            status, stepo.description = self._hanlde_repeat_name("description=%s" % step.get('description'), 'Step',
                                                                 flag)
            stepo.headers = step.get('headers')
            stepo.body = step.get('body', '')
            stepo.url = step.get('url')
            stepo.method = step.get('method')
            stepo.content_type = step.get('content_type')
            stepo.temp = step.get('tmp')
            stepo.db_id = step.get('db_id')
            try:
                author = User.objects.get(name=step.get('authorname'))
                stepo.author = author
                stepo.save()
            except:
                author = [author for author in authors if author.get('name') == step.get('authorname')][0]
                authoro = User()
                authoro.name = author.get('name')
                authoro.password = author.get('password')
                authoro.email = author.get('email')
                authoro.sex = author.get('sex')
                authoro.save()
                stepo.author = authoro
                stepo.save()

        ##bussiness
        for businessdata in businessdatas:
            bd = BusinessData()
            _cache['business_%s' % businessdata.get('id')] = bd
            status, bd.businessname = self._hanlde_repeat_name("businessname=%s" % businessdata.get('businessname'),
                                                               'BusinessData', flag)
            bd.itf_check = businessdata.get('itf_check')
            bd.db_check = businessdata.get('db_check')
            bd.params = businessdata.get('params')
            bd.save()

        # vars
        for v in vs:
            vo = Variable()
            _cache['var_%s' % v.get('id')] = vo
            vo.description = v.get('description')
            bindplanid = '{"%s":["%s","%s"]}' % (plano.description, product_id, plano.id)
            status, vo.key = self._hanlde_repeat_name("key=%s" % v.get('key'), 'Variable', flag, bindplanid)
            if status is not 'success':
                del _cache['var_%s' % v.get('id')]
                _msg.append(vo.key)
                continue;
            vo.value = v.get('value')
            vo.gain = v.get('gain')
            vo.is_cache = v.get('is_cache')
            try:
                author = User.objects.get(name=v.get('authorname'))
                vo.author = author
                vo.save()
                tag = Tag()
                tag.customize = v.get('customize', '')
                tag.planids = bindplanid
                tag.isglobal = 0
                tag.var = vo
                tag.save()
            except:
                author = [author for author in authors if author.get('name') == v.get('authorname')][0]
                authoro = User()
                authoro.name = author.get('name')
                authoro.password = author.get('password')
                authoro.email = author.get('email')
                authoro.sex = author.get('sex')
                authoro.save()
                vo.author = authoro
                vo.save()

        ##dbcons
        for con in dbcons:
            logger.info('-----数据连接导入-----')
            cono = DBCon()
            _cache['dbcon_%s' % con.get('id')] = cono
            status, cono.description = self._hanlde_repeat_name("description=%s" % con.get('description'), 'DBCon',
                                                                flag, scheme)
            logger.info(status, cono.description)
            if status is not 'success':
                del _cache['dbcon_%s' % con.get('id')]
                _msg.append(cono.description)
                continue;
            cono.kind = con.get('kind')
            cono.host = con.get('host')
            cono.port = con.get('port')
            cono.dbname = con.get('dbname')
            cono.username = con.get('username')
            cono.password = con.get('password')
            cono.scheme = scheme
            try:
                author = User.objects.get(name=con.get('authorname'))
                cono.author = author
                cono.save()
            except:
                author = [author for author in authors if author.get('name') == con.get('authorname')]
                if author:
                    author = author[0]
                    authoro = User()
                    authoro.name = author.get('name')
                    authoro.password = author.get('password')
                    authoro.email = author.get('email')
                    authoro.sex = author.get('sex')
                    authoro.save()
                    cono.author = authoro
                    cono.save()

        ##funcs
        for f in funcs:
            fo = Function()
            _cache['func_%s' % f.get('id')] = fo
            fo.kind = f.get('kind')
            fo.description = f.get('description')
            fo.name = f.get('name')
            status, fo.flag = self._hanlde_repeat_name("flag=%s" % f.get('flag'), 'Function', flag)

            if status is not 'success':
                del _cache['func_%s' % f.get('id')]
                _msg.append(fo.flag)
                continue;

            fo.body = f.get('body')

            try:
                author = User.objects.get(name=f.get('authorname'))
                fo.author = author
                fo.save()
            except:
                author = [author for author in authors if author.get('name') == f.get('authorname')][0]
                authoro = User()
                authoro.name = author.get('name')
                authoro.password = author.get('password')
                authoro.email = author.get('email')
                authoro.sex = author.get('sex')
                authoro.save()
                fo.author = authoro
                fo.save()
        # 建立依赖关系
        plan_cases = bl['relation']['plan_case']
        case_step = bl['relation']['case_step']
        case_case = bl['relation']['case_case']
        step_businesss = bl['relation']['step_business']

        logger.info('[step_businesss]=>%s' % step_businesss)
        ##
        for k, vs in plan_cases.items():
            plan = _cache.get('plan_%s' % k)
            for v, ordervalue in vs:
                case = _cache.get('case_%s' % v)
                order = Order()
                order.kind = 'plan_case'
                order.main_id = plan.id
                order.follow_id = case.id
                order.value = ordervalue
                try:
                    author = User.objects.get(name=callername)
                    order.author = author
                    order.save()
                except:
                    author = [author for author in authors if author.get('name') == callername][0]
                    authoro = User()
                    authoro.name = author.get('name')
                    authoro.password = author.get('password')
                    authoro.email = author.get('email')
                    authoro.sex = author.get('sex')
                    authoro.save()
                    order.author = authoro
                    order.save()

        ##
        logger.info('case_step')
        for k, vs in case_step.items():
            case = _cache.get('case_%s' % k)
            logger.info('查询case缓存=>', 'case_%s' % k)
            for v, ordervalue in vs:
                step = _cache.get('step_%s' % v)
                order = Order()
                order.kind = 'case_step'
                order.main_id = case.id
                order.follow_id = step.id
                order.value = ordervalue
                try:
                    author = User.objects.get(name=callername)
                    order.author = author
                    order.save()
                except:
                    author = [author for author in authors if author.get('name') == callername][0]
                    authoro = User()
                    authoro.name = author.get('name')
                    authoro.password = author.get('password')
                    authoro.email = author.get('email')
                    authoro.sex = author.get('sex')
                    authoro.save()
                    order.author = authoro
                    order.save()
        ##
        logger.info('case_case')
        for k, vs in case_case.items():
            case = _cache.get('case_%s' % k)
            for v, ordervalue in vs:
                #

                case0 = _cache.get('case_%s' % v)
                order = Order()
                order.kind = 'case_case'
                order.main_id = case.id
                order.follow_id = case0.id
                order.value = ordervalue
                try:
                    author = User.objects.get(name=callername)
                    order.author = author
                    order.save()
                except:
                    author = [author for author in authors if author.get('name') == callername][0]
                    authoro = User()
                    authoro.name = author.get('name')
                    authoro.password = author.get('password')
                    authoro.email = author.get('email')
                    authoro.sex = author.get('sex')
                    authoro.save()
                    order.author = authoro
                    order.save()

                    logger.info(traceback.format_exc())

        ##
        logger.info('[step_businesss]')
        for k, vs in step_businesss.items():
            step = _cache.get('step_%s' % k)
            logger.info('[1]=>')
            for v, ordervalue in vs:
                logger.info('[2]=>')
                business = _cache.get('business_%s' % v)
                logger.info('[business]=>', business)
                order = Order()
                order.kind = 'step_business'
                order.main_id = step.id
                order.follow_id = business.id
                order.value = ordervalue

                # if not ordervalue:
                #   order.value='1.1'

                try:
                    author = User.objects.get(name=callername)
                    order.author = author
                    order.save()
                except:
                    author = [author for author in authors if author.get('name') == callername][0]
                    authoro = User()
                    authoro.name = author.get('name')
                    authoro.password = author.get('password')
                    authoro.email = author.get('email')
                    authoro.sex = author.get('sex')
                    authoro.save()
                    order.author = authoro
                    order.save()

                logger.info('[建议步骤测试点关联]=>%s' % order)

        # 处理回调信息
        callbackmsg = ''
        for index in range(len(_msg)):
            callbackmsg = "%s.%s" % (int(index + 1), _msg[index]) + ' '

        return ('success', callbackmsg)