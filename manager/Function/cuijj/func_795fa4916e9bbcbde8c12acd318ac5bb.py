def getMd5Sign(signStr):
    import hashlib
    signature = hashlib.md5(signStr.encode('utf-8')).hexdigest()
    return signature