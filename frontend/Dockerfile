# Production multi-stage Dockerfile for React Vite frontend
FROM node:20-alpine as build

WORKDIR /app

# Install package dependencies
COPY package*.json ./
RUN npm ci

# Copy sources and compile TypeScript bundle
COPY . .
RUN npm run build

# Stage 2: Serve statically with lightweight Nginx
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Custom nginx config to support React client-side routing
RUN echo 'server { \
    listen 5173; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass http://backend:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]
