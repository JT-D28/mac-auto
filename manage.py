#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys, datetime, traceback

# from twisted.internet import asyncioreactor

from ME2.configs import confs
# from apscheduler.schedulers.background import BackgroundScheduler



# from .manager.invoker import check_user_task
def timedTask():
	print(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])

def main():
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ME2.settings')
	try:
		from django.core.management import execute_from_command_line
	except ImportError as exc:
		raise ImportError(
			"Couldn't import Django. Are you sure it's installed and "
			"available on your PYTHONPATH environment variable? Did you "
			"forget to activate a virtual environment?"
		) from exc
	
	print("++++++++++++++++++++++++++++++++++")
	# check_user_task()
	if 'daphne' == sys.argv[1]:
		current_reactor = sys.modules.get("twisted.internet.reactor", None)
		if current_reactor is not None:
			if not isinstance(current_reactor, asyncioreactor.AsyncioSelectorReactor):
				del sys.modules["twisted.internet.reactor"]
				asyncioreactor.install()
		else:
			asyncioreactor.install()
		print('使用配置：')
		for des in confs.options('useconfig'):
			if len(des) < 20:
				hdes = des + ' ' * (20 - len(des))
			print('%s: \t%s' % (hdes, confs['useconfig'][des]))
		from daphne import cli
		cli = cli.CommandLineInterface()
		cli.run(args=['-p', sys.argv.pop(), '-b', '0.0.0.0', 'ME2.asgi:application','-v','0'])
	else:
		execute_from_command_line(sys.argv)


if __name__ == '__main__':
	main()
