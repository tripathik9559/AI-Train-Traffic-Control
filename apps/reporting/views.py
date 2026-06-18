"""
Reporting System Views — PDF and CSV report generation.
"""

import csv
import io
import logging
from datetime import date, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone

from apps.trains.models import Train
from apps.conflicts.models import Conflict
from apps.scheduling.models import Schedule
from apps.analytics.models import AnalyticsSnapshot

logger = logging.getLogger(__name__)


@login_required
def report_index(request):
    """Reporting dashboard."""
    today = timezone.now().date()
    context = {
        'page_title': 'Reports & Analytics',
        'active_nav': 'reports',
        'today': today,
        'week_start': today - timedelta(days=7),
        'month_start': today.replace(day=1),
    }
    return render(request, 'reporting/index.html', context)


@login_required
def generate_daily_report(request):
    """Generate daily operations report."""
    report_date_str = request.GET.get('date', timezone.now().date().isoformat())
    try:
        report_date = date.fromisoformat(report_date_str)
    except ValueError:
        report_date = timezone.now().date()

    export_format = request.GET.get('format', 'html')

    # Gather data
    trains = Train.objects.filter(is_active=True)
    schedules = Schedule.objects.filter(
        scheduled_date=report_date
    ).select_related('train', 'station', 'platform')

    conflicts = Conflict.objects.filter(
        detected_at__date=report_date
    ).select_related('train_a', 'train_b', 'station')

    total_trains = trains.count()
    delayed = trains.filter(current_status='DELAYED').count()
    cancelled = trains.filter(current_status='CANCELLED').count()
    on_time = trains.filter(current_delay__lte=5).count()
    punctuality = round((on_time / max(total_trains, 1)) * 100, 1)
    avg_delay = round(
        sum(t.current_delay for t in trains if t.current_delay > 0) /
        max(delayed, 1), 1
    )

    report_data = {
        'report_date': report_date,
        'generated_at': timezone.now(),
        'generated_by': request.user,
        'total_trains': total_trains,
        'delayed_trains': delayed,
        'cancelled_trains': cancelled,
        'on_time_trains': on_time,
        'punctuality_rate': punctuality,
        'avg_delay': avg_delay,
        'schedules': schedules,
        'conflicts': conflicts,
        'total_conflicts': conflicts.count(),
        'resolved_conflicts': conflicts.filter(status='RESOLVED').count(),
        'critical_conflicts': conflicts.filter(severity='CRITICAL').count(),
    }

    if export_format == 'csv':
        return _export_daily_csv(report_data, report_date)
    elif export_format == 'pdf':
        return _export_daily_pdf(report_data, report_date)

    return render(request, 'reporting/daily_report.html', {
        **report_data,
        'page_title': f'Daily Report — {report_date.strftime("%d %b %Y")}',
        'active_nav': 'reports',
    })


@login_required
def generate_conflict_report(request):
    """Generate conflict analysis report."""
    from_date_str = request.GET.get('from', (timezone.now().date() - timedelta(days=7)).isoformat())
    to_date_str = request.GET.get('to', timezone.now().date().isoformat())
    export_format = request.GET.get('format', 'html')

    try:
        from_date = date.fromisoformat(from_date_str)
        to_date = date.fromisoformat(to_date_str)
    except ValueError:
        from_date = timezone.now().date() - timedelta(days=7)
        to_date = timezone.now().date()

    conflicts = Conflict.objects.filter(
        detected_at__date__gte=from_date,
        detected_at__date__lte=to_date,
    ).select_related('train_a', 'train_b', 'station', 'track_section').order_by('-detected_at')

    from django.db.models import Count
    type_stats = conflicts.values('conflict_type').annotate(count=Count('id'))
    severity_stats = conflicts.values('severity').annotate(count=Count('id'))

    report_data = {
        'from_date': from_date,
        'to_date': to_date,
        'conflicts': conflicts,
        'total': conflicts.count(),
        'resolved': conflicts.filter(status='RESOLVED').count(),
        'active': conflicts.filter(status='ACTIVE').count(),
        'critical': conflicts.filter(severity='CRITICAL').count(),
        'type_stats': list(type_stats),
        'severity_stats': list(severity_stats),
        'generated_at': timezone.now(),
        'generated_by': request.user,
    }

    if export_format == 'csv':
        return _export_conflict_csv(conflicts, from_date, to_date)

    return render(request, 'reporting/conflict_report.html', {
        **report_data,
        'page_title': f'Conflict Report: {from_date} to {to_date}',
        'active_nav': 'reports',
    })


