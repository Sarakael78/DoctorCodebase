# Use an appropriate base image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the application files
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose the port
EXPOSE 7860

# Add the required label
LABEL Name="My Gradio App"
LABEL Description="A Gradio application for demonstration purposes."
LABEL Maintainer="your_email@example.com"
LABEL License="MIT"
LABEL Version="1.0"


# Command to run the application
CMD ["python", "allcode"]