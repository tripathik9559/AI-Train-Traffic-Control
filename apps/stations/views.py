"""
Station & Route Management Views
"""

import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Station, Platform, Route, TrackSection
from .forms import StationForm, PlatformForm, RouteForm, TrackSectionForm

logger = logging.getLogger(__name__)


@ensure_csrf_cookie
@login_required
def station_list(request):
    """Stations & Routes Management Command Center."""
    from django.views.decorators.cache import never_cache as _nc
    all_stations = Station.objects.filter(is_active=True).prefetch_related('platforms')

    search = request.GET.get('search', '').strip()
    zone_filter = request.GET.get('zone', '')
    type_filter = request.GET.get('type', '')

    filtered = all_stations
    if search:
        filtered = filtered.filter(
            Q(name__icontains=search) | Q(code__icontains=search) |
            Q(city__icontains=search) | Q(state__icontains=search)
        )
    if zone_filter:
        filtered = filtered.filter(zone=zone_filter)
    if type_filter:
        filtered = filtered.filter(station_type=type_filter)

    filtered = filtered.order_by('name')
    paginator = Paginator(filtered, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Aggregates for KPI row
    from django.db.models import Sum, Count, Avg
    total_stations   = all_stations.count()
    active_stations  = all_stations.count()
    total_platforms  = Platform.objects.filter(station__is_active=True, is_active=True).count()
    avail_platforms  = Platform.objects.filter(station__is_active=True, is_active=True, status='AVAILABLE').count()
    total_routes     = Route.objects.filter(is_active=True).count()
    total_sections   = TrackSection.objects.filter(is_active=True).count()
    clear_sections   = TrackSection.objects.filter(is_active=True, status='CLEAR').count()

    routes     = Route.objects.filter(is_active=True).select_related('source_station','destination_station')[:10]
    sections   = TrackSection.objects.filter(is_active=True).select_related('from_station','to_station')[:15]
    zones      = all_stations.values_list('zone', flat=True).distinct()

    # Stations JSON for topology map
    import json as _json
    stations_json = _json.dumps([{
        'id': s.id, 'code': s.code, 'name': s.name,
        'lat': s.latitude, 'lng': s.longitude,
        'type': s.station_type, 'platforms': s.total_platforms,
        'city': s.city,
    } for s in all_stations])

    sections_json = _json.dumps([{
        'code': sec.code, 'name': sec.name,
        'from': sec.from_station.code, 'to': sec.to_station.code,
        'status': sec.status, 'color': sec.status_color,
        'length': sec.length,
    } for sec in TrackSection.objects.filter(is_active=True).select_related('from_station','to_station')])

    context = {
        'page_obj': page_obj,
        'search': search,
        'zone_filter': zone_filter,
        'type_filter': type_filter,
        'zones': sorted(z for z in zones if z),
        'type_choices': Station.StationType.choices,
        'page_title': 'Stations & Routes Command Center',
        'active_nav': 'stations',
        # KPI
        'total_stations': total_stations,
        'active_stations': active_stations,
        'total_platforms': total_platforms,
        'avail_platforms': avail_platforms,
        'total_routes': total_routes,
        'total_sections': total_sections,
        'clear_sections': clear_sections,
        'network_health': round((clear_sections / total_sections * 100) if total_sections else 94, 1),
        'avg_utilization': 78.4,
        # Data
        'all_stations': all_stations,
        'routes': routes,
        'sections': sections,
        'stations_json': stations_json,
        'sections_json': sections_json,
    }
    return render(request, 'stations/list.html', context)


@login_required
def station_create(request):
    form = StationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        station = form.save()
        messages.success(request, f'Station {station.name} ({station.code}) created.')
        return redirect('stations:detail', station_id=station.id)
    return render(request, 'stations/form.html', {
        'form': form, 'page_title': 'Add Station', 'active_nav': 'stations', 'action': 'create'
    })


@login_required
def station_edit(request, station_id):
    station = get_object_or_404(Station, id=station_id)
    form = StationForm(request.POST or None, instance=station)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Station {station.name} updated.')
        return redirect('stations:detail', station_id=station.id)
    return render(request, 'stations/form.html', {
        'form': form, 'station': station,
        'page_title': f'Edit Station — {station.code}',
        'active_nav': 'stations', 'action': 'edit'
    })


@login_required
def station_detail(request, station_id):
    station = get_object_or_404(Station, id=station_id)
    platforms = station.platforms.all()
    routes_from = Route.objects.filter(source_station=station, is_active=True)
    sections_from = TrackSection.objects.filter(from_station=station, is_active=True)

    context = {
        'station': station,
        'platforms': platforms,
        'routes_from': routes_from,
        'sections_from': sections_from,
        'page_title': f'Station — {station.name}',
        'active_nav': 'stations',
    }
    return render(request, 'stations/detail.html', context)


@login_required
def route_list(request):
    routes = Route.objects.filter(is_active=True).select_related('source_station', 'destination_station')
    context = {
        'routes': routes,
        'page_title': 'Route Management',
        'active_nav': 'stations',
    }
    return render(request, 'stations/routes.html', context)


@login_required
def route_create(request):
    form = RouteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Route created.')
        return redirect('stations:routes')
    return render(request, 'stations/route_form.html', {
        'form': form, 'page_title': 'Add Route', 'active_nav': 'stations'
    })


@login_required
def track_section_list(request):
    sections = TrackSection.objects.filter(is_active=True).select_related('from_station', 'to_station')
    context = {
        'sections': sections,
        'page_title': 'Track Sections',
        'active_nav': 'stations',
        'status_choices': TrackSection.TrackStatus.choices,
    }
    return render(request, 'stations/sections.html', context)


@login_required
def track_section_create(request):
    form = TrackSectionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Track section created.')
        return redirect('stations:sections')
    return render(request, 'stations/section_form.html', {
        'form': form, 'page_title': 'Add Track Section', 'active_nav': 'stations'
    })


@login_required
@require_http_methods(["POST"])
def update_section_status(request, section_id):
    """AJAX: Update track section status."""
    section = get_object_or_404(TrackSection, id=section_id)
    data = json.loads(request.body)
    new_status = data.get('status')
    if new_status and new_status in dict(TrackSection.TrackStatus.choices):
        section.status = new_status
        section.save(update_fields=['status', 'updated_at'])
        return JsonResponse({'success': True, 'status': section.status, 'color': section.status_color})
    return JsonResponse({'error': 'Invalid status'}, status=400)


@login_required
def api_stations_json(request):
    """API: All stations for network visualizer."""
    stations = Station.objects.filter(is_active=True)
    data = [
        {
            'id': s.id, 'code': s.code, 'name': s.name,
            'lat': s.latitude, 'lng': s.longitude,
            'type': s.station_type, 'platforms': s.total_platforms,
        }
        for s in stations
    ]
    return JsonResponse({'stations': data})


@login_required
def api_sections_json(request):
    """API: All track sections."""
    sections = TrackSection.objects.filter(is_active=True).select_related('from_station', 'to_station')
    data = [
        {
            'code': s.code, 'name': s.name,
            'from_id': s.from_station.id, 'to_id': s.to_station.id,
            'from_code': s.from_station.code, 'to_code': s.to_station.code,
            'status': s.status, 'color': s.status_color,
            'length': s.length, 'lines': s.number_of_lines,
        }
        for s in sections
    ]
    return JsonResponse({'sections': data})
