def testwaibu(a,**kws):
    print(a)
    print(kws['callername'])


def a(**kws):
    print(kws)
a(a=1)


