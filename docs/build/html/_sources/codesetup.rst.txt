Source Code
===========

**Clone Repository**

* Get sources code form the public repository  :code:`git clone https://github.com/alessiomontone/Sous-Vide-Cooking-for-Engineers.git` 

**Configure and launch in Python Environment**

* Install dependencies: :code:`pip install -r requirements.txt`
* Launch the application :code:`streamlit run './app/Cooking_for_Engineers.py'`

**Building and running a Docker Container**

* :code:`docker build --pull --rm -f "Dockerfile" -t sousvidecooking4eng:latest "."`
* :code:`docker run -p 8501:8501 sousvidecooking4eng:latest`
