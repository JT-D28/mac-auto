from manager.context import Me2Log as logger
import traceback
from manager.models import *
import time
from manager.core import EncryptUtils
class R(object):

    '''
    文本替换类
    '''
    def __init__(self,callername,startnode_id=None,old=None,expected=None):
        self.startnode_id=startnode_id
        self.old=old
        self.expected=expected
        self.callername=callername
        self.batchid=EncryptUtils.md5_encrypt(str(time.time()))

    def record(self,node_id,fields,old,expect):
        if isinstance(fields, (str,)):
            fields=[fields]

        for field in fields:
            r=Recover()
            r.batchid=self.batchid
            r.field=field
            r.nodeid=node_id
            r.old=self.old
            r.exp=self.expected
            r.creater=User.objects.get(name=self.callername)
            r.save()
        
    
    def recover(self,recover_node_id):
        '''
        节点文本替换恢复
        '''
        try:
            his=Recover.objects.filter(nodeid=recover_node_id,creater=User.objects.get(name=self.callername)).order_by('-createtime')
            if his.exists():
                last=his[0].batchid

                list_all=Recover.objects.filter(batchid=last)
                for bb in list_all:
                    node_type=bb.nodeid.split('_')[0]
                    node_tid=bb.nodeid.split('_')[1]

                    if 'business'==node_type:
                        b=BusinessData.objects.get(id=node_tid)
                        b.businessname=b.businessname.replace(bb.exp,bb.old)
                        b.save()
                    elif 'step'==node_type:
                        s=Step.objects.get(id=node_tid)
                        s.url=s.url.replace(bb.exp,bb.old)
                        s.description=s.description.replace(bb.exp,bb.old)
                        s.temp=s.temp.replace(bb.exp,bb.old)
                        s.headers=s.headers.replace(bb.exp,bb.old)
                        
                        s.save()
                    elif 'case'==node_type:
                        c=Case.objects.get(id=node_tid)
                        c.description=c.description.replace(bb.exp,bb.old)
                        c.save()

                    elif 'plan'==node_type:
                        p=Plan.objects.get(id=node_tid)
                        p.description=p.description.replace(bb.exp, bb.old)
                        p.save()
                return{
                    'status':'success',
                    'msg':'回退成功'
                }
            else:
                return{
                    'status':'success',
                    'msg':'回退失败 没找到替换历史'
                }
        except:
            logger.error('回退异常',traceback.format_exc())
            return{
                'status':'error',
                'msg':'回退异常'
            }

    @classmethod
    def replace_zz(cls,exp,new,s):
        return re.sub(exp,new,s)

    def _replace_case(self,node,scope):

        cid=node.split('_')[1]
        ccd=Case.objects.get(id=cid)
        if scope.get('check_case')=='true':
            ccd.description=self.replace_zz(self.old,self.expected,ccd.description)
            self.record(node, 'description', self.old, self.expected)

        ccd.save()
        
        oc=Order.objects.filter(kind='case_case',main_id=cid)
        for c in oc:
            cc=Case.objects.get(id=c.follow_id)
            if scope.get('check_case')=='true':
                cc.description=self.replace_zz(self.old,self.expected,cc.description)
                self.record('case_%s'%cc.id, 'description', self.old, self.expected)
            cc.save()
            nodeid='case_%s'%c.follow_id
            
            self._replace_case(nodeid,scope)

        os=Order.objects.filter(kind='case_step',main_id=cid)
        for s in os:
            cs=Step.objects.get(id=s.follow_id)
            if scope.get('check_url')=='true':
                cs.url=self.replace_zz(self.old,self.expected,cs.url)
                self.record('step_%s'%cs.id,'url', self.old, self.expected)
            if scope.get('check_step')=='true':
                cs.description=self.replace_zz(self.old,self.expected,cs.description)
                self.record('step_%s'%cs.id,'description', self.old, self.expected)
            cs.save()
            
            cod=Order.objects.filter(kind='step_business',main_id=cs.id)
            for co in cod:
                b=BusinessData.objects.get(id=co.follow_id)
                if scope.get('check_business')=='true':
                    b.businessname=self.replace_zz(self.old,self.expected,b.businessname)
                    self.record('business_%s'%b.id, 'businessname', self.old, self.expected)
                b.save()
                
    def replace(self,scope=None):

        try:
       
            if not self.old:
                return{
                    'status':'success',
                    'msg':'待替换字符串不能为空'
                }
            nodes=self.get_child_node()
            for node in nodes:
                ctype=node.split('_')[0]
                cid=node.split('_')[1]
                if 'business'==ctype:
                    b=BusinessData.objects.get(id=cid)
                    if scope.get('check_business',False):
                        b.businessname=self.replace_zz(self.old,self.expected,b.businessname)
                        self.record(node, 'businessname', self.old, self.expected)
                    b.save()

                elif 'step'==ctype:
                    logger.warn('步骤名称:',scope.get('check_step'))
                    s=Step.objects.get(id=cid)
 
                    if scope.get('check_step')=='true':
                        s.description=self.replace_zz(self.old,self.expected,s.description)
                        self.record(node,'description', self.old, self.expected)
                    if scope.get('check_url')=='true':
                        s.url=self.replace_zz(self.old,self.expected, s.url)
                        self.record(node, 'url', self.old, self.expected)
                    if scope.get('check_property')=='true':
                        s.temp=self.replace_zz(self.old,self.expected, s.temp)
                        self.record(node, 'property', self.old, self.expected)
                    if scope.get('check_header')=='true':
                        s.headers=self.replace_zz(self.old, self.expected, s.headers)
                        self.record(node, 'header', self.old, self.expected)

                    s.save()
                    

                elif 'case'==ctype:
                    
                    self._replace_case(node,scope)


                elif 'plan'==ctype:
                    p=Plan.objects.get(id=cid)
                    if scope.get('check_plan')=='true':
                        p.description=self.replace_zz(self.old,self.expected,p.description)
                        self.record(node, 'description', self.old, self.expected)
                    p.save()
                    

            return {
                'status':'success',
                'msg':'文本[%s]已替换为[%s]'%(self.old,self.expected)
            }
        except:
            logger.error('文本[%s]替换为[%s]异常:',traceback.format_exc())

            return{
            'status':'error',
            'msg':'文本[%s]替换为[%s]异常'%(self.old,self.expected)
        }


    def _handle_case_node(self,node_uid,chain):
        case_os=Order.objects.filter(kind='case_step',main_id=node_uid)
        if case_os.exists():
            for cos in case_os:
                chain.append('step_%s'%cos.follow_id)
                step_os=Order.objects.filter(kind='step_business',main_id=cos.follow_id)
                for sos in step_os:
                    chain.append('business_%s'%sos.follow_id)
        #
        case_os_0=Order.objects.filter(kind='case_case',main_id=node_uid)
        if case_os_0.exists():
            for cos in case_os_0:
                self._handle_case_node(cos.follow_id, chain)


    def get_child_node(self,**filter):
        '''
        获取开始节点所有子节点
        '''
        node_id=self.startnode_id
        chain=[node_id]
        node_type=node_id.split('_')[0]
        node_uid=node_id.split('_')[1]    

        if 'business'==node_type:
            pass
        elif 'step'==node_type:
            os=Order.objects.filter(kind='step_business',main_id=node_uid)
            [chain.append('business_%s'%x.follow_id) for x in os]
        elif 'case'==node_type:
            self._handle_case_node(node_uid, chain)
        elif 'plan'==node_type:
            plan_os=Order.objects.filter(kind='plan_case',main_id=node_uid)
            for pos in plan_os:
                chain.append('case_%s'%pos.follow_id)
                case_os=Order.objects.filter(kind='case_step',main_id=pos.follow_id)
                for cos in case_os:
                    chain.append('step_%s'%cos.follow_id)
                    step_os=Order.objects.filter(kind='step_business',main_id=cos.follow_id)
                    for sos in step_os:
                        chain.append('business_%s'%sos.follow_id)
        return chain


