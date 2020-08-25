import json
from django.db.models import Model,CharField

class AFC():
    f1=1

class MyEncoder(json.JSONEncoder):
    def __init__(self):
        pass

    def encode(self, o):
        e=super(MyEncoder,self).encode()

        return e

class AS(MyEncoder):
    def __init__(self,*attr,**kws):
        super(AS,self).__init__()


afc=AFC()
print(json.dumps(afc,cls=None))