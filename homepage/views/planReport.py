from django.shortcuts import render


def planreport(request):
	return render(request, 'planreport.html')