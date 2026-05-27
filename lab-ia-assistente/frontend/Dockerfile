FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with better error handling
RUN npm cache clean --force && \
    npm install --prefer-offline --no-audit --legacy-peer-deps && \
    npm cache clean --force

COPY . .

EXPOSE 3000

ENV REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_API_BASE=/api/v1

CMD ["npm", "start"]
