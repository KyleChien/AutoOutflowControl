import numpy as np
from typing import Dict, List, Tuple, Any


def get_anti_diagonal_sums(matrix):
    """Compute anti-diagonal sums for hydrograph convolution"""
    matrix = np.array(matrix)
    # Flip matrix left-to-right to turn anti-diagonals into standard diagonals
    flipped = np.fliplr(matrix)
    
    # Range of diagonals for an N x M matrix is from -(rows-1) to (cols-1)
    rows, cols = matrix.shape
    sums = [flipped.diagonal(i).sum() for i in range(cols - 1, -rows, -1)]
    
    return sums


class HornerTable:
    """Compute Horner coefficients and precipitation data"""
    
    @staticmethod
    def get_coefficients(return_period: float) -> Dict[str, float]:
        """
        Get Horner coefficients for a given return period.
        Default coefficients based on typical urban drainage designs.
        """
        data = {
            2:   {"a": 1666.842, "b": 23.246, "c": 0.731},
            5:   {"a": 1914.351, "b": 34.037, "c": 0.694},
            10:  {"a": 2052.866, "b": 40.099, "c": 0.69},
            25:  {"a": 2184.709, "b": 44.84, "c": 0.693},
            50:  {"a": 2228.156, "b": 45.631, "c": 0.694},
            100: {"a": 2232.124, "b": 44.432, "c": 0.694},
        }
        
        if return_period in data:
            return data[return_period]
        
        # Find closest lower return period
        sorted_periods = sorted(data.keys())
        for p in reversed(sorted_periods):
            if return_period >= p:
                return data[p]
        return data[sorted_periods[0]]

    @staticmethod
    def compute_intensity(a: float, b: float, c: float, t: float) -> float:
        """Compute precipitation intensity using Horner formula: i = a / (t+b)^c"""
        return a / (t + b)**c

    @staticmethod
    def compute_intensity_table(horners: Dict[float, Dict[str, float]], 
                               durations: List[float]) -> Dict[float, Dict[float, float]]:
        """Compute precipitation intensity table"""
        table = {}
        for period, coeffs in horners.items():
            table[period] = {}
            for t in durations:
                intensity = HornerTable.compute_intensity(coeffs['a'], coeffs['b'], coeffs['c'], t)
                table[period][t] = round(intensity, 4)
        return table

    @staticmethod
    def compute_accumulated_table(intensity_table: Dict[float, Dict[float, float]], 
                                 durations: List[float]) -> Dict[float, Dict[float, float]]:
        """Compute accumulated precipitation table"""
        acc_table = {}
        for period in intensity_table:
            acc_table[period] = {}
            for t in durations:
                intensity = intensity_table[period][t]
                accumulation = intensity * t
                acc_table[period][t] = round(accumulation, 2)
        return acc_table


class HornerRainType:
    """Compute Horner rain type and hyetograph"""
    
    @staticmethod
    def compute_precipitation_list(horners: Dict[str, float], unit_duration: float, 
                                  max_duration: float = 24.0) -> Tuple[List[float], List[float]]:
        """Compute precipitation intensity and accumulated precipitation lists"""
        times = np.arange(0, max_duration + unit_duration, unit_duration)
        intensities = []
        accumulated = []
        
        for t in times:
            if t == 0:
                intensities.append(0)
                accumulated.append(0)
            else:
                intensity = HornerTable.compute_intensity(horners['a'], horners['b'], horners['c'], t * 60)  # Convert to minutes
                intensities.append(intensity)
                
                if len(accumulated) == 0:
                    acc = intensity * unit_duration
                else:
                    acc = accumulated[-1] + intensity * unit_duration
                accumulated.append(acc)
        
        return times.tolist(), intensities, accumulated

    @staticmethod
    def compute_unit_duration_precipitation(times: List[float], accumulated: List[float]) -> List[float]:
        """Compute discrete difference of accumulated precipitation"""
        unit_precip = [0]
        for i in range(1, len(accumulated)):
            unit_precip.append(accumulated[i] - accumulated[i-1])
        return unit_precip

    @staticmethod
    def alternating_block_sort(values: List[float]) -> List[float]:
        """Sort values using alternating block method"""
        sorted_values = sorted(values)
        result = []
        left = 0
        right = len(sorted_values) - 1
        
        while left <= right:
            if left == right:
                result.append(sorted_values[left])
            else:
                result.append(sorted_values[right])
                result.append(sorted_values[left])
            left += 1
            right -= 1
        
        return result[:len(values)]  # Ensure correct length

    @staticmethod
    def create_hyetograph(unit_precip_percent: List[float], total_24hr_precip: float) -> List[float]:
        """Create hyetograph by applying percentages to total precipitation"""
        return [p * total_24hr_precip / 100 for p in unit_precip_percent]


