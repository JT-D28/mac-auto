import re
m='[uid]'
key=re.findall('\[(.*?)\]', m)
print(key)