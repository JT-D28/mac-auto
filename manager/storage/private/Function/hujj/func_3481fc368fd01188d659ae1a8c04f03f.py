def handle_params(params):
    from hashlib import md5
    values=[str(_) for _ in list(params.values())]
    valuestr_='_'.join(values)
    return md5(valuestr_.encode('utf-8')).hexdigest()