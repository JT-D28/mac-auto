class A(object):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls,'_instance'):
            cls._instance=super(A,cls).__new__(cls)
        return cls._instance


class Aj(A):
    @classmethod
    def test(cls):
        print('aj')


a1=A()
a2=A()
print(id(a1)==id(a2))

aj1=Aj()
aj2=Aj()
print(id(aj1)==id(aj2))
