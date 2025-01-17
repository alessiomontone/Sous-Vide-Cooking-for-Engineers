import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit
from typing import Callable

from models.parameters import MeatSimulationParameters, LOG_REDUCTION_MIN_THRESHOLD
from models.helpers import MeasurementFormat


def SimulateMeat(msp: MeatSimulationParameters, progress_callback = None)-> (np.ndarray, np.ndarray, int):
    """
    Simulate the heat transfer in meat using the parameters defined in msp.
    
    Parameters:
        msp (MeatSimulationParameters): The parameters for the simulation.
        
        progress_callback (callable): A callback function that will be called at each iteration of the solver.
                                      None if no callback is needed.
                                      It shall accept 2 paramenters (t:float, y:np.ndarray) and returns a dummy value.
                                      
                                    e.g,
                                    def _progress_callback (t,y):
                                        print(f"{t}")
                                        return 1
                                        
    Returns:
        np.ndarray: The temperature distribution in the meat over time.
                    Shape (r,t) where r is the radial points and t is the time points.
                    r varies in np.linspace(0, msp.R, msp.N) and is measured in meters  
                    t varies in np.linspace(0, msp.t_max, int(msp.t_max/msp.dt)+1) and is measured in seconds
                    
        np.ndarray: The time points at which the temperature was evaluated.
                    Shape (t,) where t is the time points.
                    t varies in np.linspace(0, msp.t_max, int(msp.t_max/msp.dt)+1) and is measured in seconds
        int:        The instant (in seconds) at which thermal stability (i.e., Fluid temperature - 0.5°C has been reached).
                    None if no thermal stability has been reached.

    """ 

    dr = msp.radius / (msp.N_spatial_points - 1)  # Radial step size
    r = np.linspace(0, msp.radius, msp.N_spatial_points)  # Radial points from 0 to R
    t = np.linspace(0, msp.t_max, int(msp.t_max/msp.delta_time)+1)  # Time points

    # Define the heat equation with convective boundary conditions
    def heat_equation(t, T):
        dTdt = np.zeros_like(T)
        
        # Symmetry condition at r = 0
        dTdt[0] = msp.alpha * (2 / dr**2) * (T[1] - T[0])

        # Interior points
        for i in range(1, msp.N_spatial_points - 1):
            d2T_dr2 = (T[i+1] - 2*T[i] + T[i-1]) / dr**2
            radial_term = (msp.Beta / r[i]) * (T[i+1] - T[i-1]) / (2 * dr) if r[i] != 0 else 0
            dTdt[i] = msp.alpha * (d2T_dr2 + radial_term)
        
        # Convective boundary condition at the outer radius
        
        # Boundary Conditions
        # Explicit ghost point T(R+Delta R,t)
        T_ghost = T[-1] - dr * msp.h / msp.k * (T[-1] - msp.T_fluid)
        dTdt[-1] = msp.alpha * (
            # Second derivative
            (T[-2] - 2*T[-1] + T_ghost) / dr**2 +                 
            # Radial term
            (msp.Beta * (T_ghost - T[-2])/(2*dr))*(1/msp.radius)
        )
        
        return dTdt
        
    # Solve the PDE using SciPy's solve_ivp
    solution = solve_ivp(
        heat_equation,                 # ODE function
        (0, msp.t_max),                    # Time range
        np.full(msp.N_spatial_points, msp.T_initial),         # Initial condition (uniform temperature)
        method='RK45',                 # Solver
        t_eval=t,                       # Time points to evaluate
        events=progress_callback
    )

    # Extract the solution
    T_sol = solution.y
    time_points = solution.t

    # Check whether thermal stability has been reached
    threshold_temperature = msp.T_fluid - 0.5  # Threshold temperature
    center_temperatures = T_sol[0, :]

    # Find the first time where the center temperature exceeds the threshold
    second_stability_reached = None
    for i, temp in enumerate(center_temperatures):
        if temp >= threshold_temperature:
            second_stability_reached = time_points[i]
            break

    return T_sol, time_points, second_stability_reached

