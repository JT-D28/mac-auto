def encodeBase64String(str):
    import base64
    str=str.encode('utf-8')
    bs64=base64.b64encode(str)
    return bs64