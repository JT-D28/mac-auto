import copy
from difflib import Differ
class O(object):

    A=2
    def __init__(self,a,b,c):
        self.a,self.b,self.c=a,b,c

def _diff_object(obj1,obj2):
    map_={}
    if obj1.__class__.__name__!=obj2.__class__.__name__:
        print(1)
        return map_

    attrs1,attrs2=dir(obj1),dir(obj2)
    if attrs1!=attrs2:
        print(2)
        return map_

    for attrname in [x for x in attrs1 if not x.startswith('__')]:
        v1=getattr(obj1,attrname)
        v2=getattr(obj2, attrname)
        if v1!=v2:
            al=map_.get(attrname,[])
            al.append(v1)
            al.append(v2)
            map_[attrname]=al

    return map_

def _udpate_object(target,diff):
    import difflib
    print('==调整对象{}属性值'.format(target))
    for atrrname in [x for x in dir(target) if not x.startswith('__')]:
        if atrrname in diff:
            oldvalue=getattr(target, attrname)
            if oldvalue==diff[atrrname][0]:
                setattr(target, attrname, diff[attrname][1])
                print('==属性{} {}->{}'.format(target,atrrname,diff[atrrname][0],diff[atrrname][1]))

            else:
                d=difflib.Differ()
                difflist=d.compare(diff[attrname][0], diff[attrname][1])
                setattr(target, attrname, _compute_attribute(difflist,getattr(target,atrrname)))
                ##target.save()

    target.save()


def _compute_attribute(diff,targetstr):
    count_,map_={},{}
    print('diff:{}'.format(diff))
    print('start:{}'.format(targetstr))
    ########
    for i in range(len(diff)):
        if diff[i].startswith('-') or diff[i].startswith('+'):
            bchar=_get_before_common_char(i,diff)
            print('bchar[{}]->{}, cur->{}:'.format(i,bchar,diff[i]))
            keycount= 0 if count_.get(bchar,None) is None else count_.get(bchar)+1
            mapvalue=map_.get('{}[{}]'.format(bchar,keycount),[])
            mapvalue.append(diff[i])
            map_['{}[{}]'.format(bchar,keycount)]=mapvalue
        else:
            curindex=0 if count_.get(diff[i].strip(),None) is None else count_.get(diff[i].strip())+1
            count_[diff[i].strip()]=curindex+1

    ######
    count_={}
    targetcopy=list(targetstr)
    for i in range(len(targetstr)):
        curindex=0 if count_.get(targetstr[i],None) is None else count_.get(targetstr[i])+1
        key='{}[{}]'.format(targetstr[i],curindex)
        operatelist=map_.get(key,None)
        if operatelist:
            for op in operatelist:
                if op.startswith('-'):
                    for j in range(i+1,len(targetstr)):
                        if targetstr[j]==op[-1]:
                            targetcopy.pop(j)

                elif op.startswith('+'):
                    for j in range(i+1,len(targetstr)):
                        if targetstr[j]==op[-1]:
                            targetcopy.insert(i+1, op[-1])
    return ''.join(targetcopy)

def _get_before_common_char(index,iter):
    n=iter[:index][::-1]
    for ch in n:
        if not ch.startswith('-') and not ch.startswith('+'):
            return ch 

    return None



o1=O(12,2,3)
o2=O(4,5,6)
diffmap=_diff_object(o1, o2)

_udpate_object(target, diffmap)


