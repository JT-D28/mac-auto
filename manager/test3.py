import re
a="{{lv_Signature${u,lv_key_8eb802e0fbb01e8bfa281628177aa2ae}}}"

def _replace_var(old,si=None,li=None):
    '''
    1.执行数据参数值
    2.DB检查数据
    3.接口检查数据
    4.数据字段
    '''
    # print('【变量转化】=>',old)
    varlist=re.findall('{[ru,].*?}', old)
    if len(varlist)>0:
        for x in varlist:
            varname=re.findall('{[ru],(.*?)}', x)
            # print(varname)
            print('x=>',x)
            if x.__contains__('lv_Signature') and si and li:
                print('1')
                old=old.replace(x,'{{%s_%s_%s_%s}}'%(str(varname[0]).split('$')[0],si,li,self.transform_id))
            else:
                old=old.replace(x,'{{%s_%s}}'%(varname[0],'qy'))

    return old

print(_replace_var(a,si=1,li=2))
