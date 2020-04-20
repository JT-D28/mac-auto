#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2020-02-17 09:51:22
# @Author  : Blackstone
# @to      :权限管理

import os, traceback
from login.models import *
from manager.models import Role,User_UIControl
from django.db.models import Q
from manager.context import Me2Log as logger

class RoleData():
    '''
    角色操作
    '''

    @classmethod
    def queryroletable(cls,**kws):
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
    def addrole(cls,**kws):
        try:
            role=Role()
            role.name=kws['name']
            role.description=kws['description']
            role.author=kws['user']
            role.save()
            userids=kws['userids'].split(',')
            if(userids!=[]):
                for idk in userids:
                    role.users.add(User.objects.get(id=idk))


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
    def delrole(cls,**kws):
        try:
            role_ids=kws['ids']
            for roleid in role_ids.split(','):
                Role.objects.get(id=roleid).delete()
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
    def updaterole(cls,**kws):
        try:
            role_id=kws['uid']
            role=Role.objects.get(id=role_id)
            role.name=kws['name']
            role.description=kws['description']
            role.users.clear()
            userids=kws['userids'].split(',')
            for idx in userids:
                role.users.add(User.objects.get(id=idx))

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
    def queryonerole(cls,**kws):
        try:
            role_id=kws['uid']
            role=Role.objects.get(id=role_id)
            all_users=User.objects.all()
            all_users_data=[ {'id':y.id,'name':y.name}for y in all_users]

            logger.info(all_users_data)
            selected=[]
            for user in role.users.all():
                selected.append(user.id)

            logger.info('已选择：',selected)

            return{
                'code':0,
                'msg':'查询角色明细数据成功',
                'data':{
                    'name':role.name,
                    'description':role.description,
                    'all':all_users_data,
                    'selected':selected
                }
            }
        except:
            logger.error(traceback.format_exc())
            return{
                'code':4,
                'msg':'查询角色明细异常[%s]'%traceback.format_exc()
            }


    # @classmethod
    # def updateuser(**kws):
    #     '''
    #     角色添加用户
    #     '''
    #     try:
    #         role_id=kws['row_id']
    #         user_ids=kws['user_ids']
    #         role=Role.objects.get(id=role_id)
    #         role.user.clear()
    #         for user_id in user_ids.split(','):

    #             role.user.add(User.objects.get(id=user_id))##???????????????    

    #         return{
    #             'code':0,
    #             'msg':'关联用户成功'
    #         }

    #     except:
    #         return{
    #             'code':4,
    #             'msg':'关联用户异常'
    #         }

    # @classmethod
    # def deluser(**kws):
    #     try:
    #         role_id=kws['row_id']
    #         user_ids=kws['user_ids']
    #         role=Role.objects.get(id=role_id)
    #         for user_id in user_ids.split(','):
    #             role.user.remove(User.objects.get(id=user_id))             

    #         return{
    #             'code':0,
    #             'msg':'去除关联用户成功'
    #         }

    #     except:
    #         return{
    #             'code':4,
    #             'msg':'去除关联用户异常'
    #         }

            

class Grant(object):
    '''
    权限操作
    ''' 
    @classmethod
    def _isconfig():
        return 'NO'
    
    @classmethod
    def _add_ui_control_user(cls, ucid, userlist):
        try:
            for userstr in userlist:
                uir = User_UI_Relation()
                uir.kind = userstr.split('_')[0]
                uir.uc_id = ucid
                uir.user_id = userstr.split('_')[1]
                uir.save()
        
        except:
            print(traceback.format_exc())
            raise RuntimeError('ui权限关联用户异常.')
    
    @classmethod
    def _update_ui_control_user(cls, ucid, updateuserlist):
        try:
            has_user = dict()
            L = list(User_UI_Relation.objects.filter(uc_id=ucid))
            for u in L:
                has_user[u.id] = '%s_%s' % (u.kind, u.user_id)
            
            need_add = [x for x in updateuserlist if x not in list(has_user.values())]
            need_del = [x for x in list(has_user.values()) if x not in updateuserlist]
            
            for x in need_add:
                uir = User_UI_Relation()
                uir.uc_id = ucid
                uir.kind = x.split('=')[0]
                uir.user_id = x.split('=')[1]
                uir.save()
            
            for x in need_add:
                uir = User_UI_Relation.objects.get(kind=x.split('=')[0], user_id=x.split('=')[1])
        except:
            raise RuntimeError('更新视图控制用户信息异常')
    
    @classmethod
    def add_ui_control(cls, **config):
        try:
            uc = UIControl()
            uc.code = config['code']
            uc.description = config['description']
            uc.is_config = cls._isconfig()
            uc.author = config['creater']
            uc.save()
            cls._add_ui_control_user(uc.id, config['userstrs'].split(','))
            
            return {
                'code': 0,
                'msg': '新增权限[%s]成功' % uc.description
            }
        
        except:
            err = traceback.format_exc()
            print(err)
            return {
                'code': 4,
                'msg': '新增权限异常[%s]' % err
            }
    
    @classmethod
    def del_ui_control(cls, ucid):
        try:
            uc = UIControl.objects.get(code=ucid)
            dl = list(User_UI_Relation.objects.filter(ucid=uc.id))
            for x in dl:
                x.delete()
            
            uc.delete()
            return {
                'code': 0,
                'msg': '删除权限[%s]成功' % uc.description
            }
        
        except:
            err = traceback.format_exc()
            print(err)
            return {
                'code': 4,
                'msg': '删除权限异常[%s]' % err
            }
    
    @classmethod
    def edit_ui_control(cls, **config):
        try:
            uc = UIControl.objects.get(id=config['cid'])
            uc.code = config['code']
            uc.description = config['description']
            uc.is_config = cls._isconfig()
            uc.save()
            
            cls._update_ui_control_user(uc.id, config['userstrs'].split(','))
            return {
                'code': 0,
                'msg': '编辑权限[%s]成功' % uc.description
            }
        
        except:
            err = traceback.format_exc()
            print(err)
            return {
                'code': 4,
                'msg': '编辑权限异常[%s]' % err
            }
    
    @classmethod
    def query_ui_grant_table(cls, searchvalue=None):
        try:
            data = list()
            uicall = []
            if searchvalue:
                uicall = list(
                    UIControl.objects.filter(Q(code__icontains=searchvalue) | Q(description__icontains=searchvalue)))
            else:
                uicall = UIControl.objects.all()
            for x in uicall:
                datax = dict()
                datax['code'] = x.code
                datax['description'] = x.description
                datax['author'] = x.author
                
                userstr = []
                uirlist = list(User_UI_Relation.objects.filter(uc_id=x.id))
                for y in uirlist:
                    userstr.append('%s_%s' % (y.kind, y.user_id))
                
                datax['user'] = ','.join(userstr)
                datax['isconfig'] = cls._isconfig()
                data.append(datax)
            
            return {
                'code': 0,
                'msg': '',
                'data': data
            }
        except:
            return {
                'code': 4,
                'msg': 'UI权限表查询异常[%s]' % traceback.format_exc()
            }
