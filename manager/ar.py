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
            userids=[idx for idx in kws['userids'].split(',') if idx.strip()]
            for idx in userids:
                role.users.add(User.objects.get(id=idx))

            role.save()
            return{
                'code':0,
                'msg':'更新角色成功'
            }

        except:
            logger.error('更新角色异常:',traceback.format_exc())
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
            
class Grant(object):
    '''
    权限操作
    ''' 
    @classmethod
    def _isconfig(cls):
        return False
    
    @classmethod
    def _add_ui_control_user(cls, ucid, userlist,user):
        try:
            for userstr in userlist:
                uir = User_UIControl()
                uir.kind = userstr.split('_')[0]
                uir.uc_id = ucid
                uir.user_id = userstr.split('_')[1]
                uir.author=user
                uir.save()
        
        except:
            print(traceback.format_exc())
            raise RuntimeError('ui权限关联用户异常.')
    
    @classmethod
    def _update_ui_control_user(cls, ucid, updateuserlist):
        try:
            has_user = dict()
            L = list(User_UIControl.objects.filter(uc_id=ucid))
            for u in L:
                has_user[u.id] = '%s_%s' % (u.kind, u.user_id)
            
            need_add = [x for x in updateuserlist if x not in list(has_user.values()) and x.strip()]
            need_del = [x for x in list(has_user.values()) if x not in updateuserlist]
            
            for x in need_add:
                uir = User_UIControl()
                uir.uc_id = ucid
                uir.kind = x.split('_')[0]
                uir.user_id = x.split('_')[1]
                uir.save()
            
            for x in need_add:
                uir = User_UIControl.objects.get(kind=x.split('_')[0], user_id=x.split('_')[1])
        except:
            raise RuntimeError('更新视图控制用户信息异常')
    
    @classmethod
    def query_one_ui_control(cls,uid):
        try:
            u=UIControl.objects.get(id=uid)
            selected_user_data=[]
            all_user_data=cls.queryalluicontrolusers()['data'][0]
            for ak in list(User_UIControl.objects.filter(uc_id=uid)):
                name=User.objects.get(id=ak.user_id).name if ak.kind=='USER' else Role.objects.get(id=ak.user_id).name
                selected_user_data.append(
                    '%s_%s'%(ak.kind,ak.user_id))

            return{
                'code':0,
                'msg':'',
                'data':{
                    'code':u.code,
                    'description':u.description,
                    'isvalid':u.is_valid,
                    'isopen':u.is_open,
                    'all':all_user_data,
                    'selected':selected_user_data

                }

            }



        except:
            logger.error('ui控制查询用户异常',traceback.format_exc())
            return{
                'code':4,
                'msg':'ui控制查询用户异常'
            }


    @classmethod
    def add_ui_control(cls, **config):
        try:
            uc = UIControl()
            uc.code = config['code']
            uc.description = config['description']
            uc.is_config = cls._isconfig()
            uc.is_valid=config['isvalid']
            uc.author = config['user']
            uc.save()
            cls._add_ui_control_user(uc.id, [x for x in config['userstrs'].split(',') if x.strip()],uc.author)
            
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
    def del_ui_control(cls, **kws):
        try:
            ucid=kws['ucids']
            ids=[x for x in ucid.split(',') if x.strip()]
            for idx in ids:
                uc = UIControl.objects.get(id=idx)
                dl = list(User_UIControl.objects.filter(id=uc.id))
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
            uc.is_valid=config['isvalid']
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
                datax['id']=x.id
                datax['code'] = x.code
                datax['description'] = x.description
                datax['authorname'] = x.author.name
                datax['isopen']=x.is_open
                datax['isvalid']=x.is_valid
                datax['isconfig'] = cls._isconfig()
                data.append(datax)
            
            return {
                'code': 0,
                'msg': '',
                'data': data
            }
        except:
            logger.error('获取权限表查询异常:',traceback.format_exc())
            return {
                'code': 4,
                'msg': 'UI权限表查询异常[%s]' % traceback.format_exc()
            }
    @classmethod
    def queryalluicontrolusers(cls):
        '''
        返回新增可用用户列表

        '''
        res=list()
        users=User.objects.all()
        roles=Role.objects.all()
        for user in  users:
            res.append({
                'id':'_'.join(['USER',str(user.id)]),
                'name':user.name
                })

        for role in roles:
            res.append({
                'id':'_'.join(['ROLE',str(role.id)]),
                'name':role.name
                })

        return {
            'code':0,
            'msg':'',
            'data':[res,[]]
        }

    @classmethod
    def updateuicontrolstatus(cls,**kws):
        try:
            u=UIControl.objects.get(id=kws['uid'])
            u.is_open=kws['isopen']
            u.save()

            return{
                'code':0,
                'msg':'操作成功.'
            }
        except:
            return{
             'code':4,
             'msg':'操作异常'
            }