from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.shortcuts import render
from django.shortcuts import render, redirect

# Create your views here.
def index(request):
    return render (request,"Dashboard/index.html")

