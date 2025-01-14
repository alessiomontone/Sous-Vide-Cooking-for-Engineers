# Cooking For Engineers

The simulation tool is based on the paper by Douglas E. Baldwin, _Sous vide cooking: A review, International Journal of Gastronomy and Food Science_, vol. 1(1), pp. 15–30 (2012). [Download PDF](https://douglasbaldwin.com/Baldwin-IJGFS-Preprint.pdf)

The Thermal Diffusivity coefficients are taken from Pedro D. Sanz et al., 
_Thermophysical Properties of Meat Products: General Bibliography and Experimental Values_ [Download PDF](https://www.researchgate.net/publication/286657774)

## Configure and launch in Python Environment

* Install dependencies: `pip install -r requirements.txt`
* Launch the application `streamlit run './app/🏠 Home.py'`

## Building and running Docker Container
* `docker build --pull --rm -f "Dockerfile" -t sousvidecooking4eng:latest "."`
* `docker run -p 8501:8501 sousvidecooking4eng:latest`

## Details
Further details, including mathematical continuous and discrete formalization, can be find in the documentaion
Mathematical details besides the implementation is provided in the [documentation](docs/build/index.html)
