import re
v=re.findall('def (.*?)\(.*?\)', 'def test(a)')[0]
print(v)