import gc
import sys
gc.set_debug(gc.DEBUG_LEAK)
a=[]
b=[]
a.append(b)
b.append(a)
print('a refcount:',sys.getrefcount(a))
print('b refcount:',sys.getrefcount(b))

del a
del b
print(gc.collect())