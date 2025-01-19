# Sous-vide cooking for engineers

The Sous Vide simulation used is providing different tools to support users in Sous Vide cooking, taking care of the state-of-the-art safety directions.

## Configure and launch in Python environment

* Clone source code repository: `git clone https://github.com/alessiomontone/Sous-Vide-Cooking-for-Engineers.git`
* Install dependencies: `pip install -r requirements.txt`
* Launch the application `streamlit run './app/Cooking_for_Engineers.py'`

## Building and running Docker Container

* `docker build --pull --rm -f "Dockerfile" -t sousvidecooking4eng:latest "."`
* `docker run -p 8501:8501 sousvidecooking4eng:latest`

## Other Links

* [👉Full Documentation](https://alessiomontone.github.io/Sous-Vide-Cooking-for-Engineers): including User Guide, source code documentation and underlying math (sources can be found in `docs/source` folder of this repository or build in branch `gh-pages`)
* [Demo videos](https://www.youtube.com/playlist?list=PLzwJW5sljwwQYk3AT2GME1ekr7CBrH8lL) showing the use of basic functionalities


## References

* The simulation tool is based on the paper by Douglas E. Baldwin, _Sous vide cooking: A review, International Journal of Gastronomy and Food Science_, vol. 1(1), pp. 15–30 (2012). [Download PDF](https://douglasbaldwin.com/Baldwin-IJGFS-Preprint.pdf)
* The Thermal Diffusivity coefficients are taken from Pedro D. Sanz et al., 
_Thermophysical Properties of Meat Products: General Bibliography and Experimental Values_ [Download PDF](https://www.researchgate.net/publication/286657774)
