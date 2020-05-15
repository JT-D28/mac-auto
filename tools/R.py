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

        

    def _replace_case(self,node):
        cid=node.split('_')[1]
        ccd=Case.objects.get(id=cid)
        ccd.description=self.replace_zz(self.old,self.expected,ccd.description)
        ccd.save()
        self.record(node, 'description', self.old, self.expected)

        oc=Order.objects.filter(kind='case_case',main_id=cid)
        for c in oc:
            cc=Case.objects.get(id=c.follow_id)
            cc.description=self.replace_zz(self.old,self.expected,cc.description)
            cc.save()
            nodeid='case_%s'%c.follow_id
            self.record(nodeid, 'description', self.old, self.expected)
            self._replace_case(nodeid)

        os=Order.objects.filter(kind='case_step',main_id=cid)
        for s in os:
            cs=Step.objects.get(id=s.follow_id)
            cs.url=self.replace_zz(self.old,self.expected,cs.url)
            cs.description=self.replace_zz(self.old,self.expected,cs.description)
            cs.save()
            self.record('step_%s'%cs.id, ['description','url'], self.old, self.expected)

            cod=Order.objects.filter(kind='step_business',main_id=cs.id)
            for co in cod:
                b=BusinessData.objects.get(id=co.follow_id)
                b.businessname=self.replace_zz(self.old,self.expected,b.businessnam)
                b.save()
                self.record('business_%s'%b.id, 'description', self.old, self.expected)


    def replace(self):

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
                    b.businessname=self.replace_zz(self.old,self.expected,b.businessname)
                    b.save()

                    self.record(node, 'businessname', self.old, self.expected)
                elif 'step'==ctype:
                    s=Step.objects.get(id=cid)
                    s.url=self.replace_zz(self.old,self.expected,s.url)
                    s.description=self.replace_zz(self.old,self.expected,s.description)
                    s.save()
                    self.record(node, ['url','description'], self.old, self.expected)

                elif 'case'==ctype:
                    self._replace_case(node)

                elif 'plan'==ctype:
                    p=Plan.objects.get(id=cid)
                    p.description=self.replace_zz(self.old,self.expected,p.description)
                    p.save()
                    self.record(node, 'description', self.old, self.expected)

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
            [chain.append('business_%s'%x.follow_id) for x.follow_id in os]
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


