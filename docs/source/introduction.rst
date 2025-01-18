Introduction & Set-up
=====================

The simulation tool is based on the paper by Douglas E. Baldwin, *Sous vide cooking: A review, International Journal of Gastronomy and Food Science*, vol. 1(1), pp. 15–30 (2012). `Download PDF <https://douglasbaldwin.com/Baldwin-IJGFS-Preprint.pdf>`_

The Thermal Diffusivity coefficients are taken from Pedro D. Sanz et al., *Thermophysical Properties of Meat Products: General Bibliography and Experimental Values* `Download PDF <https://www.researchgate.net/publication/286657774>`_

Set-up
------

**Configure and launch in Python Environment**

* Install dependencies: :code:`pip install -r requirements.txt`
* Launch the application :code:`streamlit run './app/🏠 Home.py'`

**Building and running a Docker Container**

* :code:`docker build --pull --rm -f "Dockerfile" -t sousvidecooking4eng:latest "."`
* :code:`docker run -p 8501:8501 sousvidecooking4eng:latest`

