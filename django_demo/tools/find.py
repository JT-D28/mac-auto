#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-11-06 17:25:05
# @Author  : Blackstone
# @to      :
import os

dz={}
def find(flag,target,dz=dz):
	
	for d in os.listdir(target):
		abspath=os.path.join(target,d)
		# print(abspath)
		if os.path.isdir(abspath):
			find(flag, abspath,dz)
		else:
			#print(abspath)
			with open(abspath,'rb') as f:
				try:
					content=f.readlines()
					for line in content:
						if flag in line:
							idx=content.index(line)
							content.remove(line)
							dz.get(abspath,[]).append(idx)
				except:
					pass
	return dz


print(find('sql', r'D:\Python36\lib\site-packages\django\db\backends'))