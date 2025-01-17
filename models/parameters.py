import json
import pandas as pd
import numpy as np

LOG_REDUCTION_MIN_THRESHOLD = 6

class MeatSimulationParameters:
    def __init__(self):
        self._Thickness = 50e-3                      # Thickness of the meat (in m)
        self._Beta = 1.0                             # Coefficient for the geometry term (set to 0 for slab, 1 for cylinder and 2 for sphere, 1.25 for cube)
        
        self.T_fluid = 58.0                         # Fluid temperature in °C
        self.T_initial = 5.0                        # Initial temperature of the cylinder in °C
        self.simulation_hours = 4                   # Simulation time in hours
        self.alpha = 1.11e-7                        # Thermal diffusivity in m^2/s
        self.k = 0.48                               # Thermal conductivity in W/(m·K)
        self.h = 95                                 # Convective heat transfer coefficient in W/(m^2·K)
        self.N_spatial_points = 30                  # Spatial Simulation Granularity: number of radial points used to solve the equations 
        self.delta_time = 60                        # Simulation Granularity: Time step in seconds used for equation evalution/solve

    # Geometry properties
    ####
    
    @property
    def Thickness(self):
        return self._Thickness

    @Thickness.setter
    def Thickness(self, value):
        raise AttributeError("Direct modification of Thickness is not allowed. Use the define_meat_shape method.")

    @property
    def Beta(self):
        return self._Beta

    @Beta.setter
    def Beta(self, value):
        raise AttributeError("Direct modification of Beta is not allowed. Use the define_meat_shape method.")
    
    @property
    def Beta_correction_large_slabs(self):
        return self._Beta_correction_large_slabs

    @Beta_correction_large_slabs.setter
    def Beta_correction_large_slabs(self, value):
        raise AttributeError("Direct modification of Beta correction for large slabs is not allowed. Use the define_meat_shape method.")
    
    def define_meat_shape(self, shape:str, thickness_mm:int, thick_slabs_beta_correction:bool=True):
        """
        Modify Thickness and Beta concurrently based on the shape.

        Parameters:
        thickness (float): New thickness of the meat (in mm).
        shape (str): Shape of the meat, must be one of ["cylinder", "slab", "sphere"].
        thick_slabs_beta_correction (bool): If True, adjust Beta for thick slabs according to the note of Table 2 in Baldwin's paper.
                                            (i.e., suggested for pasteurizaton) | If None, default is True
        """
        # if Beta correction is None, then default True value will be used
        if thick_slabs_beta_correction is None:
            thick_slabs_beta_correction = True
            
        if shape not in ["cylinder", "slab", "sphere"]:
            raise ValueError("Invalid shape. Must be one of: 'cylinder', 'slab', 'sphere'.")

        shape_to_beta = {
            "slab": 0,
            "cylinder": 1,
            "sphere": 2
        }
        
        self._Thickness = thickness_mm * 1e-3
        self._Beta = shape_to_beta[shape]
        self._Beta_correction_large_slabs = thick_slabs_beta_correction
        
        # Correction for thick slabs
        if thick_slabs_beta_correction:
            if (shape == "slab") and (self._Thickness > 30e-3): # If slab and thickness > 30mm, adjust Beta to 0.28 (see Baldwin 2011, page 12)
                self._Beta = 0.28
    
    # Helpers properties
    ####
    
    @property
    def radius (self): # Radius of the cylinder (m)      
        return self.Thickness / 2
    
    @property
    def t_max(self): # Maximum simulation time in seconds
        return self.simulation_hours * 3600
    
    @property
    def list_radius_values(self):
        return np.linspace(0, self.radius, self.N_spatial_points)
    
    @property
    def thermal_stability_threshold(self):
        return self.T_fluid - 0.5

    # Helper functions
    ####
    
    def to_dict(self):
        return {
            "Thickness": self.Thickness,
            "Beta": self.Beta,
            "Beta_correction_large_slabs": self.Beta_correction_large_slabs,
            "T_fluid": self.T_fluid,
            "T_initial": self.T_initial,
            "simulation_hours": self.simulation_hours,
            "alpha": self.alpha,
            "k": self.k,
            "h": self.h,
            "N_spatial_points": self.N_spatial_points,
            "Radius": self.radius,
            "t_max": self.t_max,
            "dt": self.delta_time
        }
        
    def to_monospace_str(self):
        return f"""
Thickness           = {self.Thickness}
Beta                = {self.Beta}
Beta corr. large sl.= {self.Beta_correction_large_slabs}
T Initial           = {self.T_initial}
T Roner             = {self.T_fluid}
Simulation time (h) = {self.simulation_hours}
Diffusivity (alpha) = {self.alpha:.2e}
Conductivity (k)    = {self.k}
Surface Heat t. (h) = {self.h}
#Spatial points (N) = {self.N_spatial_points}
Radius of food (R)  = {self.radius}
Simulated seconds   = {self.t_max}
Smallest time int.  = {self.delta_time}
"""

    def to_json(self):
        import json
        return json.dumps(self.to_dict(), indent=4)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(list(self.to_dict().items()), columns=["Key", "Value"])