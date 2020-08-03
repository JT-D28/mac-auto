#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2020/7/27 9:11
# @Author  : Blackstone
# @to      :
#
from mt.common.decorater import  decorater
import time
class A(object):
    @decorater.cached(10)
    def test(self):
        return 2

a=A()
a.test()