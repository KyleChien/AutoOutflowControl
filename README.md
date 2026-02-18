# AutoOutflowControl - Outflow Control Hydrograph Calculator

A Django-based web application for computing outflow control hydrographs using hydrological engineering methods. This application implements the complete workflow from rainfall input parameters to final outflow hydrograph visualization.

## Features

- **Project Management**: Create and manage multiple hydrology projects
- **Horner Coefficients**: Configure intensity-duration-frequency relationships
- **Watershed Parameters**: Define physical watershed characteristics
- **Rainfall Analysis**: Compute precipitation intensity and accumulation tables
- **Hyetograph Generation**: Create rainfall distribution patterns using alternating block method
- **Effective Rainfall**: Apply SCS curve number method for runoff computation
- **Time of Concentration**: Calculate flow timing using overland and channel flow methods
- **Unit Hydrograph**: Generate dimensionless and scaled unit hydrographs
- **Outflow Hydrograph**: Compute final outflow through convolution
- **Interactive Visualization**: Charts for all hydrograph components
- **Data Export**: Export results in CSV and JSON formats

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FishPeakFlow
   ```

2. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Set up the database**
   ```bash
   python3 manage.py migrate
   ```

4. **Run the development server**
   ```bash
   python3 manage.py runserver
   ```

5. **Access the application**
   Open your browser and go to `http://localhost:8000/hydrology/`

## Usage

### 1. Create a New Project

1. Click "New Project" on the project list page
2. Enter project name and optional description
3. Configure Horner coefficients (default values provided)
4. Set watershed parameters (length, elevation, Manning's n, etc.)
5. Define rainfall parameters (Curve Number, unit duration)
6. Click "Create Project"

### 2. Run Computation

1. From the project detail page, click "Run Computation"
2. The system will automatically:
   - Compute intensity and accumulation tables
   - Generate hyetograph using alternating block method
   - Calculate effective rainfall using SCS method
   - Determine time of concentration
   - Create unit hydrograph
   - Compute final outflow hydrograph

### 3. View Results

Results include:
- **Precipitation Intensity Table**: mm/hr for various durations and return periods
- **Accumulated Precipitation Table**: Total rainfall in mm
- **Hyetograph**: Rainfall distribution over time
- **Effective Rainfall**: Runoff after accounting for losses
- **Unit Hydrograph**: Watershed response to unit rainfall
- **Outflow Hydrograph**: Final discharge hydrograph

### 4. Export Data

Export results in:
- **CSV Format**: Tabular data for spreadsheet analysis
- **JSON Format**: Structured data for programmatic use

## Computational Methods

### Horner Formula
$$I = \frac{a}{(t+b)^c}$$

Where:
- I = precipitation intensity (mm/hr)
- t = duration (minutes)
- a, b, c = Horner coefficients

### SCS Curve Number Method
$$S = \frac{25400}{CN} - 254$$
$$I_{a,max} = 0.2 \times S$$

### Time of Concentration
$$T_1 = \frac{L^{0.8} \times (S+25.4)^{0.7}}{4238 \times H^{0.5}}$$
$$T_2 = \frac{L}{3600 \times V}$$
$$T_c = T_1 + T_2$$

### Unit Hydrograph
$$T_p = \frac{t_r}{2} + T_{lag}$$
$$T_{lag} = 0.6 \times T_c$$
$$Q_p = \frac{0.208 \times A \times URe}{T_p}$$

## Project Structure

```
FishPeakFlow/
├── fishpeakflow/          # Django project settings
├── hydrology/            # Main application
│   ├── models.py         # Database models
│   ├── views.py         # Web views and logic
│   ├── forms.py         # Input forms
│   ├── calculators.py    # Computation engines
│   └── templates/       # HTML templates
├── static/              # CSS, JavaScript, images
└── requirements.txt      # Python dependencies
```

## Default Values

The application includes typical default values for:
- **Horner Coefficients**: Based on urban drainage design
- **Return Periods**: 2, 5, 10, 25, 50, 100 years
- **Rainfall Durations**: 5 min to 24 hours
- **Curve Numbers**: 30-98 range for different land uses

## Dependencies

- Django 4.2+
- NumPy 1.24+
- Pandas 2.0+
- Matplotlib 3.7+
- Plotly 5.15+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues:
1. Check the documentation in `PROJECT_PLAN.md`
2. Review the computational methods above
3. Create an issue in the repository

## Acknowledgments

This application implements standard hydrological engineering methods including:
- Horner intensity-duration-frequency relationships
- SCS (NRCS) curve number method
- Dimensionless unit hydrograph theory
- Alternating block method for rainfall distribution
