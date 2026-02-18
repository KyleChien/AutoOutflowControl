import numpy as np


def Horner_table(return_period):
    """
    Look up Horner coefficients (a, b, c) for a given return period.
    In professional hydraulic engineering, these coefficients are derived from 
    intensity-duration-frequency (IDF) curves for a specific location.
    
    Args:
        return_period (int): Return period in years (e.g., 2, 5, 10, 20, 50, 100)
        
    Returns:
        dict: Horner coefficients {'a': ..., 'b': ..., 'c': ...}
    """
    # Professional IDF mock data based on typical urban drainage designs.
    # The coefficients 'b' and 'c' are often constant for a location, 
    # while 'a' increases with the return period.
    data = {
        2:   {"a": 1666.842, "b": 23.246, "c": 0.731},
        5:   {"a": 1914.351, "b": 34.037, "c": 0.694},
        10:  {"a": 2052.866, "b": 40.099, "c": 0.69},
        25:  {"a": 2184.709, "b": 44.84, "c": 0.693},
        50:  {"a": 2228.156, "b": 45.631, "c": 0.694},
        100: {"a": 2232.124, "b": 44.432, "c": 0.694},
    }
    
    # Return the exact match or the closest lower return period if not found
    if return_period in data:
        return data[return_period]
    
    # Simple interpolation or fallback for test purposes
    sorted_periods = sorted(data.keys())
    for p in reversed(sorted_periods):
        if return_period >= p:
            return data[p]
    return data[sorted_periods[0]]

def compute_intensity(a, b, c, t):
    """ 
    Compute the precipitation intensity using Horner formula: i = a / (t+b)^c
    Args:
        a, b, c: Horner coefficients
        t: duration in minutes
    Returns:
        intensity: mm/min
    """
    return a / (t + b)**c

def compute_accumulated_precipitation(intensity, duration):
    """ 
    Compute the accumulated precipitation.
    Args:
        intensity: mm/min
        duration: minutes
    Returns:
        total rainfall: mm
    """
    return intensity * duration

def compute_intensity_table(return_periods, durations):
    """ 
    Compute the precipitation intensity table across different return_periods and durations.
    Returns: {return_period: {duration: intensity}}
    """
    table = {}
    for p in return_periods:
        params = Horner_table(p)
        table[p] = {}
        for t in durations:
            intensity = compute_intensity(params["a"], params["b"], params["c"], t)
            table[p][t] = round(intensity, 4)
    return table

def compute_accumulated_precipitation_table(return_periods, durations):
    """
    Compute the accumulated precipitation table across different return_periods and durations.
    Returns: {return_period: {duration: accumulation}}
    """
    # We can reuse compute_intensity_table or calculate directly
    intensity_table = compute_intensity_table(return_periods, durations)
    acc_table = {}
    for p in return_periods:
        acc_table[p] = {}
        for t in durations:
            intensity = intensity_table[p][t]
            accumulation = compute_accumulated_precipitation(intensity, t)
            acc_table[p][t] = round(accumulation, 2)
    return acc_table


# ============================================================
def compute_peak_flow(Tc, A, Re, tr):
    """
    Args:
        Tc: Time of Concentration (hr)
        A: Area of the watershed (km^2)
        Re: Effective precipitation (mm)
        tr: Time interval(unit duration) (min)
    Return: 
        Tb: Base time (hr)
        Tp: The time when peak flow arrived (hr)
        Qp: Peak flow (cms)
    """
    Tlag = 0.6*Tc
    Tp = tr/60/2 + Tlag
    Tb = 2.67 * Tp
    Qp = 0.208*A*Re/Tp
    return Tb, Tp, Qp

def get_unit_hydrograph(Tp, Qp):
    """
    Generate a unit hydrograph based on a dimensionless unit hydrograph.
    
    The dimensionless unit hydrograph represents a standardized runoff response pattern
    that can be scaled to specific watershed conditions.
    
    Args:
        Tp: Time to peak (hr)
        Qp: Peak discharge (cms)
        
    Returns:
        T: Time array (hr)
        Q: Discharge array (cms)
    """
    # The known dimensionless_unit_hydrograph (SCS/NRCS dimensionless unit hydrograph)
    # Q_Qp values at specific T/Tp ratios

    T_Tp = np.asarray([
        0.0, 0.1, 0.2, 0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2.0,2.2,2.4,2.6,2.8,3.0,3.2,3.4,3.6,3.8,4.0,4.5,5.0,
    ])

    Q_Qp = np.asarray([
        0.000, 0.030, 0.100, 0.190, 0.310, 0.470, 0.660, 0.820, 0.930, 0.990, 1.000, 0.990,
        0.930, 0.860, 0.780, 0.680, 0.560, 0.460, 0.390, 0.330, 0.280, 0.207, 0.147, 0.107,
        0.077, 0.055, 0.040, 0.029, 0.021, 0.015, 0.011, 0.005, 0.000,
    ])
    
    return T_Tp*Tp, Q_Qp*Qp

