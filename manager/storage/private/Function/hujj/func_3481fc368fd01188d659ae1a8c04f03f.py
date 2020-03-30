def handle_params(params):
    from hashlib import md5
    print('$'*200)
    print('handle_params参数=>',params)
    keys=list(params.keys())
    keystr_='_'.join(keys)
    return md5(keystr_.encode('utf-8')).hexdigest()