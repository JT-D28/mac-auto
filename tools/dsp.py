import wmi
def sys_version(ipaddress, user, password):
    try:
        conn = wmi.WMI(computer=ipaddress, user=user, password=password)
        for sys in conn.Win32_OperatingSystem():
            print ("Version:%s" % sys.Caption, "Vernum:%s" % sys.BuildNumber ) # 系统信息
            print (sys.OSArchitecture.encode("UTF8"))  # 系统的位数
            print (sys.NumberOfProcesses ) # 系统的进程数

            filename = r"C:\test.bat"  # 此文件在远程服务器上
            cmd_callbat = r"cmd /c call %s" % filename
            print(cmd_callbat)
            id, value =conn.Win32_Process.Create(CommandLine=cmd_callbat)  # 执行bat文件   Win32_Process.Create
            print(id,value)
    except Exception as e:
        print (e)
        print (e.com_error.strerror.encode("UTF8"))


if __name__ == '__main__':
    sys_version(ipaddress="192.168.68.132", user="Administrator", password="123")