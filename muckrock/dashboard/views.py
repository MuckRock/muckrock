"""
Views for the Dashboard application
"""

from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import render

from datetime import date, timedelta

from muckrock.accounts.models import Statistics

def dashboard(request):
    """Renders and returns the dashboard."""
    return render(request, 'dashboard.html')

def dashboard_data(request):
    """Returns a week of statistics rendered into JSON."""
    stats = Statistics.objects.all()[:7]
    data = serializers.serialize('json', stats)
    return HttpResponse(data, content_type='application/json')
