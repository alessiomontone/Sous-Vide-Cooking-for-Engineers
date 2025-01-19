# Use the official Python image as a base
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port on which the Streamlit app runs (default is 8501)
EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "app/Cooking_for_Engineers.py", "--server.port=8501", "--server.address=0.0.0.0"]
