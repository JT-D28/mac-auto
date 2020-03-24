"""
WSGI config for ME2 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os, traceback

from django.core.wsgi import get_wsgi_application

from .pipline import *

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ME2.settings')
application = get_wsgi_application()
