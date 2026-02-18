from django.db import models
import json


class HydrologyProject(models.Model):
    """Main project to store complete hydrology analysis configurations"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class HornerCoefficients(models.Model):
    """Store Horner coefficients for different return periods"""
    project = models.ForeignKey(HydrologyProject, on_delete=models.CASCADE)
    return_period = models.IntegerField(help_text="Return period in years")
    coefficient_a = models.FloatField(help_text="Horner coefficient a")
    coefficient_b = models.FloatField(help_text="Horner coefficient b")
    coefficient_c = models.FloatField(help_text="Horner coefficient c")
    
    class Meta:
        unique_together = ['project', 'return_period']
    
    def __str__(self):
        return f"{self.project.name} - {self.return_period} years"


class WatershedParameters(models.Model):
    """Store watershed physical characteristics"""
    project = models.OneToOneField(HydrologyProject, on_delete=models.CASCADE)
    
    # Time of concentration calculation method
    tc_calculation_method = models.CharField(
        max_length=20,
        choices=[
            ('computed', 'Compute from parameters'),
            ('direct', 'Input directly')
        ],
        default='computed',
        help_text="How to determine time of concentration"
    )
    
    # Time of concentration parameters (for computed method)
    length = models.FloatField(help_text="Flow path length L (m)", blank=True, null=True)
    elevation_diff = models.FloatField(help_text="Elevation difference H (m)", blank=True, null=True)
    manning_n = models.FloatField(help_text="Manning's roughness coefficient n", blank=True, null=True)
    hydraulic_radius = models.FloatField(help_text="Hydraulic radius R (m)", blank=True, null=True)
    
    # Direct time of concentration input
    time_concentration = models.FloatField(
        help_text="Time of concentration Tc (hours)", 
        blank=True, 
        null=True
    )
    
    # Unit hydrograph parameters
    area = models.FloatField(help_text="Watershed area A (km²)")
    
    def __str__(self):
        return f"{self.project.name} - Watershed Parameters"


class RainfallParameters(models.Model):
    """Store rainfall-related parameters"""
    project = models.OneToOneField(HydrologyProject, on_delete=models.CASCADE)
    
    # Curve number for effective rainfall
    curve_number = models.IntegerField(help_text="SCS Curve Number (CN)")
    
    # Unit duration for Horner rain type
    unit_duration = models.FloatField(help_text="Unit precipitation duration tr (hours)")
    
    def __str__(self):
        return f"{self.project.name} - Rainfall Parameters"


class ComputationResults(models.Model):
    """Store computation results for each project"""
    project = models.OneToOneField(HydrologyProject, on_delete=models.CASCADE)
    
    # Store results as JSON for flexibility
    intensity_table = models.JSONField(help_text="Precipitation intensity table", blank=True, null=True)
    accumulation_table = models.JSONField(help_text="Accumulated precipitation table", blank=True, null=True)
    hyetograph = models.JSONField(help_text="Hyetograph data", blank=True, null=True)
    effective_rainfall = models.JSONField(help_text="Effective rainfall data", blank=True, null=True)
    time_concentration = models.FloatField(help_text="Time of concentration Tc (hours)", blank=True, null=True)
    unit_hydrograph = models.JSONField(help_text="Unit hydrograph data", blank=True, null=True)
    outflow_hydrograph = models.JSONField(help_text="Outflow hydrograph data", blank=True, null=True)
    
    computed_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.project.name} - Results"


class UnitHydrographData(models.Model):
    """Store dimensionless unit hydrograph parameters"""
    project = models.ForeignKey(HydrologyProject, on_delete=models.CASCADE)
    
    # Time ratios and discharge ratios for dimensionless hydrograph
    time_ratios = models.JSONField(help_text="Time ratios t/Tp")
    discharge_ratios = models.JSONField(help_text="Discharge ratios Q/Qp")
    effective_rainfall = models.FloatField(help_text="Effective rainfall URe (mm)", default=10.0)
    
    def __str__(self):
        return f"{self.project.name} - Unit Hydrograph Data"
