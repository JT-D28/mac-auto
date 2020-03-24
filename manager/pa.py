#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2020-03-10 14:31:32
# @Author  : Blackstone
# @to 

from manager.models import Template,TemplateField
from login.models import User
import os,re
from ftplib import FTP
from collections import OrderedDict
from .core import TemplateEncoder,TemplateFieldEncoder,getpagedata
import traceback,json
class MessageParser(object):
    '''
    报文解析器
    '''
    _SYMBOL=('>=','<=','!=','==','>','<','$')

    def __init__(self,parse_format:dict,get_config:dict,expectlist:list):

        self._parse_format=parse_format
        self._get_config=get_config
        self._expectlist=self.expectlist



    def _get_f_value(self,fcode)->tuple:
        '''
        获取指定字段的值
        '''
        text=self._get_message_content(self._get_config)
        kind=self._parse_format.get('kind')

        if kind is None or kind=='0':
            sep=self._parse_format.get('sep')
            
            findex=self._parse_format.get(fcode,None)
            if findex is None:
                return('error','字段[%s]没有配置'%fode)

            pf=text.split(sep)[self._parse_format.get(fcode)]
            return ('success',pf)

        elif kind=='1':
            start,end=self._parse_format.get(fcode,(None,None))
            if start is None or end is None:
                return('error','字段[%s]配置错误')

            return ('success',text.substring(start,end))


    def _get_message_content(self,get_config)->str:
        '''
        获取报文消息内容
        '''
        messga=''
        kind=get_config.get('kind')
        base=get_config.get('location')
        if kind is None or kind==0:
            with open(base) as f:
                messga=f.read()

        elif kind==1:
            ftp = FTP()
            ftp.connect(get_config.get('ip'),get_config.get('port'))
            ftp.login(get_config.get('username'),get_config.get('password'))
            bufsize = 1024
            loc_file=os.path.basename(get_config.get('path'))
            fp = open(loc_file, 'rb')
            ftp.retrbinaly('RETR '+ get_config.get('path'),fp,bufsize)
            ftp.set_debuglevel(0)
            fp.close()

            with open(loc_file) as f:
                messga=f.read()

        return messga

    def _compute_expression(self,child_exp:str):
        '''输入期望子表达式
            输出能正常eval化的字符串
        '''
        res=''
        count=len(re.findall('=',child_exp))
        if count==1:
            res=''' '%s'%s'%s'  '''%(child_exp.split('=')[0],'==',child_exp.split('=')[1])

        elif child_exp.__contains__('$'):
            res=''' '%s'.__contains__('%s') '''%(child_exp.split('$')[0],child_exp.split('$')[1])

        
        else:
            for _a in self._SYMBOL:
                if child_exp.__contains__(_a):
                    res=''' '%s'%s'%s'  '''%(child_exp.split(_a)[0],_a,child_exp.split(_a)[1])

            res='非法比较符'

        try:
            return('success',eval(res))
        except:
            return ('error','表达式异常[%s]'%child_exp)



    def compute(self):
        '''
        计算表达式结果
        约定子表达式左->fcode 右->期望值
        返回所有子表达计算结果
        '''
        _ret=OrderedDict()
        for ex in self._expectlist:
            status,msg=self._compute_expression(ex)
            _ret[ex]=(status,msg)


    @classmethod
    def add_template(cls,**tkws):
        '''
        新建报文模板
        '''
        try:
            t=Template()
            t.kind=tkws['kind']
            t.name=tkws['name']
            t.description=tkws['description']
            t.author=tkws['author']
            t.content_url=tkws['content_url']

            t.save()
            return {
            'code':0,
            'msg':'新增模板成功[%s]'%t
            }

        except:
            err=traceback.format_exc()
            print(err)
            return {
            'code':4,
            'msg':'新增模板异常'
            }

            


    @classmethod
    def del_template(cls,ids):
        '''删除报文模板
        '''
        try:
            for _ in  str(ids).split(','):

                t=Template.objects.get(id=_)
                fl=list(t.fieldinfo.all())
                [_.remove() for _ in fl]
                t.delete()

            return {
            'code':0,
            'msg':'删除模板成功'
            }



        except:
            error='删除模板异常'
            print(error+traceback.format_exc())

            return {
            'code':4,
            'msg':error
            }


    @classmethod
    def edit_template(cls,**tkws):
        '''
        编辑模板
        '''
        try:
            tid=tkws['tid']
            t=Template.objects.get(id=int(tid))
            t.kind=tkws['kind']
            t.name=tkws['name']
            t.description=tkws['description']
            t.content_url=tkws['content_url']
            t.save()

            return {
            'code':0,
            'msg':'编辑模板成功'
            }

        except:
            error='编辑模板异常'
            print(error+traceback.format_exc())
            return {
            'code':4,
            'msg':error
            }


    @classmethod
    def query_template_common(cls,tid):
        try:
            t=Template.objects.get(id=tid)
            jsonstr = json.dumps(t, cls=TemplateEncoder)
            return jsonstr

        except:
            msg='查询模板通用属性异常'
            print(msg+traceback.format_exc())
            return{
            'code':4,
            'msg':msg
            }

    @classmethod
    def query_template_name_list(cls):
        try:
            return {
            'code':0,
            'msg':'',
            'data':[{
            'name':x.name,
            'value':x.id

            } for x in list(Template.objects.all())]
            }

        except:
            msg='获取模板下拉信息异常'
            return{

            'code':4,
            'msg':msg
            }


    @classmethod
    def query_template_field(cls,**kws):
        try:
            tid=int(kws.get('tid'))
            page=kws.get('page')
            limit=kws.get('limit')
            t=Template.objects.get(id=tid)
            fieldlist=list(t.fieldinfo.all())
            s=kws.get('searchvalue',None)
            if s:
                fieldlist=[x for x in fieldlist if x.fieldcode.__contains__(s)]

            res, total = getpagedata(fieldlist, page, limit)

            jsonstr=json.dumps(res, cls=TemplateFieldEncoder,total=total)

            return jsonstr


        except:
            error='查询模板字段异常'
            print(error+traceback.format_exc())
            return {
            'code':4,
            'msg':error
            }

    @classmethod
    def _get_next_order(cls,tid):
        '''
        计算报文模板下个字段的排序号
        '''
        try:
            tflist=list(TemplateField.objects.filter(template=Template.objects.get(id=tid)))
            orderlist=[tf.order for tf in tflist]
            orderlist.sort()
            return ('success',int(int(orderlist[-1])+1))
        except:
            return('error','计算排序号[模板id=%s]异常'%tid)


    @classmethod
    def add_field(cls,**fkws):
        try:
            tid=fkws['tid']
            t=Template.objects.get(id=tid)

            tf=TemplateField()
            tf.fieldcode=fkws['fieldcode']
            tf.description=fkws['description']
            tf.start=fkws['start']
            tf.end=fkws['end']
            tf.index=fkws['index']
            tf.save()

            t.fieldinfo.add(tf)

            return{
            'code':0,
            'msg':'新增字段成功'
            }

        except:
            return{
            'code':4,
            'msg':'新增字段异常=>'+traceback.format_exc()
            }

    @classmethod
    def del_field(cls,ids):
        try:
            for _ in str(ids).split(','):
                TemplateField.objects.get(id=int(_)).delete()

            return {
            'code':0,
            'msg':'删除字段成功.'
            }
        except:
            return{
            'code':4,
            'msg':'删除字段异常=>'+traceback.format_exc()
            }


    @classmethod
    def edit_field(cls,**fkws):
        try:
            tf=TemplateField.objects.get(id=fkws['fid'])
            tf.fieldcode=fkws['fieldcode']
            tf.description=fkws['description']
            tf.index=fkws['index']
            tf.start=fkws['start']
            tf.end=fkws['end']
            tf.save()

            return {
            'code':0,
            'msg':'编辑字段成功.'
            }
        except:
            return {
            'code':4,
            'msg':'编辑字段异常=>'+traceback.format_exc()
            }


    @classmethod
    def query_field_detail(cls,fid):
        try:
            ft=TemplateField.objects.get(id=int(fid))
            return json.dumps(ft,cls=TemplateFieldEncoder)
        except:
            error='查询字段异常'
            print(error+traceback.format_exc())
            return {
            'code':4,
            'msg':error
            }


    @classmethod
    def move_up_or_down(cls,fid,direction='up'):
        '''
        字段上下移动

        '''
        try:
            move_step=(lambda:-1 if direction=='up' else 1)()
            tf=TemplateField.objects.get(id=fid)
            cur_order=tf.order
            t=tf.template
            expected=list(TemplateField.objects.filter(template=t,order=(cur_order+move_step)))

            if len(expected)==0:
                return ('success','边界移动忽略.')

            else:
                tf.order=cur_order+move_step
                tf.save()

                tf0=expected[0]
                tf0.order=tf0.order-move_step
                tf0.save()

                return {
                'code':0,
                'msg':"%s成功"%((lambda:'上移' if direction=='up' else '下移')())
                }

        except:
            return {
            'code':4,
            'msg':'移动异常=>'+traceback.format_exc()
            }

    @classmethod
    def get_parse_config(cls,tid):
        '''
        获取模板具体的解析配置

        '''
        res={}
        try:
            t=Template.objects.get(id=tid)
            res['kind']=t.kind
            res['sep']='|'
            tflist=list(TemplateField.objects.filter(template=t).order_by('order'))
            for tf in tflist:
                res[tf.fieldcode]={
                'order':tf.order,
                'start':tf.start,
                'end':tf.end,
                'index':tf.index,
                'description':tf.description
                }


            return ('success',res)
        except:
            return ('error','获取模板[%s]解析配置异常'%tid)



if __name__=='__main__':
    f={'kind':0,'sep':'|','A':{
        'start':0,
        'end':12,
        'index':1
    }}
    c={}
    expected=['a=111']
    m=MessageParser(f,c,expected)
    m.compute()
    

