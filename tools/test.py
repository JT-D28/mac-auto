def geta(urid,data,**kws):
    from manager.builtin import cout
    res=''
    cout('开始计算字段LunaCheckedParamHashFieldName ',**kws)
    data=data.replace('true','True').replace('false',"False").replace('null','None')
    rows=eval(data)['rows']
    for r in rows:
        if urid==r['urid']:
            res=r['LunaCheckedParamHashFieldName']
            cout('结果{}'.format(res),**kws)
            return res


   
    return '函数没查到'