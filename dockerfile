# Use official Python 3.12.3 slim image as the base
FROM python:3.12.3-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements.txt first (if you have one) to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Define the command to run your application
# CMD ["sh", "-c", "python main.py"]
CMD ["sh", "-c", "python main.py > /app/output/fit.log"]