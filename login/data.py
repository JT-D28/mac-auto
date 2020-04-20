#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2020-04-17 16:00:23
# @Author  : Blackstone
# @to      :login app操作类

from manager.models import Role,User_UIControl
from login.models import User
import traceback
class RoleData():

    @classmethod
    def queryroletable(**kws):
        try:
            return{
                'code':0,
                'msg':'获得权限表',

                'data':list(Role.objects.all())
            }
        except:
            return{
                'code':4,
                'msg':'获得权限异常',
                'data':[]
            }
    

    @classmethod
    def addrole(**kws):
        try:
            role=Role()
            role.name=kws['name']
            role.description=kws['description']
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
    def delrole(**kws):
        try:
            role_id=kws['role_id']
            Role.objects.get(id=role_id).delete()
            return{
                'code':0,
                'msg':'删除角色成功'
            }
        except:
            return{
             'code':4,
             'msg':'删除角色异常'
            }



    @classmethod
    def updaterole(**kws):
        try:
            role_id=kws['role_id']
            role=Role.objects.get(id=role_id)
            role.name=kws['name']
            role.description=kws['description']
            role.save()
            return{
                'code':0,
                'msg':'更新角色成功'
            }

        except:
            return {
                'code':4,
                'msg':'更新角色异常'
            }

    @classmethod
    def queryrole():
        pass


    @classmethod
    def updateuser(**kws):
        '''
        角色添加用户
        '''
        try:
            role_id=kws['row_id']
            user_ids=kws['user_ids']
            role=Role.objects.get(id=role_id)
            role.user.clear()
            for user_id in user_ids.split(','):

                role.user.add(User.objects.get(id=user_id))##???????????????    

            return{
                'code':0,
                'msg':'关联用户成功'
            }

        except:
            return{
                'code':4,
                'msg':'关联用户异常'
            }

    @classmethod
    def deluser(**kws):
        try:
            role_id=kws['row_id']
            user_ids=kws['user_ids']
            role=Role.objects.get(id=role_id)
            for user_id in user_ids.split(','):
                role.user.remove(User.objects.get(id=user_id))             

            return{
                'code':0,
                'msg':'去除关联用户成功'
            }

        except:
            return{
                'code':4,
                'msg':'去除关联用户异常'
            }

            


            


