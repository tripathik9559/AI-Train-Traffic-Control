"""
AI-Assisted Priority Engine
Calculates priority scores for trains and generates intelligent recommendations
for conflict resolution, crossing orders, and operational optimization.
"""

import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


class PriorityEngine:
    """
    AI-Assisted train priority calculation engine.

    Uses a multi-factor weighted scoring algorithm to determine
    train precedence at conflicts and crossing points.
    """

    # Weight distribution (must sum to 1.0)
    WEIGHTS = {
        'train_type': 0.30,
        'delay_urgency': 0.25,
        'speed_capability': 0.15,
        'operational_priority': 0.20,
        'route_importance': 0.10,
    }

    # Train type base scores (0-10)
    TYPE_SCORES = {
        'VANDE_BHARAT': 10,
        'RAJDHANI': 10,
        'SHATABDI': 9,
        'DURONTO': 9,
        'SPECIAL': 8,
        'EXPRESS': 7,
        'MAIL': 5,
        'PASSENGER': 3,
        'FREIGHT': 2,
    }

    def calculate_priority(self, train, schedule=None):
        """
        Calculate comprehensive priority score for a single train.

        Returns:
            dict: Score breakdown, total score, recommendation action
        """
        scores = {}
        explanations = {}

        # === Factor 1: Train Type (0-10) ===
        type_score = self.TYPE_SCORES.get(train.train_type, 5)
        scores['train_type'] = type_score
        explanations['train_type'] = (
            f"{train.get_train_type_display()} gets type score of {type_score}/10. "
            f"Premium trains (Rajdhani, Vande Bharat) receive highest precedence."
        )

        # === Factor 2: Delay Urgency (0-10) ===
        delay_minutes = 0
        if schedule and schedule.current_delay:
            delay_minutes = schedule.current_delay
        elif train.current_delay:
            delay_minutes = train.current_delay

        if delay_minutes >= 60:
            delay_score = 10
            delay_label = "severely delayed"
        elif delay_minutes >= 30:
            delay_score = 8
            delay_label = "significantly delayed"
        elif delay_minutes >= 15:
            delay_score = 6
            delay_label = "moderately delayed"
        elif delay_minutes >= 5:
            delay_score = 4
            delay_label = "slightly delayed"
        elif delay_minutes < 0:
            delay_score = 0
            delay_label = "running early"
        else:
            delay_score = 1
            delay_label = "on time"

        scores['delay_urgency'] = delay_score
        explanations['delay_urgency'] = (
            f"Train is {delay_label} ({delay_minutes:+d} minutes). "
            f"Delay urgency score: {delay_score}/10."
        )

        # === Factor 3: Speed Capability (0-10) ===
        max_speed = train.speed or 100
        speed_score = min(10, max_speed / 18)  # 180 km/h → 10
        scores['speed_capability'] = round(speed_score, 2)
        explanations['speed_capability'] = (
            f"Train max speed: {max_speed} km/h. "
            f"Speed capability score: {speed_score:.1f}/10."
        )

        # === Factor 4: Operational Priority (0-10) ===
        op_priority = (train.priority_level or 3) * 2  # Scale 1-5 → 2-10
        scores['operational_priority'] = op_priority
        explanations['operational_priority'] = (
            f"Operational priority level: {train.priority_level}/5. "
            f"Normalized score: {op_priority}/10."
        )

        # === Factor 5: Route Importance (0-10) ===
        route_score = self._calculate_route_importance(train)
        scores['route_importance'] = route_score
        explanations['route_importance'] = (
            f"Route importance score: {route_score}/10 "
            f"(based on connectivity and strategic significance)."
        )

        # === Calculate Weighted Total ===
        total = sum(
            scores[factor] * self.WEIGHTS[factor]
            for factor in self.WEIGHTS
        )
        total = round(total, 2)

        # === Generate Action Recommendation ===
        action, action_detail, action_color = self._generate_action(total, train, delay_minutes)

        return {
            'train': train,
            'total_score': total,
            'max_possible': 10.0,
            'score_percentage': round(total * 10, 1),
            'scores': scores,
            'weights': self.WEIGHTS,
            'explanations': explanations,
            'action': action,
            'action_detail': action_detail,
            'action_color': action_color,
            'delay_minutes': delay_minutes,
        }

    def _calculate_route_importance(self, train):
        """Estimate route importance based on source/destination."""
        score = 5  # Default mid-range

        if train.source_station and train.destination_station:
            # Major city pairs get higher scores
            major_stations = {'NDLS', 'BCT', 'HWH', 'MAS', 'CSTM', 'SBC', 'HYB', 'PUNE', 'ADI'}
            src_major = train.source_station.code in major_stations
            dst_major = train.destination_station.code in major_stations

            if src_major and dst_major:
                score = 9
            elif src_major or dst_major:
                score = 7
            else:
                score = 5

        return score

    def _generate_action(self, score, train, delay_minutes):
        """Generate recommended action based on priority score."""
        if score >= 8.5:
            return (
                'IMMEDIATE PRIORITY',
                f"Train {train.train_number} requires immediate precedence. "
                f"Clear all crossings and hold lower-priority trains. "
                f"This is a premium service with critical operational status.",
                '#e74c3c'
            )
        elif score >= 7.0:
            return (
                'HIGH PRIORITY',
                f"Train {train.train_number} should receive priority passing. "
                f"Hold mail/passenger trains to allow this express service to proceed first. "
                f"{'Urgency increased due to existing delay.' if delay_minutes > 10 else ''}",
                '#e67e22'
            )
        elif score >= 5.5:
            return (
                'NORMAL OPERATION',
                f"Train {train.train_number} follows standard scheduling protocol. "
                f"No special precedence required. Maintain regular headway.",
                '#3498db'
            )
        elif score >= 3.5:
            return (
                'LOW PRIORITY — CAN HOLD',
                f"Train {train.train_number} can be held for up to 15 minutes "
                f"to allow higher-priority trains to pass. "
                f"Inform passengers of expected delay.",
                '#f39c12'
            )
        else:
            return (
                'DEFER',
                f"Train {train.train_number} should give way to all other trains. "
                f"Consider holding at nearest loop/yard. "
                f"Coordinate with control for rescheduling.",
                '#95a5a6'
            )

    def rank_at_conflict(self, trains, schedules_map=None):
        """
        Rank multiple trains at a conflict point.

        Args:
            trains: List of Train objects
            schedules_map: Dict mapping train.id → Schedule object

        Returns:
            Sorted list of priority results, highest first
        """
        results = []
        for train in trains:
            schedule = (schedules_map or {}).get(train.id)
            result = self.calculate_priority(train, schedule)
            results.append(result)

        results.sort(key=lambda x: x['total_score'], reverse=True)

        # Add rank
        for i, result in enumerate(results):
            result['rank'] = i + 1
            if i == 0:
                result['rank_label'] = '🚀 FIRST PRIORITY'
                result['rank_color'] = '#2ecc71'
            elif i == 1:
                result['rank_label'] = '⚡ SECOND PRIORITY'
                result['rank_color'] = '#3498db'
            elif i == 2:
                result['rank_label'] = '⏸ THIRD PRIORITY'
                result['rank_color'] = '#f39c12'
            else:
                result['rank_label'] = '🛑 HOLD'
                result['rank_color'] = '#e74c3c'

        return results

    def generate_recommendations_for_conflict(self, conflict):
        """Generate AI recommendations for a specific conflict."""
        from apps.conflicts.models import Recommendation

        trains = [conflict.train_a]
        if conflict.train_b:
            trains.append(conflict.train_b)

        if not trains:
            return []

        ranked = self.rank_at_conflict(trains)
        recommendations = []

        if len(ranked) >= 2:
            winner = ranked[0]
            loser = ranked[1]

            # Primary recommendation: crossing order
            rec = Recommendation.objects.create(
                conflict=conflict,
                recommendation_type='PRIORITY',
                primary_train=winner['train'],
                secondary_train=loser['train'] if len(ranked) > 1 else None,
                title=f"Priority Order: {winner['train'].train_number} before {loser['train'].train_number}",
                description=(
                    f"Based on AI analysis, Train {winner['train'].train_number} "
                    f"({winner['train'].train_name}) should proceed first with a priority "
                    f"score of {winner['total_score']}/10, while Train {loser['train'].train_number} "
                    f"({loser['train'].train_name}, score: {loser['total_score']}/10) should hold."
                ),
                reasoning=self._build_reasoning(winner, loser),
                priority_score=winner['total_score'],
                confidence=min(0.99, 0.70 + (winner['total_score'] - loser['total_score']) * 0.05),
                estimated_benefit=f"Expected to save {int((loser['total_score'] / 10) * 15)} minutes of cascade delay.",
            )
            recommendations.append(rec)

            # Secondary: hold recommendation for loser
            hold_rec = Recommendation.objects.create(
                conflict=conflict,
                recommendation_type='HOLD',
                primary_train=loser['train'],
                secondary_train=winner['train'],
                title=f"Hold Train {loser['train'].train_number} for {min(20, int(winner['total_score']))} minutes",
                description=(
                    f"Train {loser['train'].train_number} should be held at the nearest "
                    f"loop station or platform to allow Train {winner['train'].train_number} "
                    f"to clear the section. Estimated hold time: "
                    f"{min(20, int(winner['total_score']))} minutes."
                ),
                reasoning=(
                    f"Train {loser['train'].train_number} has lower operational priority "
                    f"(score: {loser['total_score']}/10). Holding this train minimizes "
                    f"total network delay as higher-value service proceeds."
                ),
                priority_score=loser['total_score'],
                confidence=0.88,
                estimated_benefit="Prevents cascade delay to following trains.",
            )
            recommendations.append(hold_rec)

        return recommendations

    def _build_reasoning(self, winner, loser):
        """Build detailed AI reasoning text."""
        w = winner
        l = loser

        lines = [
            f"PRIORITY ANALYSIS REPORT",
            f"{'='*40}",
            f"",
            f"Train {w['train'].train_number} ({w['train'].train_name})",
            f"  • Type Score: {w['scores']['train_type']:.1f}/10",
            f"  • Delay Urgency: {w['scores']['delay_urgency']:.1f}/10",
            f"  • Operational Priority: {w['scores']['operational_priority']:.1f}/10",
            f"  • TOTAL: {w['total_score']:.2f}/10",
            f"",
            f"Train {l['train'].train_number} ({l['train'].train_name})",
            f"  • Type Score: {l['scores']['train_type']:.1f}/10",
            f"  • Delay Urgency: {l['scores']['delay_urgency']:.1f}/10",
            f"  • Operational Priority: {l['scores']['operational_priority']:.1f}/10",
            f"  • TOTAL: {l['total_score']:.2f}/10",
            f"",
            f"DECISION: Train {w['train'].train_number} gets priority because it scored "
            f"{w['total_score'] - l['total_score']:.2f} points higher in the weighted "
            f"multi-factor analysis.",
        ]
        return '\n'.join(lines)

    def get_section_throughput_recommendations(self, section):
        """Generate recommendations to improve section throughput."""
        from apps.scheduling.models import Schedule
        from django.utils import timezone

        today = timezone.now().date()
        schedules = Schedule.objects.filter(
            track_section=section,
            scheduled_date=today,
            status__in=['SCHEDULED', 'RUNNING', 'DELAYED']
        ).select_related('train').order_by('scheduled_arrival')

        recommendations = []
        if schedules.count() == 0:
            return recommendations

        delayed_count = schedules.filter(current_delay__gt=5).count()
        total = schedules.count()

        if delayed_count > total * 0.5:
            recommendations.append({
                'type': 'THROUGHPUT',
                'title': 'High Delay Rate Detected',
                'detail': f'{delayed_count}/{total} trains are delayed on this section. '
                         f'Consider speed restriction review and cascade management.',
                'severity': 'HIGH',
            })

        if total > section.capacity * 2:
            recommendations.append({
                'type': 'CAPACITY',
                'title': 'Section Over Capacity',
                'detail': f'Section capacity is {section.capacity} train(s). '
                         f'{total} trains are scheduled. Consider traffic regulation.',
                'severity': 'CRITICAL',
            })

        return recommendations
