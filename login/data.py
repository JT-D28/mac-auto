、、#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2020-04-17 16:00:23
# @Author  : Blackstone
# @to      :login app操作类

from manager.models import Role,User_UIControl
import traceback
class RoleData():
    

    @classmethod
    def addrole(**kws):
        try:
            role=Role()
            role.description=kws['description']
            users=kws['users']
            for userstr in users.split(','):
                kind=userstr.split('_')[0]
                user_id=userstr.split('_')[1]
                r=User_UIControl()
                r.kind=kind
                r.user_id=user_id
                r.save()

            role.save()
            return {
                'code':0,
                'msg':'添加角色成功'
            }
        except:
            return{
                'code':4,
                'msg':'添加角色异常[%s]'%traceback.format_exc()
            }



    @classmethod
    def delrole():
        pass

    @classmethod
    def updaterole():
        pass

    @classmethod
    def queryrole():
        pass、
            


