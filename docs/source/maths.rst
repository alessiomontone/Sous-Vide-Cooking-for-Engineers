Mathematical basis
==================

The simulation tool is based on the paper by Douglas E. Baldwin, *Sous vide cooking: A review, International Journal of Gastronomy and Food Science*, vol. 1(1), pp. 15–30 (2012). `Download PDF <https://douglasbaldwin.com/Baldwin-IJGFS-Preprint.pdf>`_

Continuous model
----------------

All the modeling is based on the heat conduction exchange equation in cylindric coordinates:

.. math::

    \begin{equation}
        \begin{cases}
        T_t = \alpha \big[ T_{rr} + \beta \frac{T_r}{r} \big], \\
        T(r, 0) = T_0, \quad T_r(0, t) = 0, \\ 
        T_r(R, t) = \frac{h}{k} \lbrace T_{\text{Water}} - T(R, t) \rbrace 
        \end{cases} \tag{*}
    \end{equation}
    


where: 

* :math:`T_t \equiv \partial T / \partial t`, :math:`T_r \equiv \partial T / \partial r`, :math:`T_{rr} \equiv \partial ^2 T/\partial r^2`
* :math:`r \in [0,R]`, representing the distance from the center of the food :math:`0` is the center, :math:`R` is the border at direct contect with the water
* :math:`T_0`, is the initial temprature of the food, generally 5°C  
* :math:`T(r,t)`, representing the temperature of the food at distance :math:`r` from the center at time :math:`t`
* :math:`\beta`, representing the geometry of the shape (:math:`0` for slab, :math:`1` for cylinder and :math:`2` for sphere)
* :math:`T_{\text{Water}}`, representing the temperature set and maintained by the Roner

Furthermore, the reduction of the pathogens the Logaritmic Reduction (LR) is computed as follows:

.. math::
    
    \text{LR} = \frac{1}{D_{\text{Ref}}} \int_0^t 10^{\frac{T(t') - T_{\text{Ref}}}{z}} dt', \tag{**}


where 

* :math:`D_{\text{Ref}}` is equal to :math:`20s^{-1}`  

Discrete model
--------------

The simulator is based on :code:`Scipy` solver, accordingly a discretize version of the equation :math:`(*)` has been used and below you may find the considerations behind the code.

Heat conduction
~~~~~~~~~~~~~~~

The main equation in spherical coordinates :math:`T_t = \alpha \lbrace T_{rr} + \beta \frac{T_r}{r} \rbrace` is discretizez as follows:

* for :math:`r=0` (center of the heated body):

.. math::
    \frac{\partial T}{\partial t} = \alpha \frac{\partial ^2 T}{\partial r ^2} \approx \frac{T(\Delta r,t)-T(0,t)}{\Delta r^2 / 2} \tag{i}


*   for :math:`r\in (0,R)`, each term will be approximated with discretization, particularly:

    .. math::

        \begin{aligned}
        &\frac{\partial ^2 T}{\partial r^2} \approx \frac {T(r+\Delta r,t)- 2T(r,t)+T(r-\Delta r,t)}{\Delta r^2},  \\[10pt]
        &\frac{\partial T}{\partial r} \approx \frac {T(r+\Delta r,t)-T(r-\Delta r)}{2 \Delta r}
        \end{aligned}

    and putting all together

    .. math::

        \begin{equation}
            \begin{aligned}
            \frac{\partial T}{\partial t} \approx \alpha & \bigg[ \frac {T(r+\Delta r,t)- 2T(r,t)+T(r-\Delta r,t)}{\Delta r^2}+ \\[10pt]
            &+\frac {T(r+\Delta r,t)-T(r-\Delta r)}{2 \Delta r} \bigg] 
            \end{aligned} \tag{ii}
        \end{equation}
    

Boundary Conditions
~~~~~~~~~~~~~~~~~~~

Heat transfer at the border with the fluid (i.e., :math:`r=R`) are modeled putting together Newton's law of heating and Fourier's thermal conductivity law, giving:

.. math::

    \text{Heat transfer} = k \frac{\partial T}{\partial r} \bigg|_{r=R} = -h \big(T(R,t) - T_\text{Water} \big)

and performing a discrete approximation of the left hand side, where :math:`T_{\text{Ghost}} \equiv T(R+\Delta r,t)` is a fictious point outside the food:

.. math::

    k\frac{T_{\text{Ghost}}-T(R, t)}{\Delta r} \approx -h \big(T(R,t) - T_\text{Water} \big)

and rearranging to explicitly write for the fictious point :math:`T_{\text{Ghost}}`

.. math::

    T_{\text{Ghost}} = T(R,t)-\frac{h \Delta r}{k}\big(T(R,t) - T_\text{Water} \big)


Coming back to the main heat conduction equation, evaluating for :math:`r=R`, performing discrete approximation and susbsituting previously computed formula for the temperature of fictious point:

.. math::

    \begin{equation}
        \begin{aligned}
        \frac{\partial T}{\partial t} \bigg|_{r=R} &= \alpha \bigg[ T_{rr} + \beta \frac{T_r}{r} \bigg] \bigg|_{r=R} \\
        &\approx \alpha \bigg[ \frac{T(R-\Delta r,t)-2T(R,t)+ T(R+\Delta r,t)}{\Delta r^2} + \beta \frac{T_\text{Ghost}-T(R-\Delta r,t)}{2R \Delta r} \bigg] \\
        \end{aligned} \tag{iii}
    \end{equation}

Python Code
~~~~~~~~~~~

By mapping equation terms into the following variables:

* :math:`T(r,t)` as :code:`T[r]` for a given :code:`t`
* :math:`\partial T / \partial t (r,t)` as :code:`DTdt[r]` for a given :code:`t`
* :math:`\Delta r` as :code:`dr`

equations :math:`(i)`, :math:`(ii)`, :math:`(iii)` can be coded in Python as follows:

.. code-block:: python

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