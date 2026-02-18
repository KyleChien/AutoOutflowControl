from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin
import json
import csv
from io import StringIO

from .models import HydrologyProject, HornerCoefficients, WatershedParameters, RainfallParameters, ComputationResults, UnitHydrographData
from .forms import ProjectForm, HornerCoefficientsForm, WatershedParametersForm, RainfallParametersForm, ComputationConfigForm, UnitHydrographDataForm
from .calculators import HornerTable, HornerRainType, EffectiveRainfall, TimeConcentration, DimensionlessUnitHydrograph


class ProjectListView(ListView):
    model = HydrologyProject
    template_name = 'hydrology/project_list.html'
    context_object_name = 'projects'
    ordering = ['-updated_at']


class ProjectDetailView(DetailView):
    model = HydrologyProject
    template_name = 'hydrology/project_detail.html'
    context_object_name = 'project'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        context['horner_coefficients'] = HornerCoefficients.objects.filter(project=project)
        context['watershed_params'] = WatershedParameters.objects.filter(project=project).first()
        context['rainfall_params'] = RainfallParameters.objects.filter(project=project).first()
        context['computation_results'] = ComputationResults.objects.filter(project=project).first()
        context['unit_hydrograph_data'] = UnitHydrographData.objects.filter(project=project).first()
        return context


