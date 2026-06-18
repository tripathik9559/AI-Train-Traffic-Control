from django import forms
from .models import Schedule

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['train','station','platform','track_section','route',
                  'scheduled_date','stop_sequence','scheduled_arrival','scheduled_departure',
                  'halt_duration','is_originating','is_terminating','status','notes']
        widgets = {
            'train': forms.Select(attrs={'class':'form-select'}),
            'station': forms.Select(attrs={'class':'form-select'}),
            'platform': forms.Select(attrs={'class':'form-select'}),
            'track_section': forms.Select(attrs={'class':'form-select'}),
            'route': forms.Select(attrs={'class':'form-select'}),
            'scheduled_date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'stop_sequence': forms.NumberInput(attrs={'class':'form-control'}),
            'scheduled_arrival': forms.DateTimeInput(attrs={'class':'form-control','type':'datetime-local'}),
            'scheduled_departure': forms.DateTimeInput(attrs={'class':'form-control','type':'datetime-local'}),
            'halt_duration': forms.NumberInput(attrs={'class':'form-control'}),
            'is_originating': forms.CheckboxInput(attrs={'class':'form-check-input'}),
            'is_terminating': forms.CheckboxInput(attrs={'class':'form-check-input'}),
            'status': forms.Select(attrs={'class':'form-select'}),
            'notes': forms.Textarea(attrs={'class':'form-control','rows':2}),
        }
