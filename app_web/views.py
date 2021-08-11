from django.shortcuts import render, redirect, HttpResponse
from django.views import View


class Login(View):
    def get(self, request):
        return HttpResponse('login')
