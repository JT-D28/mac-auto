#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-11-01 16:10:06
# @Author  : Blackstone
# @to      :

import paramiko
# 服务器相关信息,下面输入你个人的用户名、密码、ip等信息

class RemoteLogReader:
	_config=None

	@classmethod
	def connect(cls,config):
		cls._config=config

	@classmethod
	def push_start_agent(cls,config):
		transport = paramiko.Transport((cls._config['ip'], int(cls._config['port'])))
		transport.connect(username=cls._config['username'], password=cls._config['port'])
		sftp = paramiko.SFTPClient.from_transport(transport)#可能还需秘钥
		sftp.put('agent.py', "/root/itf-agent.py")
		transport.close()

		#start
		ssh= paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 允许连接不在know_hosts文件中的主机
		ssh.connect(cls._config['root'], int(cls._config['port']),cls._config['username'],cls._config['port'])
		execmd = 'python /root/itf-agent.py -file %s'%cls._config['file'] #需要输入的命令
		stdin, stdout, stderr = s.exec_command (execmd)


	@classmethod
	def get_line_content(cls):

		print(stdout.read())
		s.close()

	@classmethod
	def stop(cls,clear_agent=True):
		pass


	def test(cls):
		ip = "10.60.44.87"  
		port =  22
		user = "root"
		password = "Fingard@123"
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		# 建立连接
		ssh.connect(ip,port,user,password,timeout = 10)

		#输入linux命令
		stdin,stdout,stderr = ssh.exec_command("cat /root/mock.log")
		# 输出命令执行结果
		result = stdout.read()
		print(result)
		#关闭连接
		ssh.close()


