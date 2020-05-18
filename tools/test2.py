import re
s1='{{u_lv_kkfdaf382lf209932}}/pafda/fldad.xml'
s2='新加用例_kkfdaf382lf209932'
print(re.sub('^_.*$', '', s1))
print(re.sub('_.*','',s2))