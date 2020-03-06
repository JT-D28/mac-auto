#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-08-27 16:00:23
# @Author  : Blackstone
# @to      :

from django import forms

class UserForm(forms.Form):
    username=forms.CharField(label='Username',widget=forms.TextInput(attrs={'autocomplete':"off"}))
    password=forms.CharField(label='Password',widget=forms.PasswordInput(attrs={'autocomplete':"off"}))

class RegisterForm(forms.Form):
    gender = (
        ('male', "男"),
        ('female', "女"),
    )
    username = forms.CharField(label="用户名", max_length=128, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label="密码", max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="确认密码", max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="邮箱地址", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    sex = forms.ChoiceField(label='性别', choices=gender)
