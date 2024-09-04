# Use the official Python image from the Docker Hub
# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /project

COPY project/ /project/

# Copy the requirements file into the container
COPY requirements.txt requirements.txt

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that the app will run on
EXPOSE 8000

# Run the Flask app with waitress
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8000", "app:app"]