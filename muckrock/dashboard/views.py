"""
Views for the Dashboard application
"""

from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import render

from datetime import date, timedelta
from dateutil.parser import parse

from muckrock.accounts.models import Statistics

def dashboard(request):
    """Renders and returns the dashboard."""
    return render(request, 'dashboard.html')

def dashboard_data(request):
    """Returns a week of statistics rendered into JSON."""
    stats = Statistics.objects.all()
    min_date = request.GET.get('min_date')
    max_date = request.GET.get('max_date')
    if max_date:
        max_date = parse(max_date)
        stats = stats.exclude(date__gt=max_date)
    if min_date:
        min_date = parse(min_date)
        stats = stats.exclude(date__lt=min_date)
    data = serializers.serialize('json', stats)
    return HttpResponse(data, content_type='application/json')
