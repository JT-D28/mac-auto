from django.conf import  settings
import  redis

from manager.context import Me2Log as logger
class TreeUtil(object):
    key='treecache'
    pool = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)
    con = redis.Redis(connection_pool=pool)

    def get_tree_data_fast(self):

        cache=[eval(x) for x in self.con.lrange(self.key,0,-1)]
        if not cache:

            self.set_tree_data_cache()
            cache=[eval(x) for x in self.con.lrange(self.key,0,-1)]

        logger.info('拿到的数据结果:{}'.format(cache))
        return cache


    def set_tree_data_cache(self,force=True):
        '''
        :param force:
        :return:
        可能有坑
        '''
        from manager.cm import get_full_tree
        data=get_full_tree()
        for d in data:
            self.con.lpush(self.key,str(d))
        logger.info('缓存树信息成功....')

