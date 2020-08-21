# def test(datalist,to=None):
#     _run_map=dict()
#     _run_map[0]='上升趋势'
#     _run_map[1] = '下降趋势'
#     _run_map[2] = ''
#     _run_map[3] = ''
#     f1=True if datalist[-1]>datalist[0] else False
#     f2=True if len(datalist)==len([x for x in datalist if  datalist[0]<=x<=datalist[-1] ]) else False
#     f3=True if len(datalist)==len([x for x in datalist if datalist[0]>=x>=datalist[-1] ]) else False
#     if f1 and f2:
#         return _run_map.get(0)
#
#     if not f1 and f3 and to :
#         if datalist[0]-datalist[-1]<to:
#             return _run_map.get(1)
#
# xdata=[1,5,9,13,17,21]
# x2data=[12,9,6,3,1]
# print(test(x2data,15))

from concurrent.futures import  ThreadPoolExecutor,ProcessPoolExecutor,wait
from gevent.pool import Pool as  GeventPoolExecutor
import threading,gevent

class ExecutorProxy(object):
    _e=None
    _lock1, _lock2 = threading.RLock(), threading.RLock()

    @classmethod
    def get_instance(cls,type=0,max_workers=4):
        _executor_map = {
            0: ThreadPoolExecutor(max_workers=max_workers),
            1: ProcessPoolExecutor(max_workers=max_workers),
            3: GeventPoolExecutor(max_workers)
        }

        with cls._lock1:
            if cls._e is None:
                with cls._lock2:
                    cls._e = _executor_map.get(type,0)

        logger.info('[获取一个执行器]type={} id={}'.format(id(type,cls._e)))
        return cls._e

    @classmethod
    def wait_for_stop(cls,tasklist):
        if isinstance(cls._e,(ThreadPoolExecutor,ProcessPoolExecutor)):
            wait(tasklist)

        elif isinstance(cls._e,(GeventPoolExecutor,)):
            gevent.joinall(tasklist)







