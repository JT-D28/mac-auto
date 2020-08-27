from django.conf import  settings
import  redis
from manager.models import  *
class TreeUtil(object):
    key='treecache'
    pool = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)
    con = redis.Redis(connection_pool=pool)
    @classmethod
    def get_tree_data_fast(cls):

        def _visible(x):
            if 'data' in x:
                x=x['data']
            # print('type:',x)
            type_=x['type'].capitalize()
            classname=type_
            if 'Business'==classname:
                classname='BusinessData'
            elif 'Root'==classname:
                return True
            # print('daf:',x['id'])
            id_=-1 if x['id']==-1 else x['id'].split('_')[1]
            try:
                e=eval('{}.objects.get(id={})'.format(classname,id_))
                # logger.info('节点可见性:',e.isdelete)
                return True if e.isdelete==0 else False
            except:
                print(traceback.format_exc())
                return True


        cache=[eval(x) for x in cls.con.lrange(cls.key,0,-1)]
        if not cache:

            cls.set_tree_data_cache()
            cache=[eval(x) for x in cls.con.lrange(cls.key,0,-1)]

        else:
            #可见性过滤
            cache=list(filter(_visible,cache))
            pass

        logger.info('拿到的数据结果:{}'.format(cache))
        return cache

    @classmethod
    def set_tree_data_cache(cls,force=True):
        '''
        :param force:
        :return:
        可能有坑
        '''
        from manager.cm import get_full_tree
        data=get_full_tree()
        for d in data:
            cls.con.rpush(cls.key,str(d))
        logger.info('缓存树信息成功....')
    @classmethod
    def update_tree_cache(cls,*args,**kws):
        action=kws['action']
        if action=='add':
            if len(cls.con.keys(cls.key))==0:
                cls.set_tree_data_cache()
            logger.info('缓存添加节点数据:',str(kws['data']))
            cls.con.rpush(cls.key,str(kws['data']))
        elif action=='del':
            cache=[eval(x) for x in cls.con.lrange(cls.key,0,-1)]
            for c in cache:
                if c['id']==kws['id']:
                    cache.remove(c)

        elif action=='edit':
            cache = [eval(x) for x in cls.con.lrange(cls.key, 0, -1)]
            for c in cache:
                if c['id'] == kws['id']:
                    c['name']=kws['name']
        logger.info('完成树缓存更新==')
        logger.info('action:{}'.format(action))

    @classmethod
    def clear_cache(cls):
        print('清除缓存树')
        cls.con.delete(cls.key)

