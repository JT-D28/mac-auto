#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2020-06-10 16:38:29
# @Author  : Blackstone
# @descripttion:ME2专值测试
import traceback,copy,json
from manager.models import Step,SimpleTest,BusinessData
from login.models import User
from manager.context import Me2Log as logger

class TestMind(object):
    def _collect_params(self,nodeid):

        '''
        收集步骤节点下所有参数
        '''
        from manager.cm import getchild
        logger.info('==开始收集{}参数信息'.format(nodeid))
        try:
            pd={}
            step=Step.objects.get(id=nodeid.split('_')[1])
            bs=getchild('step_business',step.id)

            logger.info('bs:',bs)
            for b in bs:
                p=b.params
                if p.startswith('{'):
                    logger.info('dict类型：')
                    pkv=eval(p)
                    for k in pkv:
                        has=pd.get(k,None)
                        if not has:
                            pd[k]=pkv[k]
                        else:
                            if not has.__contains__('{{'):
                                pk[k]=pkv[k]

                else:
                    logger.info('urlencode类型：')
                    logger.info('p:',p)
                    if '=' in p:
                        for kv in p.split('&'):
                            logger.info('kv:',kv)
                            k=kv.split('=')[0]
                            v=kv.split('=')[1]
                            if not pd.get(k,None):
                                pd[k]=v
                            else:
                                if not v.__contains__('{{'):
                                    pd[k]=v
            return pd
        except:
            logger.error('获取{}下参数配置异常:{}'.format(nodeid,traceback.format_exc()))
            return {}




    def gen_simple_test_cases(self,nodeid):

        logger.info('开始生成simpletest 数据 nodeid={}'.format(nodeid))
        _tmpmeta=['重复','不存在','错误','null']
        paramdict=self._collect_params(nodeid)
        logger.info('paramdict:',paramdict)
        ##清除老数据
        sl=SimpleTest.objects.filter(step_id=nodeid.split('_')[1])
        logger.info('清除老simpletest数据{}条 filteid={}'.format(sl.count(),nodeid.split('_')[1]))
        sl.delete()

        ##重新生成
        for k,v in paramdict.items():
            for t in _tmpmeta:
                st=SimpleTest()
                st.tempname='{}值{}'.format(k,t)
                st.simplename=''
                st.paramname=k
                st.is_open=1
                st.is_repeat=1 if t is '重复' else 0
                st.step_id=nodeid.split('_')[1]
                st.value='null' if t is 'null' else ''
                st.db_check=''
                st.itf_check=''
                st.save()


    def get_visual_business(self,nodeid,callername):
        '''
        根据配置自动生成虚拟的待运行测试点
        '''
        ret=[]
        retd={}
        retd[nodeid]=None
        try:
            tmp=self._collect_params(nodeid)
            SimpleTests=SimpleTest.objects.filter(step_id=nodeid.split('_')[1],is_open=1)

            for c in SimpleTests:
                b=BusinessData()
                b.businessname='{}_{}'.format(c.tempname,c.simplename)
                b.description=''
                b.itf_check=c.itf_check
                b.db_check=c.db_check
                b.author=User.objects.get(name=callername)

                copytmp=copy.deepcopy(tmp)
                paramkey=c.paramname
                replacev=c.value
                for k in copytmp:
                    if k==paramkey:
                        copytmp[k]=c.value
                b.params=copytmp

                ret.append(b)
                if c.is_repeat==1:
                    ret.append(b)
            retd[nodeid]=ret
                
        except:
            print('生成待运行测试点异常:{}'.format(traceback.format_exc()))
        finally:
            return ret

    def query_simple_test(self,nodeid):
        ret=[]
        try:
            
            stepid=nodeid.split('_')[1]
            SL=SimpleTest.objects.filter(step_id=stepid)
            if not SL.exists():
                self.gen_simple_test_cases(nodeid)
                SL=SimpleTest.objects.filter(step_id=stepid)

            for s in SL:
                ret.append({
                    'id':s.id,
                    'step_id':s.step_id,
                    'paramname':s.paramname,
                    'tempname':s.tempname,
                    'is_repeat':s.is_repeat,
                    'is_open':s.is_open,
                    'simplename':s.simplename,
                    'value':s.value,
                    'db_check':s.db_check,
                    'itf_check':s.itf_check

                    })
            return {
                'code':0,
                'msg':'查询mock测试成功',
                'data':ret,
                'count':len(ret)
            }
        except:
            logger.error('查询mock测试异常：{}'.format(traceback.format_exc()))
            return{
                'code':4,
                'msg':'查询mock测试异常：{}'.format(traceback.format_exc()),

            }

    def update_simple_test(self,**kws):
        try:
            data=json.loads(kws['data'])
            uid=data['id']
            s=SimpleTest.objects.get(id=uid)
            # s.tempname=kws['tempname']
            s.db_check=data['db_check']
            s.itf_check=data['itf_check']
            s.value=data['value']
            s.save()
            return{
                'code':0,
                'msg':'修改成功.'
            }
        except:
            logger.error('修改异常:{}'.format(traceback.format_exc()))
            return{
                'code':4,
                'msg':'修改异常'
            }
    def open_simple_test(self,tid,is_open):
        try:
            s=SimpleTest.objects.get(id=tid)
            s.is_open=0 if is_open=='false' else 1
            s.save()
            return{
                'code':0
            }
        except:
            return{'code':4}

    def open_step_mock(self,tid,is_open):
        try:
            s=Step.objects.get(id=tid.split('_')[1])
            s.is_mock_open=1 if is_open=='true' else 0
            s.save()

            return{
                'code':0
            }
        except:
            return{
                'code':4
            }



