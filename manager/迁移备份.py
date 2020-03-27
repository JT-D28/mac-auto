def _replace_function(user,str_):
    '''计算函数引用表达式
    '''
    # print('--计算引用表达式=>',str_)

    resultlist=[]
    builtinmethods=[x.name for x in getbuiltin()]
    str_=str(str_)

    call_str_list=re.findall('\$\[(.*?)\]',str_)

    if len(call_str_list)==0:return ('success',str_)

    for call_str in call_str_list:
        fname=re.findall('(.*?)\(', call_str)
        f=None
        try:
            f=Function.objects.get(name=fname[0])
        except:
            pass

        status,res=Fu.call(f,call_str,builtin=(lambda:True if fname in builtinmethods else False)())
        resultlist.append((status,res))

        if status is 'success':
            print('替换函数引用 %s => %s '%('$[%s]'%call_str,str(res)))
            str_=str_.replace('$[%s]'%call_str,str(res))


    if len([x for x in resultlist if x[0] is 'success'])==len(resultlist):
        print('--成功计算引用表达式=>',str_)
        return ('success',str_)
    else:
        alist=[x[1] for x in resultlist if x[0] is not 'success']
        print('--异常计算引用表达式=>',alist[0])
        return ('error',alist[0])

class Transformer(object):
    _businessid_cache = dict()
    
    def __init__(self, callername, byte_list, content_type, taskid):
        
        print('【Transformer工具初始化】')    
        self._before_transform_check_flag = ('success', '')
        self._difference_config_file(byte_list)
        self.transform_id = taskid
        self.callername = callername
        self._has_create_var = False
    
    def _difference_config_file(self, byte_list):
        '''
        区分配置文件&用例文
        '''
        print('【识别上传文件】')
        try:
            print('上传文件数量=>', len(byte_list))
            for byte in byte_list:
                cur_workbook = xlrd.open_workbook(file_contents=byte)
                try:
                    global_sheet = cur_workbook.sheet_by_name('Global')
                    self.config_workbook = cur_workbook
                except:
                    self.data_workbook = getattr(self, 'data_workbook', [])
                    self.data_workbook.append(cur_workbook)
            
            ##校验文件
            print('配置=>', getattr(self, 'config_workbook', None))
            print('数据=>', getattr(self, 'data_workbook', []))
            if getattr(self, 'config_workbook', None) is None:
                self._before_transform_check_flag = ('fail', '没上传配置文件')
                return
            
            if getattr(self, 'data_workbook', []) == []:
                self.data_workbook = []
                self._before_transform_check_flag = ('fail', '没上传用例文件')
                return
            
            if len(self.data_workbook) > 1:
                self._before_transform_check_flag = ('fail', '暂时不支持1个配置文件对应多个case文件')
                return
        except:
            print(traceback.format_exc())
            self._before_transform_check_flag = ('error', '无法区分配置和用例文件')
            return
        
        self._before_transform_check_flag = ('success', '上传文件识别成功..')
    
    def _check_file_valid(self):
        """
        检查文件是否合法
        """
        return self._before_transform_check_flag
    
    def _check_function(self):
        '''
        检查函数是否定义 related_id准备
        '''
        all_function=list(Function.objects.all())+getbuiltin()
        all_function_name=[x.name for x  in all_function]
        try:
            #检查业务数据函数名称
            for dwb in self.data_workbook:
                act_data=self._get_workbook_sheet_cache(dwb,'执行数据')

                for rowdata in act_data:
                    vs=''
                    for v in rowdata.values():
                        vs+=str(v).strip()
                    if not vs:
                        continue;

                    step=Step()
                    step.author=User.objects.get(name=self.callername)
                    func_field_value=rowdata['函数名称']
                    # if func_field_value  not in all_function_name:
                    #print('canshu=>',rowdata['参数值'])
                    if '：' not in  rowdata['参数值'] and ':' not in rowdata['参数值']:
                        funcname=rowdata['函数名称']

                        #print('h=>',funcname)
                        if funcname not in(all_function_name):
                            #print('row=>',rowdata)
                            print('all_function_name',all_function_name)
                            return ('fail','执行数据页没定义函数[%s],请先定义'%funcname)

            #检查变量定义获取方式
            var_sheet=self._get_workbook_sheet_cache(dwb,'变量定义')
            for rowdata in var_sheet:
                gain=rowdata['获取方式'].strip()
                if _is_function_call(gain):
                    print('gain=>',gain)
                    methodname=re.findall('(.*?)\(.*?\)', gain)[0]
                    if methodname not in all_function_name:
                        print('all_function_name',all_function_name)
                        
                        return ('fail','变量定义页没定义函数[%s],请先定义'%methodname)

            return ('success','函数校验通过')
        except:
            return ('error','函数库内校验发生异常[%s]'%traceback.format_exc())

    def _set_content_type_flag(self,kind):
        #kind=('json','xml','urlencode','not json','not xml','not urlencode')
        if kind=='json':
            self.is_xml=False
        elif kind=='xml':
            self.is_xml=True
        elif kind=='urlencode':
            self.is_xml=False
        elif kind=='not_json':
            self.is_xml=None
        elif kind=='not_xml':
            self.is_xml=False
        elif kind=='not_urlencode':
            self.is_xml=True

    def _get_itf_basic_conifg(self):
        '''
        获取config init基本配置
        '''
        init_cache = self._get_workbook_sheet_cache(self.config_workbook, 'Init')
        
        for rowdata in init_cache:
            # print('basic_config=>',rowdata)
            if rowdata['默认对象'].lower().strip() == 'y' and rowdata['对象类型'].lower().strip() == 'interface':
                # print('fadfljadfljadajf')
                pv = rowdata['参数']
                if self._is_xml_h():
                    return {
                        'host': pv.split(',')[0],
                        'port': pv.split(',')[1],
                        
                    }
                else:
                    return {
                        'host': pv.split(',')[0]
                        
                    }
        
        return None
    
    def _is_xml_h(self):
        init_cache = self._get_workbook_sheet_cache(self.config_workbook, 'Init')
        
        for rowdata in init_cache:
            if rowdata['默认对象'].lower().strip() == 'y' and rowdata['对象类型'].lower().strip() == 'interface':
                pv = rowdata['参数']
                size = len(pv.split(','))
                # print('====www=>',size)
                
                return True if size == 5 else False
    
    def _get_itf_detail_config(self):
        '''获取接口具体配置信息
        '''
        res={}

        script_cache=self._get_workbook_sheet_cache(self.config_workbook, 'Scripts')
        for rowdata in script_cache:
            try:
                rowdatalist=rowdata['脚本全称'].split(',')
                #print('脚本全称=>',rowdatalist)

                path=rowdatalist[0]
                method=rowdatalist[1]
                content_type='urlencode'

                if len(rowdatalist)>2:
                    content_type=rowdatalist[2]

                res[rowdata['脚本简称']]={
                'path':path,
                'method':method,
                'content_type':(lambda:'urlencode' if content_type=='iphone' else content_type)()
                }
            except:
                print(traceback.format_exc())
                continue;

        return res

    def _get_workbook_sheet_cache(self,workbook,sheetname):
        """
        获取sheet键值数据
        """

        cache=[]

        sheet=workbook.sheet_by_name(sheetname)
        sheet_rows=sheet.nrows
        titles=sheet.row_values(0)
        title_order_map={}
        for index in range(len(titles)):
            title_order_map[str(index)]=str(titles[index])


        for rowindex in range(1, sheet_rows):
            row_map={}
            row=sheet.row_values(rowindex)
            for cellindex in range(len(row)):
                ctype=sheet.cell(rowindex,cellindex).ctype
                
                k=title_order_map[str(cellindex)]
                v=row[cellindex]
                #print('%s->%s'%(k,v))
                if 2==ctype:
                    v=int(v)
                row_map[k]=v

            cache.append(row_map)
        # print(kv_map)
        return cache

    def _get_business_sheet_cache(self):
        '''
        获取业务数据缓存
        '''
        cache={}
        index=0

        for dwb in self.data_workbook:
            sheets=dwb.sheet_names()
            for sheetname in sheets :
                if sheetname not in ('变量定义','执行数据'):
                    key='%s_I%s'%(sheetname,index)
                    cache[key]=self._get_workbook_sheet_cache(dwb, sheetname)

            index=index+1
        return cache


    def _get_act_data(self,d):
        r=[]
        for x in d:
            r+=d[x]

        return r


    def transform(self):

        print('【准备数据转化】')
        status,msg=self._check_file_valid()
        #print('检查结果=>',status,msg)
        if status!='success':
            return (status,msg)

        status,msg=self._check_function()
        if status!='success':
            return (status,msg)
        #workbookflag->actdata
        self.act_data_map={}
        self.act_data=[]
        self.var_data=[]
        resultlist=[]

        workbook_flag=0
        for dwb in self.data_workbook:
            result=[]
            self.act_data_map[workbook_flag]=self._get_workbook_sheet_cache(dwb,'执行数据')
            workbook_flag=workbook_flag+1
            self.act_data=self._get_workbook_sheet_cache(dwb,'执行数据')+self.act_data
            self.var_data=self._get_workbook_sheet_cache(dwb,'变量定义')+self.var_data

            print('【开始转换】接收数据集[%s,%s]'%(dwb,self.config_workbook))
            resultlist=[]
            f4=self.add_case()
            f5=self.add_plan()
            f1=self.add_var()
            f2=self.addbusinessdata()

            time.sleep(5)

            f3=self.add_step_data()
            f6=self.add_db_con()

            print('f1=>',f1)
            print('f2=>',f2)
            print('f3=>',f3)
            print('f4=>',f4)
            print('f5=>',f5)
            print('f6=>',f6)
            result.append(f1)
            result.append(f2)
            result.append(f3)
            result.append(f4)
            result.append(f5)
            result.append(f6)
            resultlist.append(result)
        ##分析结果
        for rs in resultlist:
            for r in rs:
                if r[0]!='success':
                    self._rollback()
                    return ('fail','转换失败')

        return('success','转换成功!')


    def _get_header(self,hid,**kws):
        _f=('数据编号','头部说明')
        c=''
        # print('fdajflda=>',self._get_business_sheet_cache().keys())
        cache=self._get_business_sheet_cache().get('head_I0')
        for rowdata in cache:
            if str( rowdata['数据编号'])==str(hid):
                pass

                vv=''
                for k,v in rowdata.items():
                    if k in('数据编号','头部说明'):continue;
                    if k in kws:
                        try:
                            vv=int(kws.get(k))
                        except:
                            vv=kws.get(k)

                        c+='<%s>%s</%s>'%(k,vv,k)
                    else:
                        try:
                            vv=int(v)
                        except:
                            vv=v

                        c+='<%s>%s</%s>'%(k,vv,k)


        # with open('header.txt','a+') as f:
        #     f.write('<Head>%s</Head>\n\n'%c)
        return '<Head>%s</Head>'%c

    def addbusinessdata(self):
        '''
        插入业务数据
        '''
        try:
            print('【开始添加业务数据】')
            _meta=['测试点','DB检查数据','UI检查数据','接口检查数据','数据编号']
            _m={
            '测试点':'businessname',
            'DB检查数据':'db_check',
            'UI检查数据':'',
            '接口检查数据':'itf_check',
            '数据编号':'',
            '头部信息':'',
            '头部说明':'',

            }

            ##接口业务数据
            print('--开始添加接口业务数据')

            for sheetname,cache in self._get_business_sheet_cache().items():

                print('sss=>',sheetname,cache)

                if sheetname.__contains__('head') or sheetname.__contains__('报文说明'):
                    continue;
                rowindex=0
                
                sheet_index=1#sheet明细行号
                for rowdata in cache:
                   #s print('rowdata=>',rowdata)
                    #print('=>1')

                    xmlcontent=''
                    params={}

                    headm={}
                    hid=-1

                    headv=rowdata.get('头部信息',None)##error
                    if headv:
                        headv=str(headv).replace('\n','')
                        hlist=str(headv).split('|')
                        hid=hlist[0]
                        
                        if len(hlist)>1:
                            for i in range(1,len(hlist)):
                                headm[hlist[i].split('=')[0]]=hlist[i].split('=')[1]

                    business=BusinessData()
                    business.businessname='%s_%s_%s'%(sheetname,sheet_index,self.transform_id)
                    sheet_index+=1

                    #print('=>2')
                    for fieldname,value in rowdata.items():
                        #print('=>3')
                        try:
                            if fieldname  in _m:
                                #print('=>4')
                                # if fieldname =='测试点':
                                #     business.businessname="%s_%s"%(value.strip(),self.transform_id)
                                #     #business.businessname="%s"%(value.strip())
                                #     continue
                                if fieldname=='DB检查数据':
                                    #business.db_check=self._replace_var(value)
                                    dck=self._replace_var(value)
                                    dck=dck.replace('\n','')
                                    if dck:
                                        if dck.__contains__('sleep'):
                                            business.db_check='|'.join(dck.split('|')[1:])
                                            business.postposition=dck.split('|')[0]

                                    continue
                                elif fieldname=='接口检查数据':
                                    business.itf_check=self._replace_var(value)
                                    continue
                            else:
                                #print('=>5')
                                ##hhhh
                                #print('==========fdafda=>',self._is_xml_h())
                                if self._is_xml_h():

                                    nodeinfo=''
                                    if fieldname.startswith('<'):
                                        xmlcontent+=fieldname

                                    else:
                                        xmlcontent+='<%s>%s</%s>'%(fieldname,value,fieldname)

                                else:
                                    params[fieldname]=value
                        except:
                            print(traceback.format_exc())

                    #print('=>6')
                    if  params.get('json',None):
                        params=params.get('json')
                    #print('=>7')
                    params=(str(params)).replace('"',"'").replace('\n','')
                    #print('[%s]params=>%s'%(sheet_index,str(params)))

                    if xmlcontent == '':
                        business.params=self._replace_var(params,sheet_index+1,rowindex+1)
                    else:
                        xmlcontent='<Root>#head#%s</Root>'%xmlcontent
                        xmlcontent=xmlcontent.replace('#head#',self._get_header(hid,**headm))
                        
                        business.params=self._replace_var(xmlcontent)

                    business.save()
                    print('==添加接口业务数据[%s]'%business)
                    self._businessid_cache['%s:%s'%(sheetname,rowindex+1)]=business.id
                    rowindex=rowindex+1

            print('---开始添加函数业务数据')
            ##函数业务数据
            aaindex=0
            for rowdata in self.act_data:
                aaindex=aaindex+1
                # print('--尝试添加函数业务数据')
                paramfield=rowdata['参数值']
                # print('paramfield=>',paramfield)
                if  not paramfield.__contains__('：') and not paramfield.__contains__(':'):
                    #businessname重复校验
                    name="%s_%s_%s"%(rowdata['测试要点概要'].strip(),str(aaindex),self.transform_id)
                    #name="%s"%(rowdata['测试要点概要'].strip())
                    size=len(list(BusinessData.objects.filter(businessname=name)))
                    # print('size=>',size)
                    if size>0:
                        print('测试点已存在[%s] next'%name)
                        continue
                    business=BusinessData()
                    business.businessname=name
                    business.params=self._replace_var(paramfield)
                    business.save()
                    print('==添加函数业务数据[%s]'%business)

            return('success','')
        except:
            return ('error','插入业务数据异常=>%s'%traceback.format_exc())



    def _get_step_names(self):
        return [x for x in self.data_workbook.sheet_names() if x not in('变量定义','执行数据')]


    def _replace_var(self,old,si=None,li=None):
        '''
        1.执行数据参数值
        2.DB检查数据
        3.接口检查数据
        4.数据字段
        '''
        # print('【变量转化】=>',old)
        varlist=re.findall('{[ru,].*?}', old)
        if len(varlist)>0:
            for x in varlist:
                varname=re.findall('{[ru],(.*?)}', x)
                # print(varname)
                if x.__contains__('lv_Signature') and si and li:
                    old=old.replace(x,'{{%s_%s_%s_%s}}'%(str(varname[0]).split('$')[0],si,li,self.transform_id))
                    print('替换签名变量名=>','{{%s_%s_%s_%s}}'%(str(varname[0]).split('$')[0],si,li,self.transform_id))
                else:
                    old=old.replace(x,'{{%s_%s}}'%(varname[0],self.transform_id))

        # print('转换后=>',old)
        return old


    def add_db_con(self):
        '''
        添加数据连接 oracle默认sid方式

        '''
        try:
            global_sheet=self._get_workbook_sheet_cache(self.config_workbook,'Global')
            con=None
            groupid=0
            for rowdata in global_sheet:
                # print('global_row->',rowdata)
                varname=rowdata['变量名称']

                if 'gv_dbtype' in varname:
                    groupid=groupid+1
                    con=DBCon()
                    dbtype=rowdata['值']
                    if dbtype.strip()=='oracle':
                        con.kind='oracle_sid'
                    else:
                        con.kind=dbtype

                elif 'gv_dbuser' in varname:
                    con.username=rowdata['值']
                elif 'gv_dbpwd' in varname or 'gv_dbpasswd' in varname:
                    con.password=rowdata['值']
                elif 'gv_dbhost' in varname:
                    con.host=rowdata['值']
                elif 'gv_dbport' in varname:
                    con.port=rowdata['值']
                elif 'gv_dbname' in varname:
                    con.dbname=rowdata['值']
                    con.host=con.dbname.split('/')[0]
                    con.dbname=con.dbname.split('/')[1]
                    if not con.port:
                        con.port='1521'
                    con.author=User.objects.get(name=self.callername)
                    con.description="库_%s_%s_%s"%(self.callername,self.transform_id,groupid)

                    print('新增数据连接=>')
                    print('dbnaem=>',con.dbname)
                    print('description=>',con.description)
                    print('username=>',con.username)
                    print('password=>',con.password)
                    print('host=>',con.host)
                    print('port=>',con.port)

                    con.save()
            return ('success','')
        except:
            return ('error','新增数据连接失败->%s'%traceback.format_exc())


    def add_step_data(self):
        '''
        添加step
        '''
        try:
            print('【开始添加步骤数据】')
            case=None

            for k,v in self.act_data_map.items():
                case=list(Case.objects.filter(description='迁移用例_%s_%s'%(self.transform_id,k)))[0]
                row_index=0
                for rowdata in v:
                    # step=Step()
                    # step.temp=''
                    # step.author=User.objects.get(name=self.callername)
                    func_field_value=rowdata['函数名称']
                    # if func_field_value  not in all_function_name:
                    row_index+=1
                    if rowdata['参数值'].__contains__('：') or  rowdata['参数值'].__contains__(':') :
                        #接口
                        bkname=''
                        if rowdata['参数值'].__contains__(':'):
                            bkname=rowdata['参数值'].split(':')[0]

                        elif rowdata['参数值'].__contains__('：'):
                            bkname=rowdata['参数值'].split('：')[0]

                        # print('bkname3=>',rowdata['参数值'].split('：'))
                        # print('bkname2=>',bkname)

                        ##多条
                        if rowdata['参数值'].__contains__('-'):
                            start=0
                            end=0
                            try:
                                start=rowdata['参数值'].split(':')[1].split('-')[0]
                                end=rowdata['参数值'].split(':')[1].split('-')[1]
                            except:
                                start=rowdata['参数值'].split('：')[1].split('-')[0]
                                end=rowdata['参数值'].split('：')[1].split('-')[1]

                            #count=int(end)-int(start)+1
                            for i in range(int(start),int(end)+1):
                                print('==多条=')

                                step=Step()
                                step.temp=''
                                step.author=User.objects.get(name=self.callername)

                                basic_config=self._get_itf_basic_conifg()
                                detail_config=self._get_itf_detail_config()

                                #print('基础配置=>',basic_config)
                                #
                                #print('详细配置=>',detail_config)
                                step.step_type='interface'
                                step.body=''
                                
                                step.headers=''
                                step.description='%s_%s_%s'%(rowdata['测试要点概要'],i,self.transform_id)

                                funcname=rowdata['函数名称']
                                try:
                                    step.content_type=detail_config.get(funcname).get('content_type')
                                    step.method=detail_config.get(funcname).get('method')
                                except:
                                    print('配置文件里没找到函数名[%s]称所对应的的配合信息'%funcname)

                                print('===============start===content_type 负值===================')
                                if self._is_xml_h():
                                    
                                    print('==================content_type 负值===================')
                                    if basic_config:
                                        step.content_type='xml'
                                        step.url='base_url_%s'%self.transform_id
                                        ##
                                        try:
                                            if not self._has_create_var:
                                                v=Variable()
                                                v.author=User.objects.get(name=self.callername)
                                                v.key='base_url_%s'%self.transform_id
                                                v.value='%s:%s'%(basic_config.get('host',''),basic_config.get('port',''))
                                                v.description='迁移url'
                                                v.gain=''
                                                v.save()

                                                self._has_create_var=True
                                        except:
                                           # print('9'*100)
                                           pass
                                else:
                                    print('==非xml')
                                    print('basic_config=>',basic_config)
                                    if basic_config:
                                        print('=有基础配置=')
                                        try:

                                            #step.url="%s%s"%(basic_config.get('host',''),detail_config.get(funcname).get('path',''))
                                            step.url="%s%s"%('{{base_url_%s}}'%self.transform_id,detail_config.get(funcname).get('path',''))
                                           # print('$$'*100)   
                                            print('step.url=>',step.url)
                                        except:
                                            print(traceback.format_exc())
                                        ##
                                        try:

                                            if not self._has_create_var:
                                                v=Variable()
                                                v.author=User.objects.get(name=self.callername)
                                                v.key='base_url_%s'%self.transform_id
                                                v.value=basic_config.get('host','')
                                                v.description='迁移url'
                                                v.gain=''
                                                v.save()

                                                self._has_create_var=True
                                        except:
                                           # print('9'*100)
                                           pass

                                is_exist=len(list(Step.objects.filter(description=step.description)))
                                if is_exist==0:
                                    step.save()
                                    print('添加步骤=>',step)
                                else:
                                    step=Step.objects.get(description=step.description)

                                ##step关联业务数据
                                self.add_case_step_relation(case.id, step.id)
                                print('--尝试获取业务id=>','%s_I0_%s_%s'%(bkname,i,self.transform_id))
                                b=BusinessData.objects.get(businessname='%s_I0_%s_%s'%(bkname,i,self.transform_id))
                                print('--成功获取业务id=>%s'%b)
                               

                                
                                self.add_step_business_relation(step.id, b.id)
                                #self.add_step_bussiness_relation2(step.id, self.data_workbook[k],rowdata['参数值'])
                                #self.add_case_business_relation2(case.id, self.data_workbook[k],rowdata['参数值'])

                        #单条
                        else:
                            step=Step()
                            step.temp=''
                            step.author=User.objects.get(name=self.callername)

                            lineindex=None
                            try:
                                lineindex=rowdata['参数值'].split(':')[1]
                            except:
                                lineindex=rowdata['参数值'].split('：')[1]


                            basic_config=self._get_itf_basic_conifg()
                            detail_config=self._get_itf_detail_config()

                            #print('基础配置=>',basic_config)
                            #
                            #print('详细配置=>',detail_config)
                            step.step_type='interface'
                            step.body=''
                            step.headers=''
                            step.description='%s_%s_%s'%(rowdata['测试要点概要'],row_index,self.transform_id)

                            funcname=rowdata['函数名称']
                            try:
                                step.content_type=detail_config.get(funcname).get('content_type')
                                step.method=detail_config.get(funcname).get('method')

                            except:
                                print('配置文件里没找到函数名[%s]称所对应的的配合信息'%funcname)
                            if self._is_xml_h():
                                if basic_config:
                                    step.url='%s:%s'%(basic_config.get('host',''),basic_config.get('port',''))
                                    step.content_type='xml'

                            else:
                                if basic_config:
                                    #step.url="%s%s"%(basic_config.get('host',''),detail_config.get(funcname).get('path',''))
                                    step.url="%s%s"%('{{base_url_%s}}'%self.transform_id,detail_config.get(funcname).get('path',''))
                                    try:
                                        if not self._has_create_var:
                                            v=Variable()
                                            v.author=User.objects.get(name=self.callername)
                                            v.key='base_url_%s'%self.transform_id
                                            v.value=basic_config.get('host','')
                                            v.description='迁移url'
                                            v.gain=''
                                            v.save()

                                            self._has_create_var=True
                                    except:
                                       # print('9'*100)
                                       pass                      
                            # print('url=>',step.url)
                            # step.url=self._replace_var(step.url)

                            is_exist=len(list(Step.objects.filter(description=step.description)))
                            if is_exist==0:
                                step.save()
                                print('添加步骤=>',step)
                            else:
                                step=Step.objects.get(description=step.description)

                            ##step关联业务数据
                            self.add_case_step_relation(case.id, step.id)

                            print('bkname=>',bkname)
                            print('lineindex=>',lineindex)
                            print('带匹配=>','%s_I0_%s_%s'%(bkname,lineindex,self.transform_id))
                            business_id=BusinessData.objects.get(businessname='%s_I0_%s_%s'%(bkname,lineindex,self.transform_id)).id
                            self.add_step_business_relation(step.id, business_id)
                            #self.add_step_bussiness_relation2(step.id, self.data_workbook[k],rowdata['参数值'])
                            #self.add_case_business_relation2(case.id, self.data_workbook[k],rowdata['参数值'])

                    else:
                        #函数
                        step=Step()
                        step.temp=''
                        step.author=User.objects.get(name=self.callername)
                        step.step_type='function'
                        step.body=func_field_value
                        # print('functionname=>',step.body)
                        step.description="%s_%s_%s"%(rowdata['测试要点概要'].strip(),row_index,self.transform_id)
                        #step.description="%s"%(rowdata['测试要点概要'].strip())
                        try:
                            step.related_id=Function.objects.get(name=step.body.strip()).id
                        except:
                            pass

                        step.save()
                        #step关联业务数据
                        try:
                            name="%s_%s_%s"%(rowdata['测试要点概要'].strip(),row_index,self.transform_id)

                            # l=list(BusinessData.objects.filter(businessname=name))
                            # print('size=>',len(l))
                            print('待匹配业务名=>',name)
                            businessId=BusinessData.objects.get(businessname=name).id
                            #businessId=BusinessData.objects.get(businessname="%s"%rowdata['测试要点概要'].strip()).id
                            self.add_case_step_relation(case.id, step.id)
                            self.add_step_business_relation(step.id, businessId)
                            #self.add_case_businss_relation(case.id, businessId)

                        except:
                            print(traceback.format_exc())
                            print('函数步骤没找到关联业务数据[%s]'%name)

            time.sleep(1)

            # genorder(kind='step',parentid=case.id)
            print('==添加步骤结束')
            return ('success','')
        except:
            return ('error','添加步骤异常[%s]'%traceback.format_exc())



    def add_plan(self):
        plan=None
        try:
            print('【添加计划】')
            dsp='迁移计划_%s'%self.transform_id
            length=len(list(Plan.objects.filter(description=dsp)))
            if length==0:
                plan=Plan()
                plan.description=dsp
                plan.author=User.objects.get(name=self.callername)
                plan.save()
                print('=新建计划=>',plan)

                #
                product=None
                L=list(Product.objects.filter(description='数据迁移'))
                exist=len(L)
                if exist==0:
                    product=Product()
                    product.description='数据迁移'
                    product.author=User.objects.get(name=self.callername)
                    product.save()
                else:
                    product=L[0]

                order=Order()
                order.kind='product_plan'
                order.main_id=product.id
                order.follow_id=plan.id
                order.value='1.1'
                order.author=User.objects.get(name=self.callername)
                order.save()
            else:
                plan=list(Plan.objects.filter(description=dsp))[0]

            self.add_plan_case_relation()

            # genorder(kind='case',parentid=plan.id)
            return ('success','')

        except:
            return ('error','添加计划异常=>%s'%traceback.format_exc())

    def add_case(self):
        case=None

        try:
            for k,v in self.act_data_map.items():
                dsp='迁移用例_%s_%s'%(self.transform_id,k)
                #dsp='迁移用例_%s'%k

                length=len(list(Case.objects.filter(description=dsp)))
                if length==0:
                    case=Case()
                    case.description=dsp
                    case.author=User.objects.get(name=self.callername)
                    case.save()
                    print('【添加用例】%s'%case.description)
            return ('success','')

        except:
            return ('error','添加用例异常=>%s'%traceback.format_exc())

    def add_plan_case_relation(self):
        # print('【关联计划和用例】')
        for k in self.act_data_map:

            plan=list(Plan.objects.filter(description='迁移计划_%s'%(self.transform_id)))[0]
            #plan=list(Plan.objects.filter(description='迁移计划_%s'%self.transform_id))[0]
            case=list(Case.objects.filter(description='迁移用例_%s_%s'%(self.transform_id,k)))[0]
            # plan.cases.add(case)
            order=Order()
            order.kind='plan_case'
            order.main_id=plan.id
            order.follow_id=case.id
            order.author=User.objects.get(name=self.callername)
            order.value='1.1'
            order.save()

    def add_case_step_relation(self,case_id,step_id):
        from .cm import getnextvalue
        #print('【关联用例和业务数据】')
        # step=Step.objects.get(id=step_id)
        # case=Case.objects.get(id=case_id)
        # case.businessdatainfo.add(business)

        length=len(list(Order.objects.filter(kind='case_step',main_id=case_id,follow_id=step_id)))
        if length==0:
            order=Order()
            order.kind='case_step'
            order.main_id=case_id
            order.follow_id=step_id
            order.author=User.objects.get(name=self.callername)
            order.value=getnextvalue(order.kind,order.main_id)
            order.save()


    def add_case_step_relation2(self,case_id,workbook,paramfieldvalue):

        print('【步骤关联业务数据】')
        case=Case.objects.get(id=case_id)
        sheetname=''

        if paramfieldvalue.__contains__('：'):
            sheetname=paramfieldvalue.split('：')[0]
        elif paramfieldvalue.__contains__(':'):
            sheetname=paramfieldvalue.split(':')[0]

        cache=self._get_workbook_sheet_cache(workbook,sheetname)#?????
        # is_contain_test_point_col=cache[0].__contains__('测试点'
        #根据参数列数字筛选合适的业务数据
        rangestr=''
        if paramfieldvalue.__contains__('：'):
            rangestr=paramfieldvalue.split('：')[1]
        elif paramfieldvalue.__contains__(':'):
            rangestr=paramfieldvalue.split(':')[1]


        fit=[]
        start=''
        end=''
        if rangestr.__contains__('-'):
            start=rangestr.split('-')[0]
            end=rangestr.split('-')[1]

            fit=[x for x in cache if int(x['数据编号'])>=int(start) and int(x['数据编号'])<=int(end)]
        else:
            start=rangestr
            fit=[x for x in cache if x['数据编号']==int(start)]

        for x in fit:
            testpoint=x.get('测试点',None)
            business=None
            if testpoint:
                try:
                    business=BusinessData.objects.get(businessname="%s_%s"%(testpoint,self.transform_id))
                    #business=BusinessData.objects.get(businessname="%s"%testpoint)
                except:
                    print('业务名称[%s_%s]查找返回的业务数据有多条'%(testpoint,self.transform_id))
                    business=list(BusinessData.objects.filter(businessname="%s_%s"%(testpoint,self.transform_id)))[0]
                    #business=list(BusinessData.objects.filter(businessname="%s"%testpoint))[0]
            else:
                business=BusinessData.objects.get(businessname="%s%s_%s"%(sheetname,x.get('数据编号'),self.transform_id))
                #business=BusinessData.objects.get(businessname="%s%s"%(sheetname,x.get('数据编号')))

            case.businessdatainfo.add(business)


            length=len(list(Order.objects.filter(kind='step',main_id=case_id,follow_id=business.id)))
            if length==0:
                order=Order()
                order.kind='step'
                order.main_id=case_id
                order.follow_id=business.id
                order.author=User.objects.get(name=self.callername)
                order.save()



    def add_step_business_relation(self,step_id,business_id):
        '''
        步骤关联业务数据
        '''
        # step=Step.objects.get(id=step_id)
        # business=BusinessData.objects.get(id=business_id)
        print('add_step_business_relation')
        from .cm import getnextvalue
        
        order = Order()
        order.kind = 'step_business'
        order.main_id = step_id
        order.follow_id = business_id
        order.author = User.objects.get(name=self.callername)
        order.value = getnextvalue(order.kind, order.main_id)
        order.save()
        print('==关联函数步骤和测试点[%s]' % order)
    
    # step.businessdatainfo.add(business)
    
    def add_step_bussiness_relation2(self, step_id, workbook, paramfieldvalue):
        '''
        通过参数列定位业务数据

        '''
        from .cm import getnextvalue

        try:
            print('add_step_business_relation2')

            step=Step.objects.get(id=step_id)
            sheetname=''
            if paramfieldvalue.__contains__('：'):
                sheetname=paramfieldvalue.split('：')[0]
            elif paramfieldvalue.__contains__(':'):
                sheetname=paramfieldvalue.split(':')[0]
            cache=self._get_workbook_sheet_cache(workbook,sheetname)#?????
            # is_contain_test_point_col=cache[0].__contains__('测试点'
            #根据参数列数字筛选合适的业务数据
            rangestr=''
            if paramfieldvalue.__contains__('：'):
                rangestr=paramfieldvalue.split('：')[1]
            elif paramfieldvalue.__contains__(':'):
                rangestr=paramfieldvalue.split(':')[1]

            print('f1==>',rangestr)

            fit=[]
            start=''
            end=''
            if rangestr.__contains__('-'):
                start=rangestr.split('-')[0]
                end=rangestr.split('-')[1]

                fit=[x for x in cache if int(x['数据编号'])>=int(start) and int(x['数据编号'])<=int(end)]
            else:
                start=rangestr
                fit=[x for x in cache if int(x['数据编号'])==int(start)]


            print('f2=>',fit)
            for x in fit:
                testpoint=x.get('测试点',None)
                if testpoint:
                    try:
                        business=BusinessData.objects.get(businessname='%s_%s'%(testpoint,self.transform_id))
                        #business=BusinessData.objects.get(businessname='%s'%testpoint)
                    except:
                        print('业务名称[%s_%s]查找返回的业务数据有多条'%(testpoint,self.transform_id))
                        business=list(BusinessData.objects.filter(businessname='%s_%s'%(testpoint,self.transform_id)))[0]
                        #business=list(BusinessData.objects.filter(businessname='%s'%testpoint))[0]
                else:
                    print('-查找测试点=>%s_I0%s_%s'%(sheetname,int(x.get('数据编号')),self.transform_id))
                    business=BusinessData.objects.get(businessname="%s_I0%s_%s"%(sheetname,x.get('数据编号'),self.transform_id))
                    #business=BusinessData.objects.get(businessname="%s%s"%(sheetname,x.get('数据编号')))


                order=Order()
                order.kind='step_business'
                order.main_id=step.id
                order.follow_id=business.id
                order.author=User.objects.get(name=self.callername)
                order.value=getnextvalue(order.kind,order.main_id)
                order.save()

                print('==步骤关联测试点[%s]'%order)
                #step.businessdatainfo.add(business)
        except:
            print(traceback.format_exc())


    def add_var(self):
        try:
            signmethodname=''

            ##常规变量
            for dwb in self.data_workbook:
                var_cache=self._get_workbook_sheet_cache(dwb, '变量定义')
                for var in var_cache:
                    description=var['变量说明'].strip()
                    gain=var['获取方式'].strip()
                    key=var['变量名称'].strip()
                    value=str(var['值']).strip()
                    # is_cache=False
                    var=Variable()
                    var.description=description
                    var.key='%s_%s'%(key,self.transform_id)
                    if  var.key.__contains__('lv_Signature'):
                        signmethodname=re.findall('(.*?)\(',gain)[0]

                    var.gain=self._get_may_sql_field_value(gain)
                    if var.gain.strip():
                        var.value=''
                    else:
                        var.value=self._get_may_sql_field_value(value)
                    var.author=User.objects.get(name=self.callername)
                    var.save()
                    print('==添加变量[%s]'%var)
            

            print('签名信息=>',signmethodname)
            if signmethodname:
                ##签名变量
                si=0
                li=0
                print('--开始处理签名变量')
                for dwb in self.data_workbook:
                    sheets=dwb.sheet_names()
                    for sheetname in sheets :
                        si+=1
                        if sheetname not in ('变量定义','执行数据'):
                            datalist=self._get_workbook_sheet_cache(dwb, sheetname)
                            for d in datalist:
                                li+=1
                                pa=[]
                                for key in d:
                                    if key not in('数据编号','DB检查数据','UI检查数据','接口检查数据','Signature'):
                                        pa.append("%s='%s'"%(key,self._replace_var(str(d[key]))))

                                    if str(d[key]).__contains__('lv_Signature'):
                                        f_pa=[]
                                        f_pa.append("'{{lv_key_%s}}'"%self.transform_id)
                                        if f_pa.__contains__('WebApi'):
                                            f_pa.append("'sendPrivateKey.pem.webapi'")
                                        [f_pa.append(x) for x in pa]

                                        var=Variable()
                                        var.description=''
                                        var.key='lv_Signature_%s_%s_%s'%(si,li,self.transform_id)
                                        var.value=''
                                        var.gain="%s(%s)"%(signmethodname,','.join(f_pa))
                                        var.author=User.objects.get(name=self.callername)
                                        var.save()
                                        print('--新建签名变量=>%s'%var)



            return ('success','')
        except:
            return ('error','添加变量异常=>%s'%traceback.format_exc())

    def _get_may_sql_field_value(self,old):
        '''sql含@链接的字段的处理  多个sql库名按照第一个sql的为准
        '''
        is_first=True
        sqlmatch=re.findall(r'(select|update|delete|insert).*(from|set|into).+(where){0,1}.*', old)
        # print(sqlmatch)
        if sqlmatch:
            groupid=1
            new_sql_list=[]
            sqllist=old.split(';')
            for sql in sqllist:
                if sql.strip()=='':
                    continue;
                new_sql=''
                if is_first:
                    is_first=False
                    if '@' in sql:
                        groupid=sql.split('@')[1]
                        length=len(groupid)
                        #print('len=>',length)
                        new_sql_list.append(sql[0:-int(length+1)])
                    else:
                        new_sql_list.append(sql)


                else:
                    if '@' in sql:
                        length=len(sql.split('@')[1])
                        new_sql_list.append(sql[0:-int(length+1)])

                    else:
                        new_sql_list.append(sql)

            return ';'.join(new_sql_list)+'@'+"库_%s_%s_%s"%(self.callername,self.transform_id,groupid)
        else:
            return old

    def _delcaserelation(self,caseid):
        try:
            Case.objects.get(id=caseid).delete()

        except:
            pass

        L1=list(Order.objects.filter(kind='case_case',main_id=caseid))
        L2=list(Order.objects.filter(kind='case_step',main_id=caseid))
        for o1 in L1:
            self._delcaserelation(o1.follow_id)
            o1.delete()

        for o2 in L2:
            businesslist=list(Order.objects.filter(kind='step_business',main_id=o2.follow_id))
            for business in businesslist:
                business.delete()
                try:
                    Step.objects.get(id=order.main_id).delete()
                except:
                    pass

                try:
                    BusinessData.objects.get(id=order.follow_id).delete()
                except:
                    pass

            o2.delete()





    def _rollback(self):
        """
        """
        print('==转换失败,开始回滚操作')
        # order表删除
        plan = Plan.objects.get(description='迁移计划_%s' % self.transform_id)
        planid = plan.id
        
        L1 = list(Order.objects.filter(kind='plan_case', main_id=planid))
        for o1 in L1:
            self._delcaserelation(o1.follow_id)
        
        plan.delete()
        
        # 清除实体表
        varlist = list(Variable.objects.all())
        for var in varlist:
            if var.description.__contains__(self.transform_id):
                var.delete()
        
        dblist = list(DBCon.objects.all())
        for db in dblist:
            if db.description.__contains__(self.transform_id):
                db.delete()
        
        print('=结束回滚操作】')