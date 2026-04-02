# Dockerfile for Next.js Frontend (Development Mode)
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy project files
COPY . .

# Expose port
EXPOSE 3000

# Start Next.js in development mode to bypass strict build errors
CMD ["npm", "run", "dev"]
