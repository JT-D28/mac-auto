#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2020-02-17 09:51:22
# @Author  : Blackstone
# @to      :权限管理

import os, traceback
from login.models import *
from manager.models import *
from login.models import *
from django.db.models import Q
from manager.context import Me2Log as logger,get_temp_dir,monitor

class RoleData():
    '''
    角色操作
    '''


    @classmethod
    @monitor(action='查询角色详情')
    def queryroletable(cls,**kws):
        searchvalue=kws.get('searchvalue','')
        data=[]
        data0=Role.objects.filter(Q(name__icontains=searchvalue)|Q(description__icontains=searchvalue))
        for x in data0:
            data.append({
                'id':x.id,
                'name':x.name,
                'description':x.description,
                'createtime':x.createtime,
                'authorname':x.author.name

                })
        try:
            return{
                'code':0,
                'msg':'获得权限表',
                'data':data,
                'count':len(data)
            }
        except:
            return{
                'code':4,
                'msg':'获得权限异常',
                'data':[]
            }
    

    @classmethod
    @monitor(action='添加角色')
    def addrole(cls,**kws):
        try:
            role=Role()
            logger.error(kws)
            role.name=kws['name']
            role.description=kws['description']
            role.author=kws['user']
            role.save()
            userids=kws['userids'].split(',')
            if(userids):
                for idk in userids:
                    if idk:
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
    @monitor(action='删除角色',authorname='$Role.objects.filter(id__in=[ids]).author.name')
    def delrole(cls,**kws):
        try:
            role_ids=kws['ids']
            for roleid in role_ids.split(','):
                if roleid:
                    Role.objects.get(id=roleid).delete()
                    
            return{
                'code':0,
                'msg':'删除角色成功'
            }
        except:
            logger.error('删除角色异常：',traceback.format_exc())
            return{
             'code':4,
             'msg':'删除角色异常'
            }

    @classmethod
    @monitor(action='更新角色',description='$Role.objects.get(id=[uid])',authorname='$Role.objects.get(id=[uid]).author.name')
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
    @monitor(action='查询角色详情')
    def queryonerole(cls,**kws):
        try:
            role_id=kws['uid']
            role=Role.objects.get(id=role_id)
            all_users=User.objects.values('id','name')
            all_users_data=[ {'id':y['id'],'name':y['name']}for y in all_users]

            logger.info(all_users_data)
            selected=[]
            for user in role.users.values('id'):
                selected.append(user['id'])

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



    @classmethod
    def queryuserrole(cls,userid):
        '''查询用户角色ID
        '''
        for r in Role.objects.all():
            u=User.objects.get(id=userid)
            if u in r.users.all():
                return r.id
            

class Grant(object):
    '''
    权限操作
    ''' 
    @classmethod
    def isconfig(cls,code):
        scandirs=get_temp_dir()
        for path in scandirs:
            for filename in os.listdir(path):
                if filename.split('.')[1]=='html':
                    with open(os.path.join(path,filename),encoding='utf-8') as f:
                        if '{{%s}}'%code in f.read():
                            return True
            
        return False

    @classmethod
    def is_ui_display(cls,code,username):
        '''
        UI组件显示控制
        '''

        logger.info('-'*50,'==开始[%s]用户权限过滤..'%code)
        uc=UIControl.objects.filter(code=code)
        isopen=0
        if uc.exists():
            isopen=uc[0].is_open
            logger.info('组件ID:',uc[0].id)
        else:
            logger.info('组件[%s]没配置 放行'%code)
            return '!important'

        user=User.objects.get(name=username)
        user_id=user.id
        user_role_ids=[]

        for r in Role.objects.all():
            if user in r.users.all():
                user_role_ids.append(r.id)

        logger.info('用户[%s]ID[%s]'%(username,User.objects.get(name=username).id))
        logger.info('用户[%s]角色ID:%s'%(username,user_role_ids))
        f1=User_UIControl.objects.filter(user_id=user_id,kind='USER',uc_id=uc[0].id)
        if f1.exists() and isopen:
            logger.info('用户[%s]看不到UI组件[%s]'%(username,uc[0].description))
            return 'none!important'

        for idx in user_role_ids:
            f2=User_UIControl.objects.filter(user_id=idx,kind='ROLE',uc_id=uc[0].id)

            if f2.exists() and isopen:
                logger.info('角色%s[%s]看不到UI组件%s[%s]'%(Role.objects.get(id=idx).name,idx,uc[0].description,uc[0].id))
                return 'none!important'
        #logger.info('用户[%s]能看到UI组件[%s]'%(username,uc[0].description))
        return '!important'
    
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
    #@monitor(action='查询权限详情')
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
    @monitor(action='添加权限')
    def add_ui_control(cls, **config):
        try:
            uc = UIControl()
            uc.code = config['code']
            uc.description = config['description']
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
    @monitor(action='删除权限')
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
    @monitor(action='编辑权限')
    def edit_ui_control(cls, **config):
        try:
            uc = UIControl.objects.get(id=config['cid'])
            uc.code = config['code']
            uc.description = config['description']
           
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
    @monitor(action='查询权限列表')
    def query_ui_grant_table(cls, **kws):

        searchvalue=kws.get('searchvalue','')
        try:
            data = list()
            uicall = []
            if searchvalue:
                uicall = list(
                    UIControl.objects.filter(Q(code__icontains=searchvalue) | Q(description__icontains=searchvalue)))
            else:
                uicall = UIControl.objects.values('id','code','author','description','isopen')
            for x in uicall:
                datax = dict()
                datax['id']=x.id
                datax['code'] = x.code
                datax['description'] = x.description
                datax['authorname'] = x.author.name
                datax['isopen']=x.is_open
                datax['isconfig'] = cls.isconfig(x.code)
                data.append(datax)
            
            return {
                'code': 0,
                'msg': '',
                'data': data,
                'count':len(data)
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
        users=User.objects.values('id','name')
        roles=Role.objects.values('id','name')
        for user in  users:
            res.append({
                'id':'_'.join(['USER',str(user['id'])]),
                'name':user['name']
                })

        for role in roles:
            res.append({
                'id':'_'.join(['ROLE',str(role['id'])]),
                'name':role['name']
                })

        return {
            'code':0,
            'msg':'',
            'data':[res,[]]
        }

    @classmethod
    #@monitor(action='开关权限')
    def updateuicontrolstatus(cls,**kws):
        try:
            u=UIControl.objects.get(id=kws['uid'])
            openstatus=kws['isopen']
            if int(openstatus)==1:
                if not cls.isconfig(u.code):
                    return{
                        'code':2,
                        'msg':"代码有埋点么"
                    }
            
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