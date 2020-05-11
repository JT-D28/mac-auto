from collections import OrderedDict
class Replace(object):
    '''
    计划:名称
    用例:名称
    步骤:描述 url 属性
    测试点:名称 参数信息
    '''
    _scope=OrderedDict()
    _scope['plan']=['description']
    _scope['case']=['description']
    _scope['step']=['description','url','property']
    _scope['business']=['businessname','params']

    @classmethod
    def _get_action_data(cls,scopename,count=1,scopeset=None):
        data=dict()
        if isinstance(scopeset,(list,)):
            for scope in scopeset:
                scopename=scope.split('_')[0]
                scopevalue=scope.split('_')[1]
                x=data.get(scopename,[])
                if scopevalue in cls._scope[scopename]:
                    x.append(scopevalue)
                    data[scopename]=x
        else:
            begin_add=False
            level_count=0
            for x in cls._scope:
                level_count+=1

                if level_count>count:
                    break;

                if scopename==x:
                    begin_add=True

                if begin_add:
                    data[x]=cls._scope[x]

        return data

    @classmethod
    def replace(cls,startnodeid,old,expect,cout=1,scopeset=None):
        '''
        节点文本替换
        可以指定节点替换深度
        可以指定节点替换的替换作用域
        '''
        scope_name=startnodeid.split('_')[0]
        node_id=startnodeid.split('_')[1]

        for k,v in cls._get_action_data(scope_name,count=count,scopeset=scopeset):
            k=k[0].upper()+k[1:]
            if k=='Business':
                k='BusinessData'

            callstr='%s.objects.get(id=%d).%s'
            txt=eval(callstr)
            txt=txt.replace(old,expect)


        return {
            'code':0,
            'msg':'替换成功..'
        }