def LogReduction (center_temperature : np.ndarray, dt : int)-> (float, list):
    """
    Parameters
        np.ndarray:     Temperature at the center of the meat with a sample every dt (see next parameters)
        int:            Temporal granularity of the simulation is seconds
    
    Returns:
        float:          Overall Log-Reduction across the whole simulation
        list:           List of cumulative Log-Reduction (with the same temporal granularity as input data)
        safety_instant  Instant of the time (in seconds) when 6-log reduction has been reached
    """
    Dref = (2*60)/6 # 2 minutes for 6-log reduction (converted in seconds)
    Tref = 70       # # 70° of Reference temperature
    z = 7.5 # Z-value in °C

    # Initialize the cumulative temporal_evolution array
    temporal_evolution = []

    # Initialize the running sum
    total_sum = 0

    # Loop through each temperature and calculate the contribution
    for T_i in center_temperature:
        contribution = 10 ** ((T_i - Tref) / z) * dt
        total_sum += (1/Dref) * contribution
        temporal_evolution.append(total_sum)  # Add the current total_sum to the array

    # Calculate the final LR
    LR = total_sum

    safety_second = next((i*dt for i, value in enumerate(temporal_evolution) if value > LOG_REDUCTION_MIN_THRESHOLD), None)

    return LR, temporal_evolution, safety_second

def ExtrapolateHeatingCurve_1exp (measurements :pd.DataFrame, T_inf: float)-> Callable [[int], float]:
    
    """
    Parameters:
        pd.DataFrame:   DataFrame with the measurements, where first column is the time in minutes and second column is the temperature
        float:          Final temperature of the heating curve
        
    Returns:    
        Callable:       Function that extrapolates the heating curve at a given time"""


    # -------------------------------------------------------------------
    # 1) Define your two-term exponential model
    # -------------------------------------------------------------------
    def single_term_exponential(t, A, k1):
        """
        Two-term exponential model for temperature approach.
        T(t) = T_inf - A*exp(-k1*t)
        
        Interpretation:
        - T_inf : final/steady temperature
        - A  : amplitudes
        - k1 : rate constants
        """
        return T_inf - A * np.exp(-k1 * t)


    # -------------------------------------------------------------------
    # 2) Fit the two-term exponential model to the data
    # -------------------------------------------------------------------
    # We'll provide initial guesses (p0) for the parameters:
    #   [ A, B, k1, k2]
    p0 = [20.0,   0.1]  # just a rough guess

    popt, _ = curve_fit(single_term_exponential, measurements[MeasurementFormat.TIMESTAMP], measurements[MeasurementFormat.TEMPERATURE], p0=p0)
    # Fitted parameters: 
    # A_fit, k1_fit = popt

    # -------------------------------------------------------------------
    # 4) Create and return callable
    # -------------------------------------------------------------------
    def returned_function(t_fit):
        return single_term_exponential(t_fit, *popt)
    return returned_function


def ExtrapolateHeatingCurve_2exp (measurements :pd.DataFrame, T_inf: float)-> Callable [[int], float]:
    
    """
    Parameters:
        pd.DataFrame:   DataFrame with the measurements, where first column is the time in minutes and second column is the temperature
        float:          Final temperature of the heating curve
        
    Returns:    
        Callable:       Function that extrapolates the heating curve at a given time"""


    # -------------------------------------------------------------------
    # 1) Define your two-term exponential model
    # -------------------------------------------------------------------
    def two_term_exponential(t, A, B, k1, k2):
        """
        Two-term exponential model for temperature approach.
        T(t) = T_inf - A*exp(-k1*t) - B*exp(-k2*t)
        
        Interpretation:
        - T_inf : final/steady temperature
        - A, B  : amplitudes
        - k1, k2: rate constants
        """
        return T_inf - A * np.exp(-k1 * t) - B * np.exp(-k2 * t)


    # -------------------------------------------------------------------
    # 2) Fit the two-term exponential model to the data
    # -------------------------------------------------------------------
    # We'll provide initial guesses (p0) for the parameters:
    #   [ A, B, k1, k2]
    p0 = [20.0,  5.0,  0.1,  0.01]  # just a rough guess

    popt, _ = curve_fit(two_term_exponential, measurements[MeasurementFormat.TIMESTAMP], measurements[MeasurementFormat.TEMPERATURE], p0=p0)
    # Fitted parameters: 
    # A_fit, B_fit, k1_fit, k2_fit = popt

    # -------------------------------------------------------------------
    # 4) Create and return callable
    # -------------------------------------------------------------------
    def returned_function(t_fit):
        return two_term_exponential(t_fit, *popt)
    return returned_function

    