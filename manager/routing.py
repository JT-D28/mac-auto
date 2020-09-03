#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-08-30 15:05:27
# @Author  : Blackstone
# @to      :

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path, re_path
from manager.consumer import ChatConsumer, ConsoleConsumer, logConsumer, PkgSaveConsumer, PkgReadConsumer, \
    ContinuousConsumer
from homepage.views import getlog

websocket_urlpatterns = [
    path(r"ws/intercept/", ChatConsumer),
    path(r"ws/consolemsg/", ConsoleConsumer),
    path(r'ws/pkgsave/', PkgSaveConsumer),
    path(r'ws/pkgread/', PkgReadConsumer),
    path(r"ws/runlog/", logConsumer),
    re_path(r'^ws/getlog/(?P<id>.*)/$', getlog),
    path(r'ws/continuous/',ContinuousConsumer)
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    )
})
