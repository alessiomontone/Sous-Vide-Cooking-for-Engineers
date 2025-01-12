# Cooking For Engineers

The simulation tool is based on the paper by Douglas E. Baldwin, _Sous vide cooking: A review, International Journal of Gastronomy and Food Science_, vol. 1(1), pp. 15–30 (2012). [Download PDF](https://douglasbaldwin.com/Baldwin-IJGFS-Preprint.pdf)

# Mathematical basis

All the modeling is based on the thermal exchange equation in cylindric coordinates

$$ 
\begin{cases}
T_t = \alpha \left\{ T_{rr} + \beta \frac{T_r}{r} \right\}, \\
T(r, 0) = T_0, \quad T_r(0, t) = 0, \\
T_r(R, t) = \frac{h}{k} \left\{ T_{\text{Water}} - T(R, t) \right\},
\end{cases} \tag{*}
$$
 
Where: 
* $r \in [0,R]$, representing the distance from the center of the food $0$ is the center, $R$ is the border at direct contect with the water
* $ T_0 $, is the initial temprature of the food, generally 5°C  
* $T(r,t)$, representing the temperature of the food at distance $r$ from the center at time $t$
* $ \beta $, representing the geometry of the shape ($0$ for slab, $1$ for cylinder and $2$ for sphere)
* $ T_{\text{Water}} $, representing the temperature set and maintained by the Roner

Furthermore, the reduction of the pathogens the Logaritmic Reduction (LR) is computed as follows
$$
\text{LR} = \frac{1}{D_{\text{Ref}}} \int_0^t 10^{\frac{T(t') - T_{\text{Ref}}}{z}} \, dt',
$$

Where_
* $D_{\text{Ref}}$ is equal to $ [\bullet] $ 

## Discrete version
The above funcit

