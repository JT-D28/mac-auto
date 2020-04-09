def base64_encrypt(str_,**kws):
    import base64

    str_=str_['mw']
    str_=str_.replace('\n','').replace(' ','').replace("'", '"')
    return base64.b64encode(str_.encode()).decode()