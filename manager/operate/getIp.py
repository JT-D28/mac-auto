import socket


def get_host_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(('1.1.1.1',80))
        ip=s.getsockname()[0]
    finally:
        s.close()
    return ip