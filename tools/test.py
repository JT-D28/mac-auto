import  time
from types import MethodType,FunctionType
from functools import  update_wrapper
class _Save(object):
    def get(self,key):
        return {}



cache_={}
def cached(func):

    def _wrap(*args,**kws):
        res=func(*args,**kws)
        a=cache_.get(args[1],{})
        a['last']=str(time.time())

        return res

    return update_wrapper(_wrap, func)


class Query(object):
    @cached
    def _query_info(self,sql):
        time.sleep(2)
        return 'res:122'


Query()._query_info('selcet ')