class ProjectCreateView(CreateView):
    model = HydrologyProject
    form_class = ProjectForm
    template_name = 'hydrology/project_form.html'
    success_url = reverse_lazy('hydrology:project_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        project = form.instance
        
        # Create Horner coefficients
        for i in range(6):
            return_period = int(self.request.POST.get(f'return_period_{i}'))
            coefficient_a = float(self.request.POST.get(f'coefficient_a_{i}'))
            coefficient_b = float(self.request.POST.get(f'coefficient_b_{i}'))
            coefficient_c = float(self.request.POST.get(f'coefficient_c_{i}'))
            
            HornerCoefficients.objects.create(
                project=project,
                return_period=return_period,
                coefficient_a=coefficient_a,
                coefficient_b=coefficient_b,
                coefficient_c=coefficient_c
            )
        
        # Create watershed parameters
        tc_method = self.request.POST.get('tc_calculation_method', 'computed')
        
        watershed_data = {
            'project': project,
            'area': float(self.request.POST.get('area')),
            'tc_calculation_method': tc_method
        }
        
        if tc_method == 'computed':
            watershed_data.update({
                'length': float(self.request.POST.get('length')),
                'elevation_diff': float(self.request.POST.get('elevation_diff')),
                'manning_n': float(self.request.POST.get('manning_n')),
                'hydraulic_radius': float(self.request.POST.get('hydraulic_radius')),
            })
        else:  # direct method
            watershed_data.update({
                'time_concentration': float(self.request.POST.get('time_concentration')),
            })
        
        WatershedParameters.objects.create(**watershed_data)
        
        # Create rainfall parameters
        RainfallParameters.objects.create(
            project=project,
            curve_number=int(self.request.POST.get('curve_number')),
            unit_duration=float(self.request.POST.get('unit_duration'))
        )
        
        # Create default unit hydrograph data
        time_ratios, discharge_ratios = DimensionlessUnitHydrograph.get_default_dimensionless_uh()
        UnitHydrographData.objects.create(
            project=project,
            time_ratios=time_ratios.tolist(),
            discharge_ratios=discharge_ratios.tolist(),
            effective_rainfall=10.0
        )
        
        messages.success(self.request, f'Project "{project.name}" created successfully!')
        return response


class ProjectUpdateView(UpdateView):
    model = HydrologyProject
    form_class = ProjectForm
    template_name = 'hydrology/project_edit.html'
    
    def get_success_url(self):
        return reverse_lazy('hydrology:project_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get existing related objects
        context['watershed_params'] = WatershedParameters.objects.filter(project=self.object).first()
        context['rainfall_params'] = RainfallParameters.objects.filter(project=self.object).first()
        context['horner_coeffs'] = HornerCoefficients.objects.filter(project=self.object)
        
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        project = form.instance
        
        # Update watershed parameters if provided
        watershed_params = WatershedParameters.objects.filter(project=project).first()
        if watershed_params:
            tc_method = self.request.POST.get('tc_calculation_method', watershed_params.tc_calculation_method)
            
            watershed_data = {
                'tc_calculation_method': tc_method
            }
            
            if tc_method == 'computed':
                watershed_data.update({
                    'length': float(self.request.POST.get('length', watershed_params.length)),
                    'elevation_diff': float(self.request.POST.get('elevation_diff', watershed_params.elevation_diff)),
                    'manning_n': float(self.request.POST.get('manning_n', watershed_params.manning_n)),
                    'hydraulic_radius': float(self.request.POST.get('hydraulic_radius', watershed_params.hydraulic_radius)),
                })
                watershed_data['time_concentration'] = None
            else:  # direct method
                watershed_data.update({
                    'time_concentration': float(self.request.POST.get('time_concentration', watershed_params.time_concentration)),
                })
                watershed_data['length'] = None
                watershed_data['elevation_diff'] = None
                watershed_data['manning_n'] = None
                watershed_data['hydraulic_radius'] = None
            
            for key, value in watershed_data.items():
                setattr(watershed_params, key, value)
            watershed_params.save()
        
        # Update rainfall parameters if provided
        rainfall_params = RainfallParameters.objects.filter(project=project).first()
        if rainfall_params:
            rainfall_params.curve_number = int(self.request.POST.get('curve_number', rainfall_params.curve_number))
            rainfall_params.unit_duration = float(self.request.POST.get('unit_duration', rainfall_params.unit_duration))
            rainfall_params.save()
        
        messages.success(self.request, f'Project "{form.instance.name}" updated successfully!')
        return response


def project_compute(request, pk):
    """Run complete hydrograph computation for a project"""
    project = get_object_or_404(HydrologyProject, pk=pk)
    
    # Get all required data
    horner_coeffs = HornerCoefficients.objects.filter(project=project)
    watershed_params = WatershedParameters.objects.filter(project=project).first()
    rainfall_params = RainfallParameters.objects.filter(project=project).first()
    unit_hydrograph_data = UnitHydrographData.objects.filter(project=project).first()
    
    if not all([horner_coeffs, watershed_params, rainfall_params, unit_hydrograph_data]):
        messages.error(request, 'Project configuration incomplete. Please check all parameters.')
        return redirect('hydrology:project_detail', pk=pk)
    
    try:
        # Prepare Horner coefficients dictionary
        horners = {coeff.return_period: {'a': coeff.coefficient_a, 'b': coeff.coefficient_b, 'c': coeff.coefficient_c} 
                  for coeff in horner_coeffs}
        
        # Target configurations
        return_periods = [2, 5, 10, 25, 50, 100]
        durations_a = [5, 10, 30, 60, 120, 180, 360, 1440]  # minutes
        durations_b = [1, 3, 6, 12, 18, 24]  # hours
        
        # Step 1: Compute intensity table
        intensity_table = HornerTable.compute_intensity_table(horners, durations_a)
        
        # Step 2: Compute accumulated precipitation table
        accumulation_table = HornerTable.compute_accumulated_table(intensity_table, durations_a)
        
        # Step 3: Compute Horner rain type (using 100-year return period for hyetograph)
        max_return_period = max(horners.keys())
        max_coeffs = horners[max_return_period]
        times, intensities, accumulated = HornerRainType.compute_precipitation_list(
            max_coeffs, rainfall_params.unit_duration
        )
        
        # Step 4: Compute unit duration precipitation and percentages
        unit_precip = HornerRainType.compute_unit_duration_precipitation(times, accumulated)
        unit_precip_percent = [p * 100 / sum(unit_precip) if sum(unit_precip) > 0 else 0 for p in unit_precip]
        sorted_percentages = HornerRainType.alternating_block_sort(unit_precip_percent)
        
        # Step 5: Create hyetograph using 24hr precipitation
        total_24hr_precip = accumulation_table.get(max_return_period, {}).get(1440, 0)
        hyetograph = HornerRainType.create_hyetograph(sorted_percentages, total_24hr_precip)
        
        # Step 6: Compute effective rainfall
        effective_rainfall = EffectiveRainfall.compute_effective_rainfall(hyetograph, rainfall_params.curve_number)
        
        # Step 7: Get time of concentration
        if watershed_params.tc_calculation_method == 'direct':
            time_concentration = watershed_params.time_concentration
        else:
            # Compute from watershed parameters
            slope = watershed_params.elevation_diff / watershed_params.length if watershed_params.length > 0 else 0
            time_concentration = TimeConcentration.compute_time_of_concentration(
                watershed_params.length,
                watershed_params.elevation_diff,
                watershed_params.manning_n,
                watershed_params.hydraulic_radius,
                slope
            )
        
        # Step 8: Compute unit hydrograph
        t_b, t_p, q_p = DimensionlessUnitHydrograph.compute_peak_flow(
            time_concentration,
            watershed_params.area,
            unit_hydrograph_data.effective_rainfall,
            rainfall_params.unit_duration
        )
        
        T, Q = DimensionlessUnitHydrograph.compute_unit_hydrograph(
            t_p, q_p, 
            unit_hydrograph_data.time_ratios,
            unit_hydrograph_data.discharge_ratios
        )
        
        T_interp, Q_interp = DimensionlessUnitHydrograph.interpolate_unit_hydrograph(
            T, Q, rainfall_params.unit_duration
        )
        
        # Step 9: Compute outflow hydrograph
        outflow_hydrograph = DimensionlessUnitHydrograph.compute_outflow_hydrograph(Q_interp, effective_rainfall)
        
        # Save results
        results, created = ComputationResults.objects.get_or_create(project=project)
        results.intensity_table = {str(k): {str(k2): v2 for k2, v2 in v.items()} for k, v in intensity_table.items()}
        results.accumulation_table = {str(k): {str(k2): v2 for k2, v2 in v.items()} for k, v in accumulation_table.items()}
        results.hyetograph = hyetograph
        results.effective_rainfall = effective_rainfall
        results.time_concentration = time_concentration
        results.unit_hydrograph = {'time': T_interp, 'discharge': Q_interp}
        results.outflow_hydrograph = outflow_hydrograph
        results.save()
        
        messages.success(request, 'Hydrograph computation completed successfully!')
        return redirect('hydrology:project_results', pk=pk)
        
    except Exception as e:
        messages.error(request, f'Computation failed: {str(e)}')
        return redirect('hydrology:project_detail', pk=pk)


def project_results(request, pk):
    """Display computation results with visualization"""
    project = get_object_or_404(HydrologyProject, pk=pk)
    results = ComputationResults.objects.filter(project=project).first()
    rainfall_params = RainfallParameters.objects.filter(project=project).first()
    
    if not results:
        messages.error(request, 'No computation results found. Please run the computation first.')
        return redirect('hydrology:project_detail', pk=pk)
    
    # Import json for proper serialization
    import json
    
    context = {
        'project': project,
        'results': results,
        'intensity_table': results.intensity_table,
        'accumulation_table': results.accumulation_table,
        'hyetograph': json.dumps(results.hyetograph if results.hyetograph else []),
        'effective_rainfall': json.dumps(results.effective_rainfall if results.effective_rainfall else []),
        'time_concentration': results.time_concentration,
        'unit_hydrograph': json.dumps(results.unit_hydrograph if results.unit_hydrograph else {'time': [], 'discharge': []}),
        'outflow_hydrograph': json.dumps(results.outflow_hydrograph if results.outflow_hydrograph else []),
        'rainfall_params': rainfall_params,
    }
    
    return render(request, 'hydrology/project_results.html', context)


def export_results(request, pk, format_type):
    """Export computation results in specified format"""
    project = get_object_or_404(HydrologyProject, pk=pk)
    results = ComputationResults.objects.filter(project=project).first()
    
    if not results:
        messages.error(request, 'No computation results found.')
        return redirect('hydrology:project_detail', pk=pk)
    
    if format_type == 'csv':
        # Create CSV response
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Project Name', project.name])
        writer.writerow(['Computed At', results.computed_at])
        writer.writerow([])
        
        # Write intensity table
        writer.writerow(['Intensity Table (mm/hr)'])
        writer.writerow(['Return Period', 'Duration (min)', 'Intensity'])
        for period_str, period_data in results.intensity_table.items():
            for duration_str, intensity in period_data.items():
                writer.writerow([period_str, duration_str, intensity])
        
        writer.writerow([])
        writer.writerow(['Outflow Hydrograph'])
        writer.writerow(['Time Step', 'Discharge (cms)'])
        for i, discharge in enumerate(results.outflow_hydrograph):
            writer.writerow([i, discharge])
        
        # Create response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{project.name}_results.csv"'
        return response
    
    elif format_type == 'json':
        # Create JSON response
        data = {
            'project': {
                'name': project.name,
                'description': project.description,
                'computed_at': results.computed_at.isoformat(),
            },
            'results': {
                'intensity_table': results.intensity_table,
                'accumulation_table': results.accumulation_table,
                'hyetograph': results.hyetograph,
                'effective_rainfall': results.effective_rainfall,
                'time_concentration': results.time_concentration,
                'unit_hydrograph': results.unit_hydrograph,
                'outflow_hydrograph': results.outflow_hydrograph,
            }
        }
        
        response = JsonResponse(data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="{project.name}_results.json"'
        return response
    
    else:
        messages.error(request, 'Invalid export format.')
        return redirect('hydrology:project_detail', pk=pk)
