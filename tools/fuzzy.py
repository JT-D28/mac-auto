#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-11-01 16:38:29
# @Author  : Blackstone
# @to      :2020-05-18
# @descripttion: mock.js python实现
import traceback
class Mock(object):
    '''
    模糊测试
    基本数据类型

    '''
    @classmethod
    def _next(cls,cur):
        print('cur:',cur)
        if isinstance(cur, (dict,)):
            for k in cur.keys():
                v=cur[k]
                if isinstance(v, (int,float,str,))




    @classmethod
    def test(cls,params):
        try:
            paramdict=eval(params)
            if isinstance(paramdict, (dict,)):
                cls._next(paramdict)
            # else:
            #     print(type(paramdict))

        except:
            print(traceback.format_exc())

data='''{
    'a':1,
    'b':'string',
    'c':[1,2],
    'd':{
        'q':1,
        'j':9
    }
}'''

Mock.test(data)