def get_interpolated_unit_hdrograph(Tp, Qp, tr):
    """
    Interpolate a unit hydrograph to specific time intervals.
    
    This function takes a continuous unit hydrograph and resamples it to uniform
    time intervals, which is useful for discrete convolution calculations in 
    hydrograph analysis.
    
    Args:
        Tp: Time to peak (hr)
        Qp: Peak discharge (cms)
        tr: Desired time interval (hr)
        
    Returns:
        T_interp: Interpolated time array with interval tr (hr)
        Q_interp: Interpolated discharge array (cms)
    """
    T, Q = get_unit_hydrograph(Tp, Qp)

    # Create new time array with uniform intervals
    T_interp = np.arange(0, T[-1] + tr, tr)
    
    # Interpolate discharge values to the new time points
    Q_interp = np.interp(T_interp, T, Q)

    print(T)
    print(Q)
    
    return T_interp, Q_interp


if __name__ == "__main__":
    # Test values
    test_return_periods = [2, 5, 10, 25, 50, 100]              # years
    test_durations = [5, 10, 30, 60, 120, 180, 360, 1440]      # minutes

    print("--- Precipitation Intensity (mm/min) ---")
    i_table = compute_intensity_table(test_return_periods, test_durations)
    
    # Header
    header = "P\\t (min) | " + " | ".join(f"{t:7}" for t in test_durations)
    print(header)
    print("-" * len(header))
    
    for p in test_return_periods:
        row = f"{p:8} | " + " | ".join(f"{i_table[p][t]:7.4f}" for t in test_durations)
        print(row)

    print("\n--- Accumulated Precipitation (mm) ---")
    h_table = compute_accumulated_precipitation_table(test_return_periods, test_durations)
    
    print(header)
    print("-" * len(header))
    for p in test_return_periods:
        row = f"{p:8} | " + " | ".join(f"{h_table[p][t]:7.2f}" for t in test_durations)
        print(row)

    A = 0.037   # (km^2)
    Tc = 0.167  # (hr)
    Re = 10     # (mm)
    tr = np.arange(0, 60, 10)   # (min)

    print("\n" + "="*60)
    print("--- Unit Hydrograph Example ---")
    print("="*60)
    
    # Example: Use a 10-minute time interval
    tr_example = 10  # minutes
    
    # Step 1: Compute peak flow characteristics
    Tb, Tp, Qp = compute_peak_flow(Tc, A, Re, tr_example)
    
    print(f"\nWatershed Parameters:")
    print(f"  Area (A):                  {A} km²")
    print(f"  Time of Concentration (Tc): {Tc} hr")
    print(f"  Effective Precipitation (Re): {Re} mm")
    print(f"  Time Interval (tr):        {tr_example} min ({tr_example/60:.4f} hr)")
    
    print(f"\nComputed Hydrograph Characteristics:")
    print(f"  Base Time (Tb):            {Tb:.4f} hr")
    print(f"  Time to Peak (Tp):         {Tp:.4f} hr")
    print(f"  Peak Discharge (Qp):       {Qp:.4f} cms")
    
    # Step 2: Get interpolated unit hydrograph
    tr_hr = tr_example / 60  # Convert to hours
    T_interp, Q_interp = get_interpolated_unit_hdrograph(Tp, Qp, tr_hr)
    
    print(f"\nInterpolated Unit Hydrograph (interval = {tr_hr:.4f} hr):")
    print(f"{'Time (hr)':>12} | {'Discharge (cms)':>16}")
    print("-" * 32)
    for t, q in zip(T_interp, Q_interp):
        print(f"{t:12.4f} | {q:16.4f}")
        if t > Tb + 0.5:  # Show a bit past base time
            break
    
    print(f"\nTotal hydrograph points: {len(T_interp)}")


