#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-11-01 16:38:29
# @Author  : Blackstone
# @to      :
import threading


def mock():
	with open('mock.log', 'w+') as f:
		while True:
			f.write('aa')


threading.Thread(target=mock).start()
