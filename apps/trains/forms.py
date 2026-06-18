from django import forms
from .models import Train


class TrainForm(forms.ModelForm):
    class Meta:
        model = Train
        fields = [
            'train_number', 'train_name', 'train_type', 'speed',
            'priority_level', 'total_coaches', 'rake_composition',
            'source_station', 'destination_station', 'via_route',
            'scheduled_departure', 'scheduled_arrival', 'days_of_operation',
            'current_status', 'notes',
        ]
        widgets = {
            'train_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 12301'}),
            'train_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Howrah Rajdhani'}),
            'train_type': forms.Select(attrs={'class': 'form-select'}),
            'speed': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'priority_level': forms.Select(attrs={'class': 'form-select'}),
            'total_coaches': forms.NumberInput(attrs={'class': 'form-control'}),
            'rake_composition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '3AC+SL+GEN'}),
            'source_station': forms.Select(attrs={'class': 'form-select'}),
            'destination_station': forms.Select(attrs={'class': 'form-select'}),
            'via_route': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CNB,MGS,PNBE'}),
            'scheduled_departure': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'scheduled_arrival': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'days_of_operation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Daily'}),
            'current_status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
