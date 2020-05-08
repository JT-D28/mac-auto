def a():
    try:
        return 1
    except:
        return 2
    finally:
        print(11111)


r=a()
print(r)