class EffectiveRainfall:
    """Compute effective rainfall using SCS curve number method"""
    
    @staticmethod
    def compute_s_and_ia_max(cn: int) -> Tuple[float, float]:
        """Compute S and Ia_max from curve number"""
        s = 25400 / cn - 254
        ia_max = 0.2 * s
        return s, ia_max

    @staticmethod
    def compute_cumulative_precipitation(hyetograph: List[float]) -> List[float]:
        """Compute cumulative precipitation from hyetograph"""
        cumulative = [0]
        for i in range(1, len(hyetograph)):
            cumulative.append(cumulative[-1] + hyetograph[i])
        return cumulative

    @staticmethod
    def compute_effective_rainfall(hyetograph: List[float], cn: int) -> List[float]:
        """Compute effective rainfall using SCS method"""
        s, ia_max = EffectiveRainfall.compute_s_and_ia_max(cn)
        cumulative = EffectiveRainfall.compute_cumulative_precipitation(hyetograph)
        
        effective_rainfall = []
        for i, p in enumerate(cumulative):
            if p <= ia_max:
                ia = p
            else:
                ia = ia_max
            
            if p <= ia_max:
                fa = 0
            else:
                fa = s * (p - ia_max) / (p - ia_max + s)
            
            pe = max(0, p - ia - fa)
            effective_rainfall.append(pe)
        
        # Compute discrete difference and convert mm to cm
        unit_effective = []
        for i in range(len(effective_rainfall)):
            if i == 0:
                diff = effective_rainfall[i]
            else:
                diff = effective_rainfall[i] - effective_rainfall[i-1]
            unit_effective.append(diff / 10)  # Convert mm to cm
        
        return unit_effective


class TimeConcentration:
    """Compute time of concentration"""
    
    @staticmethod
    def compute_overland_flow_time(length: float, elevation_diff: float, s: float) -> float:
        """Compute overland flow time T1"""
        if elevation_diff <= 0:
            return 0
        return (length ** 0.8) * ((s + 25.4) ** 0.7) / (4238 * (elevation_diff ** 0.5))

    @staticmethod
    def compute_channel_flow_time(length: float, manning_n: float, hydraulic_radius: float, 
                                 slope: float) -> float:
        """Compute channel flow time T2"""
        if hydraulic_radius <= 0 or slope <= 0:
            return 0
        velocity = (1 / manning_n) * (hydraulic_radius ** (2/3)) * (slope ** 0.5)
        return length / (3600 * velocity)  # Convert to hours

    @staticmethod
    def compute_time_of_concentration(length: float, elevation_diff: float, 
                                     manning_n: float, hydraulic_radius: float,
                                     slope: float) -> float:
        """Compute total time of concentration"""
        s, _ = EffectiveRainfall.compute_s_and_ia_max(50)  # Use default CN for slope calculation
        t1 = TimeConcentration.compute_overland_flow_time(length, elevation_diff, s)
        t2 = TimeConcentration.compute_channel_flow_time(length, manning_n, hydraulic_radius, slope)
        return t1 + t2


class DimensionlessUnitHydrograph:
    """Compute unit hydrograph and outflow hydrograph"""
    
    @staticmethod
    def get_default_dimensionless_uh() -> Tuple[np.ndarray, np.ndarray]:
        """Get default SCS dimensionless unit hydrograph"""
        T_Tp = np.array([
            0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 3.6, 3.8, 4.0, 4.5, 5.0,
        ])

        Q_Qp = np.array([
            0.000, 0.030, 0.100, 0.190, 0.310, 0.470, 0.660, 0.820, 0.930, 0.990, 1.000, 0.990,
            0.930, 0.860, 0.780, 0.680, 0.560, 0.460, 0.390, 0.330, 0.280, 0.207, 0.147, 0.107,
            0.077, 0.055, 0.040, 0.029, 0.021, 0.015, 0.011, 0.005, 0.000,
        ])
        return T_Tp, Q_Qp

    @staticmethod
    def compute_peak_flow(tc: float, area: float, unit_rainfall: float, unit_duration: float) -> Tuple[float, float, float]:
        """Compute peak flow characteristics"""
        t_lag = 0.6 * tc
        t_p = unit_duration / 2 + t_lag
        t_b = 2.67 * t_p
        q_p = 0.208 * area * unit_rainfall / t_p
        return t_b, t_p, q_p

    @staticmethod
    def compute_unit_hydrograph(t_p: float, q_p: float, time_ratios: List[float], 
                               discharge_ratios: List[float]) -> Tuple[List[float], List[float]]:
        """Compute unit hydrograph from dimensionless data"""
        T = [tr * t_p for tr in time_ratios]
        Q = [qr * q_p for qr in discharge_ratios]
        return T, Q

    @staticmethod
    def interpolate_unit_hydrograph(T: List[float], Q: List[float], 
                                  unit_duration: float) -> Tuple[List[float], List[float]]:
        """Interpolate unit hydrograph to specific time intervals"""
        T_interp = np.arange(0, max(T) + unit_duration, unit_duration)
        Q_interp = np.interp(T_interp, T, Q)
        return T_interp.tolist(), Q_interp.tolist()

    @staticmethod
    def compute_outflow_hydrograph(q_interp: List[float], re_values: List[float]) -> List[float]:
        """Compute outflow hydrograph through convolution"""
        matrix = []
        for re in re_values:
            scaled_q = [q * re for q in q_interp]
            matrix.append(scaled_q)
        
        return get_anti_diagonal_sums(matrix)