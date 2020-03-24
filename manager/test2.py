import re
from hashlib import md5, sha512


def _md5(s):
	"""
	函数文件名标识
	"""
	new_md5 = md5()
	new_md5.update(s.encode(encoding='utf-8'))
	return new_md5.hexdigest()


def tzm_compute(src, pattern):
	"""
	计算方法特征码
	通过pattern从src字符串获取方法名和参数串计算特征码
	"""
	pool = [chr(x) for x in range(97, 123)]
	m = re.findall(pattern, src)
	funcname = m[0][0]
	paramlist = m[0][1].split(",")
	
	# 带关键字参数和可变参数的 都按a()计算
	# 参数带=好 记为关键参数 去除
	paramlist = [p for p in paramlist if not p.startswith('*') and not p.__contains__('=')]
	size = len(paramlist)
	paramstr = ",".join(pool[0:size])
	final = "%s(%s)" % (funcname, paramstr)
	print('final=>', final)
	
	return _md5(final)


def createSignature(key, **kws):
	from hashlib import sha512
	keys = list(kws.keys())
	keys.sort()
	# print(keys)
	valstr = ""
	for k in keys:
		if kws[k] != None:
			valstr += str(kws[k]) + '_'
	valstr += key
	hash = sha512()
	hash.update(valstr.encode('utf-8'))
	Signature = hash.hexdigest().upper()
	return Signature


print(createSignature('wwww', AppVersion='1.11.0', UserInfoURID='', EnterpriseNum='AC530001', PhoneNum='',
                      OrganizationID='0103', IdentityType=1, IdentityID='2018092901'))
