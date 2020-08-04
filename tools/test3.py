#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2020/7/20 9:39
# @Author  : Blackstone
# @to      :
import easyquotation
quotation = easyquotation.use('jsl') # ['jsl']
a=quotation.funda('sh161725') # 参数可选择利率、折价率、交易量、有无下折、是否永续来过滤
print(a)
b=quotation.fundb() # 参数如上
