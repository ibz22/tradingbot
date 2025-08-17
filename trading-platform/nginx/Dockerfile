# Nginx Dockerfile
FROM nginx:alpine

# Copy custom nginx configuration
COPY conf.d/default.conf /etc/nginx/conf.d/default.conf

# Create directory for SSL certificates
RUN mkdir -p /etc/nginx/ssl

# Expose ports
EXPOSE 80 443

# Start nginx
CMD ["nginx", "-g", "daemon off;"]