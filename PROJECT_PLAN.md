# FishPeakFlow - Outflow Control Hydrograph Web App

## Project Description
A Django-based web application for computing outflow control hydrographs using hydrological engineering methods. The app takes user inputs for rainfall parameters, watershed characteristics, and computes comprehensive hydrograph analysis.

## Architecture

### Framework Choice: Django
- Full-featured framework with robust admin interface
- Excellent form handling for complex scientific inputs
- Built-in ORM for data persistence
- Strong security and scalability

### Application Structure
```
FishPeakFlow/
├── manage.py
├── requirements.txt
├── fishpeakflow/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── hydrology/
│   ├── models.py          # Data models for inputs/results
│   ├── views.py           # Web views and logic
│   ├── forms.py           # Input forms
│   ├── urls.py            # App URLs
│   ├── calculators.py     # Hydrology computations
│   └── templates/
│       ├── base.html
│       ├── input.html
│       └── results.html
└── static/
    ├── css/
    ├── js/
    └── charts/
```

## Core Components

### A. Input Forms (forms.py)
- **HornerCoefficientsForm**: Table input for a,b,c coefficients per return period
- **RainfallParametersForm**: Unit duration, CN value, watershed parameters
- **UnitHydrographForm**: Time ratios, discharge ratios, area, effective rainfall
- **WatershedForm**: L, H, V, R parameters for time of concentration

### B. Computation Modules (calculators.py)
- **ExtremeRainEvent**: Intensity and accumulation tables
- **HornerRainType**: Hyetograph computation using alternating block method
- **EffectiveRainfall**: SCS curve number method
- **TimeConcentration**: Overland and channel flow calculations
- **DimensionlessUH**: Unit hydrograph and convolution

### C. Data Models (models.py)
- **HydrologyProject**: Store complete project configurations
- **HornerCoefficients**: Coefficient sets per return period
- **WatershedParameters**: Physical watershed characteristics
- **ComputationResults**: Store computed tables and hydrographs

### D. Visualization
- **Chart.js** for interactive graphs
- Hydrograph plots (time vs discharge)
- Rainfall intensity curves
- Accumulated precipitation charts
- Effective rainfall visualization

## User Workflow
1. **Project Setup**: Create new hydrology project
2. **Input Data**: Enter Horner coefficients, watershed parameters
3. **Configure**: Set return periods, durations, time intervals
4. **Compute**: Run complete hydrograph computation
5. **Results**: View tables, charts, and download data

## Key Features
- **Data Persistence**: Save/load projects
- **Validation**: Input range checking and scientific validation
- **Export**: CSV/JSON export for results
- **Help System**: Tooltips and guidance for parameters
- **Responsive Design**: Mobile-friendly interface

## Implementation Phases
1. **Phase 1**: Basic Django setup + input forms
2. **Phase 2**: Core computation engine integration
3. **Phase 3**: Results display and basic tables
4. **Phase 4**: Interactive charts and visualization
5. **Phase 5**: Data export and project management

## Technical Considerations
- **NumPy integration** for mathematical computations
- **Celery** for long-running computations if needed
- **PostgreSQL** for robust data storage
- **Docker** for deployment consistency

## Computation Prerequisites

### Target Configurations
1. Target return periods (year): [2, 5, 10, 25, 50, 100]
2. Target rainfall duration A (minute): [5, 10, 30, 60, 120, 180, 360, 1440]
3. Target rainfall duration B (hr): [1, 3, 6, 12, 18, 24]

### Extreme Rain Event Computation
1. User input: Horner coefficients table (a, b, c) for each return period
2. Compute precipitation intensity table (mm/hr) for duration A
3. Compute accumulated precipitation table (mm) for duration B

### Horner Rain Type Computation
1. User input: unit precipitation duration (hr), tr
2. Compute precipitation intensity using Horner formula: I = a/(t+b)^c
3. Compute accumulated precipitation
4. Compute discrete difference for unit duration precipitation
5. Convert to percentage and sort by alternating block method
6. Apply 24hr accumulated precipitation to create hyetograph

### Effective Rainfall Computation
1. User input: CN value
2. Compute S = 25400/CN - 254 (mm), Ia_max = 0.2*S
3. Compute cumulative sum P from hyetograph
4. Clip P by Ia_max to get Ia
5. Compute Fa and Pe values
6. Compute discrete difference and convert to cm

### Time of Concentration Computation
1. User input: L (m), H, V, R
2. Compute overland flow time: T1 = L^0.8 * ((S+25.4)^0.7)/(4238*H^0.5)
3. Compute channel flow time: T2 = L/(3600*V)
4. Compute time of concentration: Tc = T1 + T2

### Dimensionless Unit Hydrograph Computation
1. User input: time ratios t/Tp, discharge ratios Q/Qp, area A (km^2), effective rainfall URe=10mm
2. Compute Tp = tr/2 + Tlag, where Tlag = 0.6*Tc
3. Compute Qp = 0.208*A*URe/Tp
4. Generate 1cm unit hydrograph
5. Interpolate by tr interval
6. Create matrix M by multiplying q_interp by RE values
7. Compute anti-diagonal sums for outflow hydrograph