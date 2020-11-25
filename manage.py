import os
import sys


def main():
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ME2.settings')
	try:
		from django.core.management import execute_from_command_line
	except ImportError as exc:
		raise ImportError("启动失败，检查环境") from exc
	
	print("++++++++++++++++++++++++++++++++++")
	execute_from_command_line(sys.argv)


if __name__ == '__main__':
	main()
