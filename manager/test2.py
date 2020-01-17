from collections import OrderedDict
from urllib3 import encode_multipart_formdata
import requests

def test():
    files = OrderedDict([("upload", (None, open("test.txt", 'rb').read(), 'application/octet-stream'))])
    boundary='----WebKitFormBoundaryKPjN0GYtWEjAni5F'
    m = encode_multipart_formdata(files, boundary=boundary)
    print("0", m[0])
    params = {'path': 'test.txt',
              'token': '123456',
              'num': 0,
              'offset': 0,
              'limit': 8}
    response = requests.post('http://httpbin.org/post',
                              params=params,
                              data=m[0],
                              headers={'Content-Type': "multipart/form-data; "+boundary})

    print("1: ", response.text)
    print("2: ", response.request.body)
    print("3: ", response.request.headers)

if __name__ == '__main__':
    test()