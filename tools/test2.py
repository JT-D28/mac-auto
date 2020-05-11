def p():
    def _wrap(*args,**kws):
        print(args)
        print(kws)
    return _wrap

class A(object):
    @p
    AGE='1234'

    def t(self):
        print('ttttttt')



A().t()