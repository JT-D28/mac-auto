urls=[
"{{a}}/test_expression/",
"http://127.0.0.1:8000/test_expression/",
"https://127.0.0.1:8000/test_expression/"
]

for url in urls:
	matcher=[a for a in url.split('/') if not a.__contains__("{{") and not a.__contains__(':')]
	api='/'.join(matcher)
	if not  api.startswith('/'):
		#print(api)
		api='/'+api

	print(api)
