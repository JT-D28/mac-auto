a='def kk()'
b='def fa("11",2)'

import re
print(re.findall('\((.*?)\)', b))