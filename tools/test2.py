class Order(object):
    def __init__(self,name,value):
        self.name=name
        self.value=value

    def __repr__(self):
        return'{}[{}]'.format(self.name,self.value)


L=[]
L.append(Order('a','1.10'))
L.append(Order('a','1.4'))
L.append(Order('a','1.14'))
L.append(Order('a','1.1'))
L.sort(key=lambda a:int(a.value.split('.')[1]))
print(L)