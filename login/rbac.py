from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import HttpResponse, redirect
import re


class MiddlewareMixin(object):
	def __init__(self, get_response=None):
		self.get_response = get_response
		super(MiddlewareMixin, self).__init__()
	
	def __call__(self, request):
		response = None
		if hasattr(self, 'process_request'):
			response = self.process_request(request)
		if not response:
			response = self.get_response(request)
		if hasattr(self, 'process_response'):
			response = self.process_response(request, response)
		return response


class RbacMiddleware(MiddlewareMixin):
	"""
	检查用户的url请求是否是其权限范围内
	"""
	
	def process_request(self, request):
		if request.session.get('username') == 'admin':
			return None

		request_url = request.path_info
		permission_url = request.session.get(settings.SESSION_PERMISSION_URL_KEY)
		# 如果请求url在白名单，放行
		for url in settings.SAFE_URL:
			if re.match(url, request_url):
				return None
		if not request.session.get('is_login'):
			return HttpResponseRedirect('/api/account/login/')
		
		print("1111",request_url,permission_url)
		
		if request_url in request.session[settings.SESSION_MENU_KEY].get(settings.ALL_PERMISSION_KEY,[]):
			print("2222", request_url, settings.ALL_PERMISSION_KEY)
			flag = False
			for url in permission_url:
				print("2222", url, settings.ALL_PERMISSION_KEY)
				url_pattern = settings.REGEX_URL.format(url=url)
				if re.match(url_pattern, request_url):
					flag = True
					break
			return None if flag else JsonResponse({'code': 403})
		
