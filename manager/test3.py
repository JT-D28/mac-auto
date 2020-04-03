import base64,re

s="$[aaak(11)]"
print(len(re.findall('\$\[(.*?)\((.*?)\)\]', s)))