
from rpc4django import rpcmethod



@rpcmethod(name='function.add', signature=['int', 'int', 'int'])
def add(a, b):
    return a+b



@rpcmethod(name='function.execute', signature=['str','str','str'])
def execute(name,params,taskid):
    from manager.StartPlan import executeFunction
    return executeFunction(name,params,taskid)