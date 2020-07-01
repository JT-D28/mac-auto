from functools import update_wrapper
class ValidChecker(object):
    '''
    有效性校验工具  控制台输出提示

    '''
    _builtin_type=(str,list,tuple,dict,int,float)
    
    def __init__(self):
        pass


    def custom_method_check(self,f):
        '''
        自定义函数有效性校验
        '''
        def _wrap(*args,**kws):
            return f(*args,**kws)
        return update_wrapper(_wrap, f)


    def params_check(self,f):
        '''
        参数值有效性校验 简化参数嵌套
        '''
        def _wrap(*args,**kws):
            print('*************************8888')
            for p in args:
                if not isinstance(p, (str,list,tuple,dict,int,float)):
                    cout('函数{}调用参数{}类型python无法识别请检查'.format(f,p),**kws)

            return f(*args,**kws)
        return update_wrapper(_wrap, f)


v=ValidChecker()

@v.custom_method_check
@v.params_check
def test(a,b,*args,**kws):
    
    return 'test value'

kws={'ykkk':1}

callstr='''test(1,'\"hfhda\"',4,5,**kws)'''
print(eval(callstr))