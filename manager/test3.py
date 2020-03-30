
from ftplib import FTP
import traceback,os
def ftp_to_local(ip,port,username,password,remotefile,callername):
    try:
        ftp = FTP()
        ftp.set_debuglevel(0)
        ftp.connect(ip,int(port))
        ftp.login(username,password)
        bufsize = 1024
        #remotefilename=os.sep.split(remotefile)[-1]
        remotefilename=remotefile.split('/')[-1]
        print('remotefilename=>',remotefilename)
        localfile=os.path.join(os.path.dirname(__file__),'storage','private','File',callername,remotefilename)
        print('localfile=>',localfile)
        #print(os.path.dirname(__file__))
        fp = open(localfile,'wb') #以写模式在本地打开文件
        ftp.retrbinary('RETR ' + remotefile,fp.write,bufsize) 
        fp.close()
        ftp.quit()

        return ('success','远程文件[%s] ftp[%s] 本地下载成功.'%(remotefile,','.join((ip,str(port)))))


    except:
        return ('error','ftp下载异常[%s]'%traceback.format_exc())




def local_to_ftp(filename,ip,port,username,password,remotedir,callername):
    try:
        ftp = FTP()
        ftp.set_debuglevel(0)
        ftp.connect(ip,int(port))
        ftp.login(username,password)
        bufsize = 1024
        localfile=os.path.join(os.path.dirname(__file__),'storage','private','File',callername,filename)
        if not os.path.exists(localfile):
            return ('error','本地文件[%s]不存在 请先上传'%localfile)
        fp = open(localfile, 'rb')
        remotepath=os.path.join(remotedir,filename)
        ftp.storbinary('STOR ' + remotepath, fp, bufsize)
        fp.close()
        ftp.quit()

        return ('success','本地文件[%s] 上传ftp[%s]成功. '%(filename,','.join((ip,str(port),remotepath))      ))
    except:
        return ('error','ftp上传异常[%s]'%traceback.format_exc())
    

ip='172.17.1.30'
port=8021
username='PT'
password='pt123'
remotefile='/INSURANCE/AS330106/REC/AS330106_212020191101_20191101154417.rd'
callername='hujj'
#res=ftp_to_local(ip, port, username, password, remotefile, callername)

filename='AS330106_212020191101_20191101154417.rd'
res=local_to_ftp(filename,ip,port,username,password,'/INSURANCE',callername)
print(res)