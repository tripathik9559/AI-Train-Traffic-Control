"""
Management command: seed_demo_simulations
Creates realistic completed Simulation + SimulationResult records for demo/dev.

Usage:
    python manage.py seed_demo_simulations
    python manage.py seed_demo_simulations --count 10
    python manage.py seed_demo_simulations --clear
    python manage.py seed_demo_simulations --count 8 --clear
"""

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.simulation.models import Simulation, SimulationResult

User = get_user_model()


# ── Realistic seed data ────────────────────────────────────────────────────────

SCENARIO_CONFIGS = {
    'HEAVY_RAIN': {
        'delay_range': (20, 60),
        'duration_range': (2.0, 5.0),
        'throughput_range': (8.0, 30.0),
        'recovery_range': (45, 180),
        'recommendations': (
            "Reduce train speed to 60 km/h on all open-air sections\n"
            "Activate standby platforms at major junctions\n"
            "Issue passenger advisory for 30–60 min delays\n"
            "Pre-position maintenance crew at flood-prone sections\n"
            "Enable real-time weather overlay on dispatcher consoles"
        ),
    },
    'SIGNAL_FAILURE': {
        'delay_range': (15, 45),
        'duration_range': (1.0, 3.0),
        'throughput_range': (15.0, 40.0),
        'recovery_range': (30, 120),
        'recommendations': (
            "Switch affected block to manual token working immediately\n"
            "Halt all trains within 3 km of failure point\n"
            "Dispatch signal technician — ETA under 25 minutes\n"
            "Divert express trains via alternate loop route\n"
            "Notify adjacent station masters for hand-signal authorization"
        ),
    },
    'PLATFORM_FAILURE': {
        'delay_range': (10, 35),
        'duration_range': (1.0, 4.0),
        'throughput_range': (5.0, 20.0),
        'recovery_range': (20, 90),
        'recommendations': (
            "Reroute arriving trains to adjacent available platforms\n"
            "Coordinate passenger transfer via connecting walkways\n"
            "Hold departing trains by 8–12 minutes to clear backlog\n"
            "Deploy station staff for crowd management at affected zone\n"
            "Update PIS boards and mobile app with platform change alerts"
        ),
    },
    'MAINTENANCE_BLOCK': {
        'delay_range': (25, 70),
        'duration_range': (3.0, 8.0),
        'throughput_range': (10.0, 35.0),
        'recovery_range': (60, 240),
        'recommendations': (
            "Implement single-line working through maintenance block\n"
            "Re-schedule non-priority freight trains to off-peak window\n"
            "Advance crew rotation to complete work 2 hours early\n"
            "Enable temporary speed restriction signage at both ends\n"
            "Coordinate with adjacent division for extended block approval"
        ),
    },
    'ROUTE_CONGESTION': {
        'delay_range': (10, 30),
        'duration_range': (1.5, 4.0),
        'throughput_range': (5.0, 18.0),
        'recovery_range': (20, 75),
        'recommendations': (
            "Priority-clear express trains before local services\n"
            "Increase headway on congested corridor by 4 minutes\n"
            "Activate cross-platform interchange at key junctions\n"
            "Divert 2 freight trains to parallel route to ease capacity\n"
            "Monitor section occupancy every 90 seconds until clear"
        ),
    },
    'MASS_DELAY': {
        'delay_range': (30, 90),
        'duration_range': (2.0, 6.0),
        'throughput_range': (20.0, 55.0),
        'recovery_range': (90, 300),
        'recommendations': (
            "Identify and isolate broken-down train; clear track immediately\n"
            "Dispatch rescue locomotive from nearest yard\n"
            "Implement skip-stop pattern for following express services\n"
            "Issue mass SMS/app alerts with revised departure times\n"
            "Activate emergency bus bridges at affected stations"
        ),
    },
    'TRAIN_DELAY': {
        'delay_range': (15, 50),
        'duration_range': (1.0, 3.5),
        'throughput_range': (8.0, 25.0),
        'recovery_range': (25, 100),
        'recommendations': (
            "Grant line-clear priority to delayed train at next 3 signals\n"
            "Adjust following train headway to prevent compounding delays\n"
            "Notify connecting services to hold for 10 minutes\n"
            "Request speed-up authorization from divisional controller\n"
            "Log delay cause for root-cause analysis and reporting"
        ),
    },
}

RESULT_ACTIONS = [
    "Reroute via alternate corridor",
    "Platform reassignment executed",
    "Speed restriction lifted",
    "Held for crossing authorization",
    "Emergency stop — signal fault cleared",
    "Priority passage granted",
    "Cascaded delay absorbed — no further action",
    "Crew change expedited at junction",
    "Train merged into preceding slot",
    "Deferred to off-peak window",
]

STATUS_CHANGES = [
    "RUNNING → DELAYED",
    "SCHEDULED → DELAYED",
    "DELAYED → RUNNING",
    "RUNNING → HELD",
    "HELD → RUNNING",
    "SCHEDULED → CANCELLED",
]


