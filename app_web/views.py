from django.shortcuts import render, redirect, HttpResponse
from django.views import View


def page_not_found(request, exception):
    return render(request, '404.html')
