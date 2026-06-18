"""
Seed Data Management Command
Populates the database with realistic Indian Railways sample data
covering stations, routes, track sections, trains, schedules, and conflicts.
"""

import random
from datetime import date, time, timedelta, datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    help = 'Seed the database with realistic Indian Railways demonstration data'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self._clear_data()

        self.stdout.write(self.style.MIGRATE_HEADING('🚂 Seeding Railway Control System...'))

        self._create_users()
        self._create_stations()
        self._create_platforms()
        self._create_routes()
        self._create_track_sections()
        self._create_trains()
        self._create_schedules()
        self._create_conflicts()
        self._create_notifications()

        self.stdout.write(self.style.SUCCESS('\n✅ Seed data loaded successfully!\n'))
        self.stdout.write('  Admin login: admin / Admin@2024')
        self.stdout.write('  Controller login: controller1 / Pass@2024\n')

    def _clear_data(self):
        from apps.conflicts.models import Conflict, Recommendation
        from apps.scheduling.models import Schedule, TrackOccupancy
        from apps.trains.models import Train
        from apps.stations.models import Station, Platform, Route, TrackSection
        from apps.notifications.models import Notification
        from apps.ml_prediction.models import DelayPrediction

        Recommendation.objects.all().delete()
        Conflict.objects.all().delete()
        TrackOccupancy.objects.all().delete()
        Schedule.objects.all().delete()
        DelayPrediction.objects.all().delete()
        Notification.objects.all().delete()
        Train.objects.all().delete()
        Platform.objects.all().delete()
        Route.objects.all().delete()
        TrackSection.objects.all().delete()
        Station.objects.all().delete()

    def _create_users(self):
        from apps.authentication.models import User

        if not User.objects.filter(username='admin').exists():
            User.objects.create(
                username='admin', email='admin@railwaycontrol.in',
                first_name='System', last_name='Administrator',
                role='ADMIN', employee_id='EMP000',
                department='IT Administration',
                is_staff=True, is_superuser=True, is_active=True,
                password=make_password('Admin@2024'),
            )
            self.stdout.write('  ✓ Admin user created')

        controllers = [
            ('controller1', 'Ravi', 'Shankar', 'LKO-CNB'),
            ('controller2', 'Priya', 'Mehta', 'CNB-MGS'),
            ('controller3', 'Amit', 'Verma', 'MGS-PNBE'),
        ]
        for uname, fname, lname, section in controllers:
            if not User.objects.filter(username=uname).exists():
                idx = controllers.index((uname, fname, lname, section)) + 1
                User.objects.create(
                    username=uname, email=f'{uname}@railwaycontrol.in',
                    first_name=fname, last_name=lname,
                    role='SECTION_CONTROLLER',
                    employee_id=f'EMP{idx:03d}',
                    department='Operations',
                    section_assigned=section,
                    is_active=True,
                    is_on_duty=True,
                    password=make_password('Pass@2024'),
                )
        self.stdout.write('  ✓ Controller users created')

    def _create_stations(self):
        from apps.stations.models import Station

        stations_data = [
            ('Lucknow Charbagh', 'LKO', 'MAJOR', 'Lucknow', 'Uttar Pradesh', 'NR', 'Lucknow', 26.8467, 80.9462, 9, True),
            ('Kanpur Central', 'CNB', 'JUNCTION', 'Kanpur', 'Uttar Pradesh', 'NCR', 'Allahabad', 26.4609, 80.3319, 10, True),
            ('Allahabad Junction', 'ALD', 'JUNCTION', 'Allahabad', 'Uttar Pradesh', 'NCR', 'Allahabad', 25.4358, 81.8463, 10, True),
            ('Mughal Sarai Junction', 'MGS', 'JUNCTION', 'Chandauli', 'Uttar Pradesh', 'ECR', 'Varanasi', 25.2833, 83.1167, 12, True),
            ('Patna Junction', 'PNBE', 'MAJOR', 'Patna', 'Bihar', 'ECR', 'Patna', 25.5941, 85.1376, 10, True),
            ('Varanasi Junction', 'BSB', 'JUNCTION', 'Varanasi', 'Uttar Pradesh', 'NER', 'Varanasi', 25.3176, 82.9739, 8, True),
            ('New Delhi', 'NDLS', 'TERMINAL', 'New Delhi', 'Delhi', 'NR', 'Delhi', 28.6424, 77.2194, 16, True),
            ('Agra Cantt', 'AGC', 'JUNCTION', 'Agra', 'Uttar Pradesh', 'NCR', 'Agra', 27.1591, 77.9858, 6, True),
            ('Gwalior', 'GWL', 'JUNCTION', 'Gwalior', 'Madhya Pradesh', 'NCR', 'Jhansi', 26.2183, 78.1828, 5, False),
            ('Etawah', 'ETW', 'CROSSING', 'Etawah', 'Uttar Pradesh', 'NCR', 'Allahabad', 26.7805, 79.0169, 3, False),
            ('Faridabad', 'FBD', 'HALT', 'Faridabad', 'Haryana', 'NR', 'Delhi', 28.4089, 77.3178, 4, False),
            ('Mathura Junction', 'MTJ', 'JUNCTION', 'Mathura', 'Uttar Pradesh', 'NCR', 'Agra', 27.4924, 77.6737, 6, True),
        ]

        for name, code, stype, city, state, zone, div, lat, lng, platforms, is_junc in stations_data:
            Station.objects.get_or_create(
                code=code,
                defaults=dict(
                    name=name, station_type=stype, city=city, state=state,
                    zone=zone, division=div, latitude=lat, longitude=lng,
                    total_platforms=platforms, is_junction=is_junc, is_active=True,
                )
            )
        self.stdout.write(f'  ✓ {len(stations_data)} stations created')

    def _create_platforms(self):
        from apps.stations.models import Station, Platform

        pf_created = 0
        for station in Station.objects.filter(is_active=True):
            for i in range(1, station.total_platforms + 1):
                pf, created = Platform.objects.get_or_create(
                    station=station, platform_number=str(i),
                    defaults=dict(
                        platform_type='BOTH',
                        length=random.choice([400, 500, 550, 600, 700]),
                        status=random.choice(['AVAILABLE', 'AVAILABLE', 'AVAILABLE', 'OCCUPIED']),
                        has_shelter=True, is_active=True,
                    )
                )
                if created:
                    pf_created += 1
        self.stdout.write(f'  ✓ {pf_created} platforms created')

    def _create_routes(self):
        from apps.stations.models import Station, Route

        routes_data = [
            ('NDLS-LKO Route', 'NDLS', 'LKO', 497, 330, 130),
            ('LKO-CNB Route', 'LKO', 'CNB', 80, 60, 110),
            ('CNB-ALD Route', 'CNB', 'ALD', 190, 130, 120),
            ('ALD-MGS Route', 'ALD', 'MGS', 155, 110, 110),
            ('MGS-PNBE Route', 'MGS', 'PNBE', 205, 150, 120),
            ('NDLS-AGC Route', 'NDLS', 'AGC', 200, 120, 160),
            ('AGC-GWL Route', 'AGC', 'GWL', 120, 85, 130),
            ('LKO-BSB Route', 'LKO', 'BSB', 320, 210, 110),
            ('NDLS-MTJ Route', 'NDLS', 'MTJ', 141, 100, 130),
            ('MTJ-AGC Route', 'MTJ', 'AGC', 58, 45, 110),
        ]

        created = 0
        for name, src_code, dst_code, dist, dur, spd in routes_data:
            try:
                src = Station.objects.get(code=src_code)
                dst = Station.objects.get(code=dst_code)
                Route.objects.get_or_create(
                    source_station=src, destination_station=dst,
                    defaults=dict(
                        name=name, distance=dist, estimated_duration=dur,
                        max_speed=spd, is_electrified=True, is_double_line=True, is_active=True,
                    )
                )
                created += 1
            except Station.DoesNotExist:
                pass
        self.stdout.write(f'  ✓ {created} routes created')

    def _create_track_sections(self):
        from apps.stations.models import Station, TrackSection

        sections_data = [
            ('LKO-ETW Section', 'LKO-ETW-01', 'LKO', 'ETW', 110, 2, 110, 2),
            ('ETW-CNB Section', 'ETW-CNB-01', 'ETW', 'CNB', 70, 2, 120, 2),
            ('CNB-ALD Section', 'CNB-ALD-01', 'CNB', 'ALD', 190, 2, 120, 2),
            ('ALD-MGS Section', 'ALD-MGS-01', 'ALD', 'MGS', 155, 2, 110, 2),
            ('MGS-PNBE Section', 'MGS-PNBE-01', 'MGS', 'PNBE', 205, 2, 120, 2),
            ('NDLS-MTJ Section', 'NDLS-MTJ-01', 'NDLS', 'MTJ', 141, 4, 160, 4),
            ('MTJ-AGC Section', 'MTJ-AGC-01', 'MTJ', 'AGC', 58, 2, 130, 2),
            ('AGC-GWL Section', 'AGC-GWL-01', 'AGC', 'GWL', 120, 2, 130, 2),
            ('LKO-BSB Loop', 'LKO-BSB-01', 'LKO', 'BSB', 150, 1, 100, 1),
            ('NDLS-FBD Section', 'NDLS-FBD-01', 'NDLS', 'FBD', 30, 4, 160, 6),
        ]

        statuses = ['CLEAR', 'CLEAR', 'CLEAR', 'CLEAR', 'OCCUPIED', 'MAINTENANCE']
        created = 0
        for name, code, from_code, to_code, length, lines, spd, cap in sections_data:
            try:
                from_st = Station.objects.get(code=from_code)
                to_st = Station.objects.get(code=to_code)
                TrackSection.objects.get_or_create(
                    code=code,
                    defaults=dict(
                        name=name, from_station=from_st, to_station=to_st,
                        length=length, number_of_lines=lines, max_speed=spd,
                        capacity=cap, status=random.choice(statuses),
                        is_electrified=True, is_active=True,
                    )
                )
                created += 1
            except Station.DoesNotExist:
                pass
        self.stdout.write(f'  ✓ {created} track sections created')

    def _create_trains(self):
        from apps.trains.models import Train
        from apps.stations.models import Station
        from apps.authentication.models import User

        admin = User.objects.filter(username='admin').first()

        trains_data = [
            ('12301', 'Howrah Rajdhani', 'RAJDHANI', 130, 5, 'NDLS', 'PNBE', 'RUNNING', 0),
            ('12309', 'Rajendra Nagar Rajdhani', 'RAJDHANI', 130, 5, 'NDLS', 'PNBE', 'DELAYED', 25),
            ('12003', 'LKO Shatabdi', 'SHATABDI', 150, 4, 'NDLS', 'LKO', 'RUNNING', 5),
            ('12559', 'Shiv Ganga Express', 'EXPRESS', 110, 3, 'NDLS', 'BSB', 'SCHEDULED', 0),
            ('15017', 'LKO Gorakhpur Express', 'EXPRESS', 100, 3, 'LKO', 'GKP', 'DELAYED', 40),
            ('12275', 'Allahabad Duronto', 'DURONTO', 120, 4, 'NDLS', 'ALD', 'RUNNING', 0),
            ('12393', 'Sampoorna Kranti', 'EXPRESS', 110, 4, 'NDLS', 'PNBE', 'DELAYED', 15),
            ('22435', 'Vande Bharat Express', 'VANDE_BHARAT', 160, 5, 'NDLS', 'LKO', 'RUNNING', 0),
            ('14015', 'Sadhbhavna Express', 'MAIL', 90, 2, 'NDLS', 'BSB', 'SCHEDULED', 0),
            ('53505', 'Patna Passenger', 'PASSENGER', 70, 1, 'PNBE', 'MGS', 'SCHEDULED', 0),
            ('11123', 'Bandra Faizabad', 'EXPRESS', 100, 3, 'LKO', 'ALD', 'RUNNING', 10),
            ('14235', 'BSB Express', 'EXPRESS', 100, 3, 'LKO', 'BSB', 'HELD', 20),
            ('58101', 'CNB Freight', 'FREIGHT', 60, 1, 'CNB', 'ALD', 'RUNNING', 5),
            ('12419', 'Gomti Express', 'EXPRESS', 110, 3, 'LKO', 'NDLS', 'RUNNING', 0),
            ('12483', 'Amritsar Express', 'EXPRESS', 110, 3, 'LKO', 'NDLS', 'DELAYED', 30),
        ]

        created = 0
        for number, name, ttype, speed, priority, src, dst, status, delay in trains_data:
            try:
                src_st = Station.objects.filter(code=src).first()
                dst_st = Station.objects.filter(code=dst).first()
                train, c = Train.objects.get_or_create(
                    train_number=number,
                    defaults=dict(
                        train_name=name, train_type=ttype, speed=speed,
                        priority_level=priority,
                        source_station=src_st, destination_station=dst_st,
                        current_status=status, current_delay=delay,
                        total_coaches=random.choice([12, 16, 20, 22, 24]),
                        days_of_operation='Daily',
                        is_active=True, created_by=admin,
                    )
                )
                if c:
                    created += 1
            except Exception as e:
                self.stderr.write(f'    Train {number} error: {e}')

        self.stdout.write(f'  ✓ {created} trains created')

    def _create_schedules(self):
        from apps.scheduling.models import Schedule
        from apps.trains.models import Train
        from apps.stations.models import Station, Platform

        trains = list(Train.objects.filter(is_active=True))
        today = date.today()
        stations = list(Station.objects.filter(is_active=True))
        created = 0

        for train in trains[:10]:
            route_stations = [train.source_station] if train.source_station else []
            mid_stations = random.sample([s for s in stations if s not in route_stations], min(3, len(stations)))
            route_stations.extend(mid_stations)
            if train.destination_station and train.destination_station not in route_stations:
                route_stations.append(train.destination_station)

            base_time = timezone.make_aware(datetime.combine(today, time(random.randint(4, 22), 0)))

            for seq, station in enumerate(route_stations, 1):
                base_time = base_time + timedelta(minutes=random.randint(45, 120))
                dep_time = base_time + timedelta(minutes=random.choice([2, 3, 5, 10]))

                platform = Platform.objects.filter(station=station, is_active=True).first()

                status_choice = 'SCHEDULED'
                if train.current_status == 'RUNNING':
                    status_choice = random.choice(['RUNNING', 'DEPARTED', 'ARRIVED'])
                elif train.current_status == 'DELAYED':
                    status_choice = 'DELAYED'

                Schedule.objects.get_or_create(
                    train=train, station=station, scheduled_date=today,
                    stop_sequence=seq,
                    defaults=dict(
                        platform=platform,
                        scheduled_arrival=base_time if seq > 1 else None,
                        scheduled_departure=dep_time,
                        halt_duration=random.choice([2, 3, 5, 10]),
                        current_delay=train.current_delay,
                        status=status_choice,
                        is_originating=(seq == 1),
                        is_terminating=(seq == len(route_stations)),
                    )
                )
                created += 1

        self.stdout.write(f'  ✓ {created} schedule entries created')

    def _create_conflicts(self):
        from apps.conflicts.models import Conflict
        from apps.trains.models import Train
        from apps.stations.models import Station, TrackSection

        trains = list(Train.objects.filter(is_active=True))
        stations = list(Station.objects.filter(is_active=True))
        sections = list(TrackSection.objects.filter(is_active=True))

        if len(trains) < 2:
            return

        conflicts_data = [
            ('TRACK', 'HIGH', 'ACTIVE'),
            ('PLATFORM', 'MEDIUM', 'ACTIVE'),
            ('CROSSING', 'CRITICAL', 'ACTIVE'),
            ('HEADWAY', 'MEDIUM', 'ACKNOWLEDGED'),
            ('TRACK', 'HIGH', 'RESOLVED'),
            ('PLATFORM', 'LOW', 'RESOLVED'),
        ]

        created = 0
        for ctype, severity, status in conflicts_data:
            t_a = random.choice(trains)
            t_b = random.choice([t for t in trains if t != t_a])
            station = random.choice(stations) if stations else None
            section = random.choice(sections) if sections else None

            conflict_time = timezone.now() - timedelta(hours=random.randint(0, 24))

            desc_map = {
                'TRACK': f"Track conflict: {t_a.train_number} and {t_b.train_number} on same section.",
                'PLATFORM': f"Platform conflict at {station.name if station else 'unknown'}: {t_a.train_number} vs {t_b.train_number}.",
                'CROSSING': f"CRITICAL: Single-line crossing conflict — {t_a.train_number} vs {t_b.train_number}.",
                'HEADWAY': f"Headway violation: Only 6 min gap between {t_a.train_number} and {t_b.train_number}.",
            }

            c = Conflict.objects.create(
                conflict_type=ctype, severity=severity, status=status,
                train_a=t_a, train_b=t_b,
                station=station, track_section=section,
                conflict_time=conflict_time,
                description=desc_map.get(ctype, 'Conflict detected.'),
            )
            if status == 'RESOLVED':
                c.resolved_at = timezone.now()
                c.save(update_fields=['resolved_at'])
            created += 1

        self.stdout.write(f'  ✓ {created} conflicts created')

    def _create_notifications(self):
        from apps.notifications.models import Notification

        notifications = [
            ('CONFLICT', 'CRITICAL', '🚨 Critical Track Conflict Detected', 'Train 12301 and 12309 are on the same section. Immediate action required.', '/conflicts/'),
            ('DELAY', 'HIGH', 'Train 15017 Delayed — 40 min', 'LKO Gorakhpur Express is running 40 minutes behind schedule.', '/trains/'),
            ('RECOMMENDATION', 'NORMAL', '🤖 AI Recommendation Available', 'Priority analysis complete for LKO-CNB crossing. View recommendation.', '/ai-engine/'),
            ('SYSTEM', 'NORMAL', 'ML Model Retrained', 'Delay prediction model retrained with 5000 samples. R² = 0.87.', '/ml-prediction/'),
            ('INFO', 'LOW', 'Scheduled Maintenance', 'LKO-BSB-01 section scheduled for maintenance tomorrow 06:00–08:00.', '/stations/sections/'),
        ]

        for ntype, priority, title, msg, link in notifications:
            Notification.objects.get_or_create(
                title=title,
                defaults=dict(
                    notification_type=ntype, priority=priority,
                    message=msg, link=link, is_broadcast=True,
                )
            )
        self.stdout.write(f'  ✓ {len(notifications)} notifications created')
