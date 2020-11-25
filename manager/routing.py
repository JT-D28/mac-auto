#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-08-30 15:05:27
# @Author  : Blackstone
# @to      :

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path, re_path
from homepage.views import getlog
from performance.views import reportConsumer

websocket_urlpatterns = [
	path(r'ws/getlog', getlog),
	path(r'ws/report', reportConsumer),
]

application = ProtocolTypeRouter({
	'websocket': AuthMiddlewareStack(
		URLRouter(
			websocket_urlpatterns
		)
	)
})
