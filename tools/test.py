a="fda{{abc}}xxx"

import re
rs=re.findall('\{\{.*?\}\}', a)
print(len(rs))