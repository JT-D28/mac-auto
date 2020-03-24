#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-08-30 15:05:27
# @Author  : Blackstone
# @to      :

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path, re_path
from manager.consumer import ChatConsumer, ConsoleConsumer, logConsumer

websocket_urlpatterns = [
	path(r"ws/intercept/", ChatConsumer),
	path(r"ws/consolemsg/", ConsoleConsumer),
	path(r"ws/runlog/", logConsumer)
]

application = ProtocolTypeRouter({
	'websocket': AuthMiddlewareStack(
		URLRouter(
			websocket_urlpatterns
		)
	)
})
