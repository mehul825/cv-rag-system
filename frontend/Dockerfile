# Use Node.js LTS image
FROM node:20-alpine

# Set work directory
WORKDIR /app

# Copy package files
COPY package*.json /app/

# Install dependencies
RUN npm install

# Copy application code
COPY . /app/

# Expose Vite dev server port
EXPOSE 5173

# Run Vite dev server
CMD ["npm", "run", "dev"]
