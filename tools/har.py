import json

def har_import(self,content_byte_list,callername)
    content = b''
    for byte in content_byte_list:
        content = content + byte

    if content.startswith(b'\xef\xbb\xbf'):
        content=content.replace(b'\xef\xbb\xbf', b'')
        entries=json.loads(content)['log']['entries']
        for e in entries:
            mimetype=e['request']['postData']['mimeType']
            if not mimetype:
                continue;

            url=e['request']['url']
            method=e['request']['method']
            headers=dict()
            for h in e['request']['headers']:
                headers[h['name']]=h['value']

            params=dict()
            for p in e['request']['postData'].get('params',[]):
                params[p['name']]=p['value']

            print('url：',url)
            print('mimeType:',mimetype)
            print('method:',method),
            print('headers:',headers),
            print('mineType:',mimetype)
            print('params:',params)
            print('\n')
            #开始创建实例类


 
