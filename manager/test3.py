import base64

str_="eyJTdGF0dXMiOiItMSIsIlJldHVybk1zZyI6IuacquefpemUmeivryJ9"
print(base64.b64decode(str_).decode(encoding='utf-8'))