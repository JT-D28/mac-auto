def base64_encrypt(**mw):
    import base64
    return base64.b64encode(str(mw['mw']).encode('utf-8')).decode()