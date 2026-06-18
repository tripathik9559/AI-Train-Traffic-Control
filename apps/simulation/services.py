"""
Scenario Simulation Engine
Runs railway disruption scenarios and computes expected impacts.
"""

import random
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


class ScenarioSimulator:
    """Executes simulation scenarios and computes cascading impacts."""

    SCENARIO_CONFIGS = {
        'TRAIN_DELAY': {
            'base_multiplier': 1.0,
            'cascade_factor': 0.4,
            'throughput_hit': 15,
            'recovery_factor': 0.8,
        },
        'PLATFORM_FAILURE': {
            'base_multiplier': 1.5,
            'cascade_factor': 0.6,
            'throughput_hit': 30,
            'recovery_factor': 1.2,
        },
        'MAINTENANCE_BLOCK': {
            'base_multiplier': 2.0,
            'cascade_factor': 0.8,
            'throughput_hit': 50,
            'recovery_factor': 1.5,
        },
        'SIGNAL_FAILURE': {
            'base_multiplier': 2.5,
            'cascade_factor': 0.9,
            'throughput_hit': 60,
            'recovery_factor': 2.0,
        },
        'HEAVY_RAIN': {
            'base_multiplier': 1.8,
            'cascade_factor': 0.7,
            'throughput_hit': 40,
            'recovery_factor': 1.0,
        },
        'ROUTE_CONGESTION': {
            'base_multiplier': 1.3,
            'cascade_factor': 0.5,
            'throughput_hit': 25,
            'recovery_factor': 0.9,
        },
        'MASS_DELAY': {
            'base_multiplier': 3.0,
            'cascade_factor': 1.0,
            'throughput_hit': 70,
            'recovery_factor': 2.5,
        },
        'CUSTOM': {
            'base_multiplier': 1.0,
            'cascade_factor': 0.5,
            'throughput_hit': 20,
            'recovery_factor': 1.0,
        },
    }

    def run(self, simulation):
        """Execute a simulation and populate results."""
        from .models import SimulationResult
        from apps.trains.models import Train

        simulation.status = 'RUNNING'
        simulation.started_at = timezone.now()
        simulation.save(update_fields=['status', 'started_at'])

        config = self.SCENARIO_CONFIGS.get(simulation.scenario_type, self.SCENARIO_CONFIGS['CUSTOM'])
        base_delay = simulation.delay_minutes

        # Get affected trains
        affected_trains = list(simulation.affected_trains.all())
        if not affected_trains:
            affected_trains = list(Train.objects.filter(
                is_active=True,
                current_status__in=['SCHEDULED', 'RUNNING', 'DELAYED']
            )[:12])

        results = []
        total_cascade_delay = 0

        for i, train in enumerate(affected_trains):
            primary_delay = base_delay * config['base_multiplier']
            primary_delay += random.uniform(-5, 10)
            primary_delay = max(0, primary_delay)

            cascade_delay = 0
            if i > 0:
                cascade_delay = primary_delay * config['cascade_factor'] * (1 - i * 0.08)
                cascade_delay = max(0, cascade_delay)

            total_cascade_delay += cascade_delay

            platform_conflict = random.random() < (config['throughput_hit'] / 150)
            track_conflict = random.random() < (config['throughput_hit'] / 200)

            action = self._recommend_action(
                train, simulation.scenario_type, primary_delay, cascade_delay,
                platform_conflict, track_conflict
            )

            result = SimulationResult.objects.create(
                simulation=simulation,
                train=train,
                simulated_delay=int(primary_delay),
                cascaded_delay=int(cascade_delay),
                status_change='DELAYED' if primary_delay > 5 else 'ON_TIME',
                platform_conflict=platform_conflict,
                track_conflict=track_conflict,
                recommended_action=action,
            )
            results.append(result)

        # Compute overall impact
        throughput_reduction = config['throughput_hit'] + random.uniform(-5, 5)
        throughput_reduction = min(95, max(0, throughput_reduction))

        recovery_time = int(
            base_delay * config['recovery_factor'] * len(affected_trains) * 0.15
        )
        recovery_time = max(10, recovery_time)

        summary = self._build_summary(simulation, results, throughput_reduction, recovery_time)
        recovery_actions = self._build_recovery_plan(simulation.scenario_type, results)

        simulation.status = 'COMPLETED'
        simulation.completed_at = timezone.now()
        simulation.throughput_impact = round(throughput_reduction, 1)
        simulation.trains_affected_count = len(affected_trains)
        simulation.estimated_recovery_time = recovery_time
        simulation.result_summary = summary
        simulation.recommendations = recovery_actions
        simulation.save()

        return simulation, results

    def _recommend_action(self, train, scenario_type, primary_delay, cascade_delay,
                          platform_conflict, track_conflict):
        """Generate per-train recommended action."""
        actions = []

        if primary_delay > 30:
            actions.append(f"Hold Train {train.train_number} at next loop station for {int(primary_delay/2)} minutes.")

        if platform_conflict:
            actions.append(f"Reassign platform for Train {train.train_number} to avoid conflict.")

        if track_conflict:
            actions.append(f"Coordinate crossing order — Train {train.train_number} gives way to higher-priority service.")

        if scenario_type == 'SIGNAL_FAILURE':
            actions.append("Operate under caution — proceed at restricted speed with pilot.")
        elif scenario_type == 'HEAVY_RAIN':
            actions.append(f"Reduce speed to 30 km/h on affected section.")
        elif scenario_type == 'PLATFORM_FAILURE':
            actions.append(f"Divert to alternate platform. Announce to passengers.")
        elif scenario_type == 'MAINTENANCE_BLOCK':
            actions.append("Reroute via alternate line if available. Else queue at block limit.")

        if cascade_delay > 15:
            actions.append(f"Expect {int(cascade_delay)} min cascade delay — adjust downstream connections.")

        return ' | '.join(actions) if actions else "No immediate action required. Monitor status."

    def _build_summary(self, simulation, results, throughput_reduction, recovery_time):
        """Build textual result summary."""
        total_delay = sum(r.simulated_delay for r in results)
        conflicts = sum(1 for r in results if r.platform_conflict or r.track_conflict)

        lines = [
            f"SIMULATION RESULT — {simulation.name}",
            f"Scenario: {simulation.get_scenario_type_display()}",
            f"",
            f"• Trains Affected: {len(results)}",
            f"• Total Simulated Delay: {total_delay} minutes",
            f"• Average Delay Per Train: {total_delay / max(len(results), 1):.1f} minutes",
            f"• Throughput Reduction: {throughput_reduction:.1f}%",
            f"• Conflicts Detected: {conflicts}",
            f"• Estimated Recovery Time: {recovery_time} minutes",
            f"",
            f"Simulation completed at {timezone.now().strftime('%H:%M:%S')}",
        ]
        return '\n'.join(lines)

    def _build_recovery_plan(self, scenario_type, results):
        """Generate recovery action plan."""
        plans = {
            'SIGNAL_FAILURE': [
                "1. Deploy track patrolling staff immediately.",
                "2. Issue Block Working instructions to all trains in section.",
                "3. Notify divisional control and signal engineer.",
                "4. Maintain 20-minute headway until signal restored.",
                "5. Prepare list of trains for priority clearance on restoration.",
            ],
            'PLATFORM_FAILURE': [
                "1. Identify alternate platforms for each displaced train.",
                "2. Update departure boards and PA announcements.",
                "3. Coordinate with RPF for crowd management.",
                "4. Issue crew change orders if trains miss scheduled times.",
            ],
            'HEAVY_RAIN': [
                "1. Enforce speed restrictions: 30 km/h on flood-prone sections.",
                "2. Activate rain gauge monitoring protocol.",
                "3. Suspend operations on vulnerable bridges pending inspection.",
                "4. Coordinate rescue trains if passenger trains are stranded.",
            ],
            'MAINTENANCE_BLOCK': [
                "1. Confirm block start/end times with maintenance team.",
                "2. Reschedule affected trains via alternate routes.",
                "3. Issue revised timetable to all controllers.",
                "4. Pre-position trains at block limits for rapid clearance.",
            ],
            'ROUTE_CONGESTION': [
                "1. Implement traffic regulation — hold lower priority trains.",
                "2. Optimize crossing orders using AI priority engine.",
                "3. Identify and use all available loop/yard capacity.",
                "4. Coordinate with adjacent divisions for end-to-end recovery.",
            ],
        }

        steps = plans.get(scenario_type, [
            "1. Assess extent of disruption and affected trains.",
            "2. Prioritize high-value services for clearance.",
            "3. Issue delay notifications to all stakeholders.",
            "4. Monitor situation and update control every 15 minutes.",
        ])

        return '\n'.join(steps)
