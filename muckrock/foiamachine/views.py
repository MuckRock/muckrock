"""FOIAMachine views"""

from django.shortcuts import render

def homepage(request):
    """FOIAMachine homepage"""
    return render(request, 'foiamachine/homepage.html')
