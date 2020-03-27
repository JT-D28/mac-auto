import subprocess
command=r'java -jar C:\Users\F\Desktop\测试文件\tool.jar C:\Users\F\Desktop\测试文件\AS330106_212020191101_20191101154417.r'
p=subprocess.Popen(command,shell=True,stdin=subprocess.PIPE,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
print(p.communicate()[0].decode('gbk'))