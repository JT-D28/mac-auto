#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-08-27 16:00:23
# @Author  : Blackstone
# @to      :

from django import forms


class InterfaceForm(forms.Form):
	author = forms.CharField(label='author', widget=forms.TextInput(attrs={'class': 'form-control'}))
	name = forms.CharField(label='name', widget=forms.TextInput(attrs={'class': 'form-control'}))
	headers = forms.CharField(label='headers', widget=forms.TextInput(attrs={'class': 'form-control'}))
	url = forms.CharField(label='url', widget=forms.TextInput(attrs={'class': 'form-control'}))
	method = forms.CharField(label='method', widget=forms.TextInput(attrs={'class': 'form-control'}))
	content_type = forms.ChoiceField(
		choices=(('urlencode', 'xxx-www-form-urlencode'), ('json', 'application/json'), ('xml', 'application/xml')))
	version = forms.CharField(label='version', widget=forms.TextInput(attrs={'class': 'form-control'}))
	body = forms.CharField(label='body', widget=forms.TextInput(attrs={'class': 'form-control'}))


class StepForm(forms.Form):
	run_order = forms.CharField(label='执行顺序', widget=forms.TextInput(attrs={'class': 'form-control'}))
	url = forms.CharField(label='url', widget=forms.TextInput(
		attrs={'class': 'form-control', 'placeholder': "Username", 'autofocus': ''}))
	method = forms.ChoiceField(label='method', choices=(('get', 'GET'), ('post', 'POST')))
	content_type = forms.ChoiceField(label='content-type', choices=(
		('json', 'application/json'), ('xml', 'application/xml'), ('urlencode', 'x-www-form-urlencode')))
	version = forms.CharField(label='version', widget=forms.TextInput(attrs={'class': 'form-control'}))
	body = forms.CharField(label='body', widget=forms.TextInput(attrs={'class': 'form-control'}))
	db_check = forms.CharField(label='db_check', widget=forms.TextInput(attrs={'class': 'form-control'}))
	itf_check = forms.CharField(label='itf_check', widget=forms.TextInput(attrs={'class': 'form-control'}))
	headers = forms.CharField(label='headers', widget=forms.TextInput(attrs={'class': 'form-control'}))
	description = forms.CharField(label='description', widget=forms.TextInput(attrs={'class': 'form-control'}))


class VariableForm(forms.Form):
	description = forms.CharField(label='description', widget=forms.TextInput(attrs={'class': 'form-control'}))
	tag = forms.CharField(label='tag', widget=forms.TextInput(attrs={'class': 'form-control'}))  #
	author = forms.CharField(label='author', widget=forms.TextInput(attrs={'class': 'form-control'}))
	key = forms.CharField(label='key', widget=forms.TextInput(attrs={'class': 'form-control'}))
	value = forms.CharField(label='value', widget=forms.TextInput(attrs={'class': 'form-control'}))
	gain = forms.CharField(label='gain', widget=forms.TextInput(attrs={'class': 'form-control'}))
	is_cache = forms.BooleanField(label='cache')
# is_default=forms.BooleanField(label='cache')