@login_required
def generate_train_report(request):
    """Generate per-train performance report."""
    export_format = request.GET.get('format', 'html')
    trains = Train.objects.filter(is_active=True).select_related(
        'source_station', 'destination_station'
    ).order_by('-current_delay')

    if export_format == 'csv':
        return _export_train_csv(trains)

    return render(request, 'reporting/train_report.html', {
        'trains': trains,
        'total_trains': trains.count(),
        'delayed_count': trains.filter(current_status='DELAYED').count(),
        'generated_at': timezone.now(),
        'page_title': 'Train Performance Report',
        'active_nav': 'reports',
    })


# ─── Export Helpers ────────────────────────────────────────────────────────

def _export_daily_csv(data, report_date):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="daily_report_{report_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(['DAILY OPERATIONS REPORT', report_date.strftime('%d %b %Y')])
    writer.writerow([])
    writer.writerow(['KPI', 'Value'])
    writer.writerow(['Total Trains', data['total_trains']])
    writer.writerow(['Delayed Trains', data['delayed_trains']])
    writer.writerow(['Cancelled Trains', data['cancelled_trains']])
    writer.writerow(['On-Time Trains', data['on_time_trains']])
    writer.writerow(['Punctuality Rate (%)', data['punctuality_rate']])
    writer.writerow(['Average Delay (min)', data['avg_delay']])
    writer.writerow(['Total Conflicts', data['total_conflicts']])
    writer.writerow(['Resolved Conflicts', data['resolved_conflicts']])
    writer.writerow([])
    writer.writerow(['Train Number', 'Train Name', 'Status', 'Delay (min)', 'Station'])
    for s in data['schedules']:
        writer.writerow([
            s.train.train_number, s.train.train_name,
            s.status, s.current_delay, s.station.name
        ])
    return response


def _export_conflict_csv(conflicts, from_date, to_date):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="conflicts_{from_date}_{to_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Conflict ID', 'Type', 'Severity', 'Status', 'Train A', 'Train B',
                     'Station', 'Detected At', 'Resolved At'])
    for c in conflicts:
        writer.writerow([
            c.id, c.conflict_type, c.severity, c.status,
            c.train_a.train_number,
            c.train_b.train_number if c.train_b else '—',
            c.station.name if c.station else '—',
            c.detected_at.strftime('%Y-%m-%d %H:%M'),
            c.resolved_at.strftime('%Y-%m-%d %H:%M') if c.resolved_at else '—',
        ])
    return response


def _export_train_csv(trains):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="train_performance.csv"'

    writer = csv.writer(response)
    writer.writerow(['Train No', 'Name', 'Type', 'Status', 'Delay (min)',
                     'Priority', 'Source', 'Destination', 'Speed (km/h)'])
    for t in trains:
        writer.writerow([
            t.train_number, t.train_name, t.get_train_type_display(),
            t.current_status, t.current_delay, t.priority_level,
            t.source_station.code if t.source_station else '—',
            t.destination_station.code if t.destination_station else '—',
            t.speed,
        ])
    return response


def _export_daily_pdf(data, report_date):
    """Generate PDF using reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
        from reportlab.lib.units import cm

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                     fontSize=18, textColor=colors.HexColor('#1a1a2e'))
        story.append(Paragraph(f"Daily Operations Report", title_style))
        story.append(Paragraph(f"{report_date.strftime('%d %B %Y')}", styles['Normal']))
        story.append(Spacer(1, 0.5*cm))

        kpi_data = [
            ['KPI', 'Value'],
            ['Total Trains', str(data['total_trains'])],
            ['Delayed', str(data['delayed_trains'])],
            ['On-Time', str(data['on_time_trains'])],
            ['Punctuality Rate', f"{data['punctuality_rate']}%"],
            ['Avg Delay', f"{data['avg_delay']} min"],
            ['Total Conflicts', str(data['total_conflicts'])],
        ]
        t = Table(kpi_data, colWidths=[8*cm, 6*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"Generated at: {data['generated_at'].strftime('%Y-%m-%d %H:%M')} "
                                f"by {data['generated_by'].username}", styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="daily_report_{report_date}.pdf"'
        return response

    except ImportError:
        logger.warning("reportlab not available, falling back to CSV")
        return _export_daily_csv(data, report_date)
