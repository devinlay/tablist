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
RUN apt-get update; apt-get clean

# Install wget.
RUN apt-get install -y wget

RUN apt-get install -y gnupg

# Set the Chrome repo.
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

# Install Chrome.
RUN apt-get update && apt-get -y install google-chrome-stable

# Expose the port that the app will run on
EXPOSE 8000

# Run the Flask app with waitress
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8000", "app:app"]