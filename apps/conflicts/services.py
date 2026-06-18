"""
Conflict Detection Engine
Detects track conflicts, platform conflicts, crossing conflicts, and section occupancy issues.
Uses time-space analysis to identify potential conflicts between scheduled trains.
"""

import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

logger = logging.getLogger(__name__)


class ConflictDetectionEngine:
    """
    Core conflict detection engine for railway operations.

    Implements time-space analysis to detect:
    - Track section conflicts (two trains on same section simultaneously)
    - Platform conflicts (two trains at same platform simultaneously)
    - Crossing conflicts (trains on single-line sections approaching each other)
    - Headway violations (insufficient gap between successive trains)
    """

    MIN_HEADWAY_MINUTES = 10  # Minimum gap between trains on same section
    PLATFORM_BUFFER_MINUTES = 5  # Buffer time for platform clearance
    WARNING_WINDOW_MINUTES = 60  # Look-ahead window for conflict detection

    def detect_all(self, scheduled_date=None):
        """Run complete conflict detection for a given date."""
        if scheduled_date is None:
            scheduled_date = timezone.now().date()

        logger.info(f"Running conflict detection for {scheduled_date}")

        detected = []
        detected.extend(self._detect_track_conflicts(scheduled_date))
        detected.extend(self._detect_platform_conflicts(scheduled_date))
        detected.extend(self._detect_crossing_conflicts(scheduled_date))
        detected.extend(self._detect_headway_violations(scheduled_date))

        # Persist detected conflicts
        saved = self._persist_conflicts(detected)
        logger.info(f"Detected {len(saved)} conflicts for {scheduled_date}")
        return saved

    def _detect_track_conflicts(self, scheduled_date):
        """Detect when two trains are scheduled on the same track section simultaneously."""
        from apps.scheduling.models import Schedule

        conflicts = []
        schedules = list(
            Schedule.objects.filter(
                scheduled_date=scheduled_date,
                track_section__isnull=False,
                status__in=['SCHEDULED', 'RUNNING', 'DELAYED']
            ).select_related('train', 'track_section', 'station')
        )

        for i in range(len(schedules)):
            for j in range(i + 1, len(schedules)):
                s1, s2 = schedules[i], schedules[j]

                if s1.train == s2.train:
                    continue

                if s1.track_section != s2.track_section:
                    continue

                if self._times_overlap(s1, s2, buffer=0):
                    severity = self._compute_severity(s1.train, s2.train, 'TRACK')
                    conflicts.append({
                        'conflict_type': 'TRACK',
                        'severity': severity,
                        'train_a': s1.train,
                        'train_b': s2.train,
                        'track_section': s1.track_section,
                        'station': s1.station,
                        'conflict_time': s1.scheduled_arrival or timezone.now(),
                        'description': (
                            f"Track conflict detected: Train {s1.train.train_number} "
                            f"({s1.train.train_name}) and Train {s2.train.train_number} "
                            f"({s2.train.train_name}) are both scheduled on section "
                            f"{s1.track_section.name} simultaneously."
                        ),
                    })

        return conflicts

    def _detect_platform_conflicts(self, scheduled_date):
        """Detect when two trains occupy the same platform simultaneously."""
        from apps.scheduling.models import Schedule

        conflicts = []
        schedules = list(
            Schedule.objects.filter(
                scheduled_date=scheduled_date,
                platform__isnull=False,
                status__in=['SCHEDULED', 'RUNNING', 'DELAYED']
            ).select_related('train', 'platform', 'station')
        )

        for i in range(len(schedules)):
            for j in range(i + 1, len(schedules)):
                s1, s2 = schedules[i], schedules[j]

                if s1.train == s2.train:
                    continue

                if s1.platform != s2.platform:
                    continue

                if self._times_overlap(s1, s2, buffer=self.PLATFORM_BUFFER_MINUTES):
                    severity = self._compute_severity(s1.train, s2.train, 'PLATFORM')
                    conflicts.append({
                        'conflict_type': 'PLATFORM',
                        'severity': severity,
                        'train_a': s1.train,
                        'train_b': s2.train,
                        'platform': s1.platform,
                        'station': s1.station,
                        'conflict_time': s1.scheduled_arrival or timezone.now(),
                        'description': (
                            f"Platform conflict: Train {s1.train.train_number} and "
                            f"Train {s2.train.train_number} are both assigned to "
                            f"Platform {s1.platform.platform_number} at {s1.station.name}. "
                            f"Insufficient clearance time between departures."
                        ),
                    })

        return conflicts

    def _detect_crossing_conflicts(self, scheduled_date):
        """Detect opposing trains on single-line sections."""
        from apps.scheduling.models import Schedule
        from apps.stations.models import TrackSection

        conflicts = []
        # Get single-line sections
        single_line_sections = TrackSection.objects.filter(
            number_of_lines=1,
            is_active=True,
            status='CLEAR'
        )

        for section in single_line_sections:
            forward_schedules = list(
                Schedule.objects.filter(
                    scheduled_date=scheduled_date,
                    track_section=section,
                    status__in=['SCHEDULED', 'RUNNING', 'DELAYED']
                ).select_related('train')
            )

            if len(forward_schedules) >= 2:
                for i in range(len(forward_schedules)):
                    for j in range(i + 1, len(forward_schedules)):
                        s1, s2 = forward_schedules[i], forward_schedules[j]
                        if s1.train != s2.train and self._times_overlap(s1, s2, buffer=0):
                            conflicts.append({
                                'conflict_type': 'CROSSING',
                                'severity': 'CRITICAL',
                                'train_a': s1.train,
                                'train_b': s2.train,
                                'track_section': section,
                                'station': section.from_station,
                                'conflict_time': s1.scheduled_arrival or timezone.now(),
                                'description': (
                                    f"CRITICAL CROSSING CONFLICT: Single-line section {section.name} "
                                    f"has two trains scheduled simultaneously — "
                                    f"Train {s1.train.train_number} and Train {s2.train.train_number}. "
                                    f"Immediate action required to establish crossing order."
                                ),
                            })

        return conflicts

    def _detect_headway_violations(self, scheduled_date):
        """Detect insufficient headway between successive trains on same section."""
        from apps.scheduling.models import Schedule

        conflicts = []
        from apps.stations.models import TrackSection

        sections = TrackSection.objects.filter(is_active=True)

        for section in sections:
            section_schedules = list(
                Schedule.objects.filter(
                    scheduled_date=scheduled_date,
                    track_section=section,
                    status__in=['SCHEDULED', 'RUNNING', 'DELAYED'],
                    scheduled_arrival__isnull=False
                ).select_related('train').order_by('scheduled_arrival')
            )

            for i in range(len(section_schedules) - 1):
                s1, s2 = section_schedules[i], section_schedules[i + 1]
                if s1.train == s2.train:
                    continue

                if s1.scheduled_departure and s2.scheduled_arrival:
                    gap = (s2.scheduled_arrival - s1.scheduled_departure).total_seconds() / 60
                    if 0 < gap < self.MIN_HEADWAY_MINUTES:
                        conflicts.append({
                            'conflict_type': 'HEADWAY',
                            'severity': 'MEDIUM' if gap > 5 else 'HIGH',
                            'train_a': s1.train,
                            'train_b': s2.train,
                            'track_section': section,
                            'station': section.from_station,
                            'conflict_time': s2.scheduled_arrival,
                            'description': (
                                f"Headway violation on {section.name}: Only {gap:.0f} minutes "
                                f"gap between Train {s1.train.train_number} (departure) and "
                                f"Train {s2.train.train_number} (arrival). "
                                f"Minimum required: {self.MIN_HEADWAY_MINUTES} minutes."
                            ),
                        })

        return conflicts

    def _times_overlap(self, s1, s2, buffer=5):
        """Check if two schedule time windows overlap."""
        arr1 = s1.actual_arrival or s1.scheduled_arrival
        dep1 = s1.actual_departure or s1.scheduled_departure
        arr2 = s2.actual_arrival or s2.scheduled_arrival
        dep2 = s2.actual_departure or s2.scheduled_departure

        if not arr1 or not dep1 or not arr2 or not dep2:
            return False

        buf = timedelta(minutes=buffer)
        # Expand windows by buffer
        start1 = arr1 - buf
        end1 = dep1 + buf
        start2 = arr2 - buf
        end2 = dep2 + buf

        return not (end1 <= start2 or end2 <= start1)

    def _compute_severity(self, train_a, train_b, conflict_type):
        """Calculate conflict severity based on train priorities and type."""
        priority_sum = (train_a.priority_level or 3) + (train_b.priority_level or 3)

        base_severity = {
            'CROSSING': 'CRITICAL',
            'TRACK': 'HIGH',
            'PLATFORM': 'MEDIUM',
            'HEADWAY': 'MEDIUM',
            'OCCUPANCY': 'HIGH',
        }.get(conflict_type, 'MEDIUM')

        if conflict_type == 'CROSSING':
            return 'CRITICAL'

        if priority_sum >= 9:
            return 'CRITICAL'
        elif priority_sum >= 7 or base_severity == 'HIGH':
            return 'HIGH'
        elif priority_sum >= 5:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _persist_conflicts(self, detected_conflicts):
        """Save detected conflicts to database, avoiding duplicates."""
        from .models import Conflict
        from apps.notifications.services import NotificationService

        saved = []
        notif_service = NotificationService()

        for data in detected_conflicts:
            # Check for existing active conflict
            existing = Conflict.objects.filter(
                conflict_type=data['conflict_type'],
                train_a=data['train_a'],
                train_b=data.get('train_b'),
                status__in=['ACTIVE', 'ACKNOWLEDGED'],
            ).first()

            if existing:
                # Update severity if escalated
                if self._severity_level(data['severity']) > self._severity_level(existing.severity):
                    existing.severity = data['severity']
                    existing.save(update_fields=['severity'])
                saved.append(existing)
                continue

            conflict = Conflict.objects.create(
                conflict_type=data['conflict_type'],
                severity=data['severity'],
                status='ACTIVE',
                train_a=data['train_a'],
                train_b=data.get('train_b'),
                track_section=data.get('track_section'),
                platform=data.get('platform'),
                station=data.get('station'),
                conflict_time=data.get('conflict_time', timezone.now()),
                description=data['description'],
            )
            saved.append(conflict)

            # Create notification for active users
            notif_service.create_conflict_notification(conflict)

        return saved

    def _severity_level(self, severity_str):
        levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        return levels.get(severity_str, 0)

    def generate_conflict_report(self, from_date, to_date):
        """Generate conflict statistics for reporting."""
        from .models import Conflict
        from django.db.models import Count

        conflicts = Conflict.objects.filter(
            detected_at__date__gte=from_date,
            detected_at__date__lte=to_date,
        )

        report = {
            'total': conflicts.count(),
            'by_type': dict(conflicts.values('conflict_type').annotate(count=Count('id')).values_list('conflict_type', 'count')),
            'by_severity': dict(conflicts.values('severity').annotate(count=Count('id')).values_list('severity', 'count')),
            'by_status': dict(conflicts.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'resolved': conflicts.filter(status='RESOLVED').count(),
            'active': conflicts.filter(status='ACTIVE').count(),
            'resolution_rate': 0,
        }

        if report['total'] > 0:
            report['resolution_rate'] = round((report['resolved'] / report['total']) * 100, 1)

        return report
