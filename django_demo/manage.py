#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys,datetime,traceback
from apscheduler.schedulers.background import BackgroundScheduler
# from .manager.invoker import check_user_task
def timedTask():
    print(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_demo.settings')
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
    try:
        execute_from_command_line(sys.argv)
    except:
        #print(traceback.format_exc())
        pass



if __name__ == '__main__':

    main()
