# Use Python as base
FROM python:3.11-slim

# Install C++ compiler and tools
RUN apt-get update && apt-get install -y \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Compile the C++ logic during the build stage
RUN g++ -O3 logic/stego.cpp -o logic/encoder.exe
RUN g++ -O3 logic/stego.cpp -o logic/decoder.exe

# Ensure the binaries are executable (important for Linux-based Render)
RUN chmod +x logic/encoder.exe logic/decoder.exe

# Start the server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
