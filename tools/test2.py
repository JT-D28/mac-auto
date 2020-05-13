def get_node_id_chain(node_id,**filter):
    '''
    '''
    from manager.models import *
    chain=[node_id]
    node_type=node_id.split('_')[0]
    node_uid=node_id.split('_')[1]    

    if 'business'==node_type:
        pass
    elif 'step'==node_type:
        os=Order.objects.filter(kind='step_business',main_id=node_uid)
        [chain.append('business_%s'%x.follow_id) for x.follow_id in os]
    elif 'case'==node_type:
        case_os=Order.objects.filter(kind='case_step',main_id=node_uid)

        for cos in case_os:
            chain.append('step_%s'%cos.follow_id)
            step_os=Order.objects.filter(kind='step_business',main_id=cos.follow_id)
            for sos in step_os:
                chain.append('business_%s'%sos.follow_id)
        #
        case_os_0=Order.objects.filter(kind='case_case',main_id=node_uid)
        if case_os_0.exists():
            for cos in case_os_0:
                

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


def replace(chain,old,expect,**filter):
    f=filter.get('fields',[])
    all_types=set([x.split('_')[0] for x in chain ])

    for c in chain:
        cid=c.split('_')[1]
        for p in f:
            ctype=p.split('_')[0]
            cfield=p.split('_')[1]
            if ctype not in all_types:
                continue;





def _description(node_id):
    '''
    树节点字段解析
    '''
    node_type=node_id.split('_')[0]
    node_uid=node_id.split('_')[1]

    if 'business'==node_type:
        b=BusinessData.objects.get(id=node_uid)
        return '[id=,t=business,businessname=%s]'%b.businessname
    elif 'step'==node_type:
        s=Step.objects.get(id=node_uid)
        return '[t=step,description=%s,url=%s]'%(s.description,s.url)

    elif 'case'==node_type:
        c=Case.objects.get(id=node_uid)
        return '[t=case,description=%s]'%c.description
    elif 'plan'==node_type:
        p=Plan.objects.get(id=node_uid)
        return '[t=plan,description=%s]'%p.description