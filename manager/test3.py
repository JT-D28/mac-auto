m={'1.10':"1",'1.2':'2'}
akeys=([int(k.replace('1.','')) for k in m.keys()])
print(akeys)
bkeys=sorted(akeys)
print(bkeys)
ckeys=['1.'+str(k) for k in bkeys]
print(ckeys)





