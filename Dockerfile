# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the root of the project
WORKDIR /app

# Copy the requirements file into the container
COPY space-weather-chatbot/requirements.txt /app/

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project into the container
COPY . /app/

# Expose the port that uvicorn runs on
EXPOSE 8000

# Change working directory so that uvicorn can find main.py and prediction_loader.py paths resolve correctly
# prediction_loader.py looks for model.pkl at ../../model.pkl relative to its location
WORKDIR /app/space-weather-chatbot/backend

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
