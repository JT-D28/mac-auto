a="{'fgMerchantName': '', 'tenantIds': '', 'pageNum': '1', 'pageSize': '10', 'sortName': '{u,lv_special_character}', 'sortType': 'desc'}"

import re
def _replace_var(old):
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
            print('x=>',x)
            varname=re.findall('{[ru],(.*?)}', x)
            print(varname)
            print(x)
            old=old.replace(x,'{{%s_%s}}'%(varname[0],'ak'))

    # print('转换后=>',old)
    return old

#print(a)
print(_replace_var(a))