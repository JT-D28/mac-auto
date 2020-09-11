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
		request_url = request.path_info
		# 如果请求url在白名单，放行
		for url in settings.SAFE_URL:
			if re.match(url, request_url):
				return None
		
		if not request.session.get('is_login'):
			return HttpResponseRedirect('/api/account/login/')
		#  用户是admin，全部权限
		if request.session.get('username') == 'admin':
			return None
		
		permission_url = request.session.get(settings.SESSION_PERMISSION_URL_KEY)
		
		# 如果未取到permission_url, 重定向至登录；为了可移植性，将登录url写入配置
		# 另外，Login必须设置白名单，否则访问login会反复重定向
		if not permission_url:
			return redirect(settings.LOGIN_URL)
		
		# 循环permission_url，作为正则，匹配用户request_url
		# 正则应该进行一些限定，以处理：/user/ -- /user/add/匹配成功的情况
		flag = False
		for url in permission_url:
			url_pattern = settings.REGEX_URL.format(url=url)
			if re.match(url_pattern, request_url):
				flag = True
				break
		return None if flag else JsonResponse({'code': 403})
