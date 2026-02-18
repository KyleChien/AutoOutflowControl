from django import forms
from .models import HydrologyProject, HornerCoefficients, WatershedParameters, RainfallParameters, UnitHydrographData


class ProjectForm(forms.ModelForm):
    """Form for creating/editing hydrology projects"""
    class Meta:
        model = HydrologyProject
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class HornerCoefficientsForm(forms.ModelForm):
    """Form for Horner coefficients input"""
    class Meta:
        model = HornerCoefficients
        fields = ['return_period', 'coefficient_a', 'coefficient_b', 'coefficient_c']
        widgets = {
            'return_period': forms.NumberInput(attrs={'class': 'form-control'}),
            'coefficient_a': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'coefficient_b': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'coefficient_c': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
        }


class WatershedParametersForm(forms.ModelForm):
    """Form for watershed parameters"""
    class Meta:
        model = WatershedParameters
        fields = ['tc_calculation_method', 'length', 'elevation_diff', 'manning_n', 'hydraulic_radius', 'time_concentration', 'area']
        widgets = {
            'tc_calculation_method': forms.Select(attrs={'class': 'form-control', 'id': 'tc_calculation_method'}),
            'length': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'id': 'length'}),
            'elevation_diff': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'id': 'elevation_diff'}),
            'manning_n': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'id': 'manning_n'}),
            'hydraulic_radius': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'id': 'hydraulic_radius'}),
            'time_concentration': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'id': 'time_concentration'}),
            'area': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'id': 'area'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields optional by default
        self.fields['length'].required = False
        self.fields['elevation_diff'].required = False
        self.fields['manning_n'].required = False
        self.fields['hydraulic_radius'].required = False
        self.fields['time_concentration'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('tc_calculation_method')
        
        if method == 'computed':
            # Validate that all computation parameters are provided
            required_fields = ['length', 'elevation_diff', 'manning_n', 'hydraulic_radius']
            missing_fields = []
            
            for field in required_fields:
                if not cleaned_data.get(field):
                    missing_fields.append(self.fields[field].help_text)
            
            if missing_fields:
                raise forms.ValidationError(
                    f"When computing time of concentration, all watershed parameters are required: {', '.join(missing_fields)}"
                )
        
        elif method == 'direct':
            # Validate that time concentration is provided
            if not cleaned_data.get('time_concentration'):
                raise forms.ValidationError(
                    "When inputting time concentration directly, the time concentration value is required."
                )
        
        return cleaned_data


class RainfallParametersForm(forms.ModelForm):
    """Form for rainfall parameters"""
    class Meta:
        model = RainfallParameters
        fields = ['curve_number', 'unit_duration']
        widgets = {
            'curve_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'unit_duration': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }


class UnitHydrographDataForm(forms.ModelForm):
    """Form for unit hydrograph parameters"""
    class Meta:
        model = UnitHydrographData
        fields = ['time_ratios', 'discharge_ratios', 'effective_rainfall']
        widgets = {
            'time_ratios': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 
                                                'placeholder': 'Enter comma-separated values: 0.0, 0.1, 0.2, ...'}),
            'discharge_ratios': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 
                                                    'placeholder': 'Enter comma-separated values: 0.0, 0.03, 0.1, ...'}),
            'effective_rainfall': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }

    def clean_time_ratios(self):
        data = self.cleaned_data['time_ratios']
        try:
            # Parse JSON or comma-separated values
            if data.strip().startswith('['):
                ratios = json.loads(data)
            else:
                ratios = [float(x.strip()) for x in data.split(',')]
            return ratios
        except (json.JSONDecodeError, ValueError):
            raise forms.ValidationError("Invalid format. Use comma-separated values or JSON array.")

    def clean_discharge_ratios(self):
        data = self.cleaned_data['discharge_ratios']
        try:
            # Parse JSON or comma-separated values
            if data.strip().startswith('['):
                ratios = json.loads(data)
            else:
                ratios = [float(x.strip()) for x in data.split(',')]
            return ratios
        except (json.JSONDecodeError, ValueError):
            raise forms.ValidationError("Invalid format. Use comma-separated values or JSON array.")


class ProjectEditForm(forms.ModelForm):
    """Comprehensive form for editing all project parameters"""
    
    class Meta:
        model = HydrologyProject
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = kwargs.get('instance')
        if project:
            # Add forms for related models
            self.watershed_form = WatershedParametersForm(
                instance=getattr(project, 'watershedparameters', None)
            )
            self.rainfall_form = RainfallParametersForm(
                instance=getattr(project, 'rainfallparameters', None)
            )


class ComputationConfigForm(forms.Form):
    """Form for configuring computation parameters"""
    
    RETURN_PERIOD_CHOICES = [
        (2, '2 years'),
        (5, '5 years'),
        (10, '10 years'),
        (25, '25 years'),
        (50, '50 years'),
        (100, '100 years'),
    ]
    
    DURATION_A_CHOICES = [
        (5, '5 minutes'),
        (10, '10 minutes'),
        (30, '30 minutes'),
        (60, '1 hour'),
        (120, '2 hours'),
        (180, '3 hours'),
        (360, '6 hours'),
        (1440, '24 hours'),
    ]
    
    DURATION_B_CHOICES = [
        (1, '1 hour'),
        (3, '3 hours'),
        (6, '6 hours'),
        (12, '12 hours'),
        (18, '18 hours'),
        (24, '24 hours'),
    ]
    
    return_periods = forms.MultipleChoiceField(
        choices=RETURN_PERIOD_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        initial=[2, 5, 10, 25, 50, 100]
    )
    
    durations_a = forms.MultipleChoiceField(
        label="Rainfall Durations (minutes)",
        choices=DURATION_A_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        initial=[5, 10, 30, 60, 120, 180, 360, 1440]
    )
    
    durations_b = forms.MultipleChoiceField(
        label="Rainfall Durations (hours)",
        choices=DURATION_B_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        initial=[1, 3, 6, 12, 18, 24]
    )


# Import json for parsing
import json