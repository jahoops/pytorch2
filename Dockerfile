# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Install build-essential, x11-apps, and clean up
RUN apt-get update && apt-get install -y \
    build-essential \
    x11-apps \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

    # Upgrade pip
RUN pip install --upgrade pip

# Install PyTorch
RUN pip install torch torchvision

# Install other dependencies
RUN pip install numpy pygame debugpy

# Set the working directory
WORKDIR /pytorch2

# Copy your project files into the container
COPY . /pytorch2

# Ensure the script is executable
RUN chmod +x /pytorch2/main.py

# Expose the debug port
EXPOSE 5678

# Run your main script
CMD ["python", "/pytorch2/main.py"]