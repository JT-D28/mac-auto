def base64_encrypt(str_):
    import base64
    return base64.b64encode(str(str_).encode('utf-8')).decode()