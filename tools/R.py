class R(object):

    '''
    文本替换类
    '''
    def __init__(self,startnode_id,old,expected,callername):
        self.startnode_id=startnode_id
        self.old=old
        self.expected=expected
        self.callername=callername

    def record(self,node_id,fields,old,expect):
        if isinstance(fields, (str,)):
            fields=[fields]

        for field in fields:
            r=Recover()
            r.field=field
            r.node_id=node_id
            r.old=self.old
            r.exp=self.expected
            r.creater=User.objects.get(name=self.callername)
            r.save()
        
        

    def replace(self):
        nodes=get_child_node()
        for node in nodes:
            ctype=node.split('_')[0]
            cid=node.split('_')[1]
            if 'business'==ctype:
                b=BusinessData.objects.get(id=cid)
                b.businessname=b.businessname.replace(self.old,self.expected)
                b.save()

                self.record(node, 'businessname', self.old, self.expect)
            elif 'step'==ctype:
                s=Step.objects.get(id=cid)
                s.url=s.url.replace(self.old,self.expected)
                s.description=s.description.replace(self.old,self.expected)
                s.save()
                self.record(node, ['url','description'], self.old, self.expect)

            elif 'case'==ctype:
                c=Case.objects.get(id=cid)
                c.description=c.description.replace(self.old,self.expected)
                c.save()
                self.record(node, 'description', self.old, self.expect)
            elif 'plan'==ctype:
                p=Plan.objects.get(id=cid)
                p.description=p.description.replace(self.old,self.expected)
                p.save()
                self.record(node, 'description', self.old, self.expect)
        

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
        from manager.models import *
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
            plan_os=order.objects.filter(kind='plan_case',main_id=node_uid)
            for pos in plan_os:
                chain.append('case_%s'%pos.follow_id)
                case_os=Order.objects.filter(kind='case_step',main_id=pos.follow_id)
                for cos in case_os:
                    chain.append('step_%s'%cos.follow_id)
                    step_os=Order.objects.filter(kind='step_business',main_id=cos.follow_id)
                    for sos in step_os:
                        chain.append('business_%s'%sos.follow_id)
        return chain


