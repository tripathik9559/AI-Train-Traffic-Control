from django import forms
from .models import Station, Platform, Route, TrackSection

w = lambda t, p='': {'class': f'form-control', 'placeholder': p}
ws = lambda: {'class': 'form-select'}

class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        fields = ['name','code','station_type','city','state','zone','division',
                  'latitude','longitude','total_platforms','is_junction','has_goods_shed']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control','placeholder':'Station name'}),
            'code': forms.TextInput(attrs={'class':'form-control','placeholder':'e.g. LKO'}),
            'station_type': forms.Select(attrs={'class':'form-select'}),
            'city': forms.TextInput(attrs={'class':'form-control'}),
            'state': forms.TextInput(attrs={'class':'form-control'}),
            'zone': forms.TextInput(attrs={'class':'form-control','placeholder':'e.g. NR'}),
            'division': forms.TextInput(attrs={'class':'form-control','placeholder':'e.g. Lucknow'}),
            'latitude': forms.NumberInput(attrs={'class':'form-control','step':'0.0001'}),
            'longitude': forms.NumberInput(attrs={'class':'form-control','step':'0.0001'}),
            'total_platforms': forms.NumberInput(attrs={'class':'form-control'}),
            'is_junction': forms.CheckboxInput(attrs={'class':'form-check-input'}),
            'has_goods_shed': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }

class PlatformForm(forms.ModelForm):
    class Meta:
        model = Platform
        fields = ['station','platform_number','platform_type','length','status','has_shelter']
        widgets = {
            'station': forms.Select(attrs={'class':'form-select'}),
            'platform_number': forms.TextInput(attrs={'class':'form-control'}),
            'platform_type': forms.Select(attrs={'class':'form-select'}),
            'length': forms.NumberInput(attrs={'class':'form-control','step':'0.1'}),
            'status': forms.Select(attrs={'class':'form-select'}),
            'has_shelter': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }

class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['name','source_station','destination_station','distance',
                  'estimated_duration','max_speed','is_electrified','is_double_line']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'source_station': forms.Select(attrs={'class':'form-select'}),
            'destination_station': forms.Select(attrs={'class':'form-select'}),
            'distance': forms.NumberInput(attrs={'class':'form-control','step':'0.1'}),
            'estimated_duration': forms.NumberInput(attrs={'class':'form-control'}),
            'max_speed': forms.NumberInput(attrs={'class':'form-control','step':'0.1'}),
            'is_electrified': forms.CheckboxInput(attrs={'class':'form-check-input'}),
            'is_double_line': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }

class TrackSectionForm(forms.ModelForm):
    class Meta:
        model = TrackSection
        fields = ['name','code','from_station','to_station','length',
                  'number_of_lines','max_speed','capacity','status']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'code': forms.TextInput(attrs={'class':'form-control','placeholder':'e.g. LKO-CNB-01'}),
            'from_station': forms.Select(attrs={'class':'form-select'}),
            'to_station': forms.Select(attrs={'class':'form-select'}),
            'length': forms.NumberInput(attrs={'class':'form-control','step':'0.1'}),
            'number_of_lines': forms.NumberInput(attrs={'class':'form-control'}),
            'max_speed': forms.NumberInput(attrs={'class':'form-control','step':'0.1'}),
            'capacity': forms.NumberInput(attrs={'class':'form-control'}),
            'status': forms.Select(attrs={'class':'form-select'}),
        }
