import numpy as np
from scipy.integrate import solve_ivp

from models.parameters import MeatSimulationParameters

def SimulateMeat(msp: MeatSimulationParameters)-> (np.ndarray, np.ndarray):
    """
    Simulate the heat transfer in meat using the parameters defined in msp.
    
    Parameters:
    msp (MeatSimulationParameters): The parameters for the simulation.
    
    Returns:
        np.ndarray: The temperature distribution in the meat over time.
                    Shape (r,t) where r is the radial points and t is the time points.
                    r varies in np.linspace(0, msp.R, msp.N) and is measured in meters  
                    t varies in np.linspace(0, msp.t_max, int(msp.t_max/msp.dt)+1) and is measured in seconds
                    
        np.ndarray: The time points at which the temperature was evaluated.
                    Shape (t,) where t is the time points.
                    t varies in np.linspace(0, msp.t_max, int(msp.t_max/msp.dt)+1) and is measured in seconds
    """ 

    dr = msp.R / (msp.N - 1)  # Radial step size
    r = np.linspace(0, msp.R, msp.N)  # Radial points from 0 to R
    t = np.linspace(0, msp.t_max, int(msp.t_max/msp.dt)+1)  # Time points

    # Define the heat equation with convective boundary conditions
    def heat_equation(t, T):
        dTdt = np.zeros_like(T)
        
        # Symmetry condition at r = 0
        #dTdt[0] = alpha * (T[1] - T[0]) / dr**2
        dTdt[0] = msp.alpha * (2 / dr**2) * (T[1] - T[0])

        # Interior points
        for i in range(1, msp.N - 1):
            d2T_dr2 = (T[i+1] - 2*T[i] + T[i-1]) / dr**2
            radial_term = (msp.Beta / r[i]) * (T[i+1] - T[i-1]) / (2 * dr) if r[i] != 0 else 0
            dTdt[i] = msp.alpha * (d2T_dr2 + radial_term)
        
        # Convective boundary condition at the outer radius
        dTdt[-1] = msp.alpha * (1 / dr**2) * (T[-2] - T[-1] - (dr * msp.h / msp.k) * (T[-1] - msp.T_fluid))
        
        return dTdt

    # Solve the PDE using SciPy's solve_ivp
    solution = solve_ivp(
        heat_equation,                 # ODE function
        (0, msp.t_max),                    # Time range
        np.full(msp.N, msp.T_initial),         # Initial condition (uniform temperature)
        method='RK45',                 # Solver
        t_eval=t                       # Time points to evaluate
    )

    # Extract the solution
    T_sol = solution.y
    time_points = solution.t
    
    return T_sol, time_points

def LogReduction (center_temperature : np.ndarray)-> (float, list):
    Dref = 2/6 # 2 minutes for 6-log reduction
    Tref = 70 # Reference temperature in °C
    z = 7.5 # Z-value in °C

    # Initialize the cumulative temporal_evolution array
    temporal_evolution = []

    # Initialize the running sum
    total_sum = 0

    # Loop through each temperature and calculate the contribution
    for T_i in center_temperature:
        contribution = 10 ** ((T_i - Tref) / z)
        total_sum += (1/Dref) * contribution
        temporal_evolution.append(total_sum)  # Add the current total_sum to the array

    # Calculate the final LR
    LR = total_sum
    return LR, temporal_evolution