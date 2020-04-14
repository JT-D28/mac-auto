#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2020-03 09:42:34
# @Author  : Blackstone
# @to      :空间管理

import os, traceback, subprocess
from .pa import MessageParser
from ftplib import FTP
from ME2.settings import logme

class SpaceMeta(object):
	
	@classmethod
	def local_to_ftp(cls, filename, ip, port, username, password, remotedir, callername):
		try:
			ftp = FTP()
			ftp.set_debuglevel(0)
			ftp.connect(ip, int(port))
			ftp.login(username, password)
			bufsize = 1024
			localfile = os.path.join(os.path.dirname(__file__), 'storage', 'private', 'File', callername, filename)
			if not os.path.exists(localfile):
				return ('error', '本地文件[%s]不存在 请先上传' % localfile)
			fp = open(localfile, 'rb')
			remotepath = os.path.join(remotedir, filename)
			ftp.storbinary('STOR ' + remotepath, fp, bufsize)
			fp.close()
			ftp.quit()
			
			return ('success', '本地文件[%s] 上传ftp[%s]成功. ' % (filename, ','.join((ip, str(port), remotepath))))
		except:
			return ('error', 'ftp上传异常[%s]' % traceback.format_exc())
	
	@classmethod
	def ftp_to_local(cls, ip, port, username, password, remotefile, callername):
		try:
			ftp = FTP()
			ftp.set_debuglevel(0)
			ftp.connect(ip, int(port))
			ftp.login(username, password)
			bufsize = 1024
			# remotefilename=os.sep.split(remotefile)[-1]
			remotefilename = remotefile.split('/')[-1]
			logme.debug('remotefilename=>', remotefilename)
			localfile = os.path.join(os.path.dirname(__file__), 'storage', 'private', 'File', callername,
			                         remotefilename)
			logme.debug('localfile=>', localfile)
			# logme.debug(os.path.dirname(__file__))
			fp = open(localfile, 'wb')  # 以写模式在本地打开文件
			ftp.retrbinary('RETR ' + remotefile, fp.write, bufsize)
			fp.close()
			ftp.quit()
			
			return ('success', '远程文件[%s] ftp[%s] 本地下载成功.' % (remotefile, ','.join((ip, str(port)))))
		
		
		except:
			return ('error', 'ftp下载异常[%s]' % traceback.format_exc())
	
	@classmethod
	def local_file_check(cls, filename, templatename, checklist, callername, jarname='jiemi_rh_20200326.jar'):
		
		toolpath = os.path.join(os.path.dirname(__file__), 'storage', 'public', 'tools', jarname)
		filepath = os.path.join(os.path.dirname(__file__), 'storage', 'private', 'File', callername, filename)
		if not os.path.exists(toolpath):
			return ('error', '文件[%s]不存在' % jarname)
		if not os.path.exists(filepath):
			return ('error', '文件[%s]不存在' % filename)
		
		decryptresult = ''
		if filename.endswith('rd'):
			with open(filepath) as f:
				decryptresult = f.read()
		else:
			command = 'java -jar %s %s' % (toolpath, filepath)
			p = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
			                     stdout=subprocess.PIPE)
			p.wait()
			decryptresult = p.communicate()[0].decode('GBK')
		
		logme.debug('==获得文件[%s]内容:\n%s' % (filename, decryptresult))
		
		parser = MessageParser.get_parse_config(templatename)
		if parser[0] is not 'success':
			return parser
		mp = MessageParser(parser[1], decryptresult, checklist)
		checkresult = mp.compute()
		
		logme.debug('本地文件校验计算明细=>', checkresult)
		for exp in checkresult:
			if checkresult[exp][0] is not 'success':
				return checkresult[exp]
		
		return ('success', '表达式[%s]校验通过' % '|'.join(checklist))