class Command(BaseCommand):
    help = "Seed demo Simulation and SimulationResult records for development/demo."

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, default=5,
            help='Number of simulations to create (default: 5)',
        )
        parser.add_argument(
            '--clear', action='store_true', default=False,
            help='Delete all existing simulations before seeding',
        )

    def handle(self, *args, **options):
        count = options['count']
        do_clear = options['clear']

        # ── Resolve user ──────────────────────────────────────────────────
        user = (
            User.objects.filter(is_superuser=True).order_by('id').first()
            or User.objects.order_by('id').first()
        )
        if not user:
            self.stderr.write(self.style.ERROR(
                "No users found in the database. Create a superuser first:\n"
                "  python manage.py createsuperuser"
            ))
            return

        self.stdout.write(f"Using user: {user.username} (pk={user.pk})")

        # ── Optional clear ────────────────────────────────────────────────
        if do_clear:
            deleted, _ = Simulation.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing simulation(s)."))

        # ── Fetch real trains / stations (safe — may be empty) ────────────
        try:
            from apps.trains.models import Train
            active_trains = list(Train.objects.filter(is_active=True)[:30])
        except Exception:
            active_trains = []

        try:
            from apps.stations.models import Station
            active_stations = list(Station.objects.filter(is_active=True)[:20])
        except Exception:
            active_stations = []

        scenario_choices = list(Simulation.ScenarioType.choices)
        scenario_keys = [k for k, _ in scenario_choices]

        # ── Create simulations ────────────────────────────────────────────
        for i in range(count):
            stype = scenario_keys[i % len(scenario_keys)]
            cfg = SCENARIO_CONFIGS.get(stype, SCENARIO_CONFIGS['TRAIN_DELAY'])

            delay_min = random.randint(*cfg['delay_range'])
            duration_hrs = round(random.uniform(*cfg['duration_range']), 1)
            throughput_impact = round(random.uniform(*cfg['throughput_range']), 1)
            recovery_time = random.randint(*cfg['recovery_range'])

            started_at = timezone.now() - timedelta(
                hours=random.randint(1, 72),
                minutes=random.randint(0, 59),
            )
            completed_at = started_at + timedelta(hours=duration_hrs)

            trains_affected = random.randint(2, min(8, max(2, len(active_trains))))

            sim = Simulation.objects.create(
                name=f"Demo — {dict(scenario_choices)[stype]} #{i + 1}",
                scenario_type=stype,
                description=(
                    f"Seeded demonstration scenario: {dict(scenario_choices)[stype]}. "
                    f"Duration {duration_hrs}h, {delay_min} min delay injection, "
                    f"{trains_affected} trains affected."
                ),
                status='COMPLETED',
                delay_minutes=delay_min,
                duration_hours=duration_hrs,
                throughput_impact=throughput_impact,
                estimated_recovery_time=recovery_time,
                trains_affected_count=trains_affected,
                recommendations=cfg['recommendations'],
                result_summary=(
                    f"Scenario completed. {trains_affected} trains affected. "
                    f"Throughput reduced by {throughput_impact}%. "
                    f"Estimated recovery: {recovery_time} min."
                ),
                parameters={
                    'seed': True,
                    'scenario_index': i,
                    'delay_minutes': delay_min,
                    'duration_hours': duration_hrs,
                },
                created_by=user,
                started_at=started_at,
                completed_at=completed_at,
            )

            # ── Assign affected trains M2M ────────────────────────────────
            if active_trains:
                chosen_trains = random.sample(
                    active_trains,
                    min(trains_affected, len(active_trains)),
                )
                sim.affected_trains.set(chosen_trains)

            # ── Create 2–4 SimulationResult rows ─────────────────────────
            result_count = random.randint(2, 4)
            trains_for_results = (
                random.sample(active_trains, min(result_count, len(active_trains)))
                if active_trains else []
            )
            stations_for_results = (
                random.sample(active_stations, min(result_count, len(active_stations)))
                if active_stations else []
            )

            for j in range(result_count):
                train_obj = trains_for_results[j] if j < len(trains_for_results) else None
                station_obj = stations_for_results[j] if j < len(stations_for_results) else None

                simulated_delay = random.randint(
                    max(5, delay_min // 2),
                    delay_min + random.randint(5, 20),
                )
                cascaded_delay = random.randint(0, simulated_delay // 2)

                SimulationResult.objects.create(
                    simulation=sim,
                    train=train_obj,
                    station=station_obj,
                    simulated_delay=simulated_delay,
                    cascaded_delay=cascaded_delay,
                    platform_conflict=random.random() < 0.3,
                    track_conflict=random.random() < 0.25,
                    status_change=random.choice(STATUS_CHANGES),
                    recommended_action=random.choice(RESULT_ACTIONS),
                )

            self.stdout.write(self.style.SUCCESS(
                f"  [{i + 1}/{count}] Created: \"{sim.name}\" "
                f"| type={stype} | delay={delay_min}m "
                f"| throughput=-{throughput_impact}% | recovery={recovery_time}m "
                f"| results={result_count}"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Done — {count} simulation(s) seeded for user '{user.username}'.\n"
            f"   Run the dashboard at /simulation/ to see them live.\n"
            f"   To seed more:  python manage.py seed_demo_simulations --count 10\n"
            f"   To reset:      python manage.py seed_demo_simulations --clear --count 5"
        ))
