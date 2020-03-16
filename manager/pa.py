#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2020-03-10 14:31:32
# @Author  : Blackstone
# @to 
from manager.models import Template,TemplateField
import os,re
from ftplib import FTP
from collections import OrderedDict
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

        if kind is None or kind==0:
            sep=self._parse_format.get('sep')
            
            findex=self._parse_format.get(fcode,None)
            if findex is None:
                return('error','字段[%s]没有配置'%fode)

            pf=text.split(sep)[self._parse_format.get(fcode)]
            return ('success',pf)

        elif kind==1:
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

        
        elif:
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

        return _ret


    @classmethod
    def add_template(cls,**tkws,fkwslist:list):
        t=Template()
        for key in tkws:
            eval('t.%s=%s'%(key,tkws.get(key)))

            


    @classmethod
    def del_template(cls,tid):
        pass

    @classmethod
    def edit_template(cls,**tkws,**fkws):
        pass


    @classmethod
    def query_template_detail(cls,tid):
        pass

    @classmethod
    def add_field(cls,**fkws):
        pass

    @classmethod
    def del_field(cls,fid):
        pass


    @classmethod
    def edit_field(cls,**fkws):
        pass

    @classmethod
    def exchange(cls,src_id,dist_id):
        pass





if __name__=='__main__':
    #m=MessageParser()
    m=map()
    print(m)