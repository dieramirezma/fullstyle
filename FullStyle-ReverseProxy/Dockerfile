FROM nginx:1.25-alpine

# Install additional tools and SSL utilities
RUN apk add --no-cache \
    curl \
    openssl \
    ca-certificates \
    && mkdir -p /usr/share/nginx/html/error \
    && mkdir -p /var/log/nginx/waf \
    && mkdir -p /etc/ssl/certs \
    && mkdir -p /etc/ssl/private \
    && mkdir -p /var/www/html/.well-known/acme-challenge

# Generate DH parameters for SSL
RUN openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048

# Generate self-signed certificate for development
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/fullstyle.key \
    -out /etc/ssl/certs/fullstyle.crt \
    -subj "/C=CO/ST=Bogota/L=Bogota/O=FullStyle/CN=localhost"

# Copy NGINX configuration with SSL and WAF
COPY nginx-lb-basic.conf /etc/nginx/nginx.conf

# Create basic error pages with SSL branding
RUN echo '<!DOCTYPE html><html><head><title>404 Not Found</title><style>body{font-family:Arial,sans-serif;background:#f4f4f4;color:#333;text-align:center;padding:50px;}h1{color:#e74c3c;}.ssl-badge{background:#27ae60;color:white;padding:5px 10px;border-radius:3px;font-size:12px;}</style></head><body><div class="ssl-badge">🔒 SSL Protected</div><h1>404 Not Found</h1><p>The requested resource was not found on this server.</p></body></html>' > /usr/share/nginx/html/404.html && \
    echo '<!DOCTYPE html><html><head><title>500 Internal Server Error</title><style>body{font-family:Arial,sans-serif;background:#f4f4f4;color:#333;text-align:center;padding:50px;}h1{color:#e74c3c;}.ssl-badge{background:#27ae60;color:white;padding:5px 10px;border-radius:3px;font-size:12px;}</style></head><body><div class="ssl-badge">🔒 SSL Protected</div><h1>500 Internal Server Error</h1><p>The server encountered an unexpected condition.</p></body></html>' > /usr/share/nginx/html/50x.html && \
    echo '<!DOCTYPE html><html><head><title>429 Too Many Requests</title><style>body{font-family:Arial,sans-serif;background:#f4f4f4;color:#333;text-align:center;padding:50px;}h1{color:#f39c12;}.ssl-badge{background:#27ae60;color:white;padding:5px 10px;border-radius:3px;font-size:12px;}</style></head><body><div class="ssl-badge">🔒 SSL Protected</div><h1>429 Too Many Requests</h1><p>Rate limit exceeded. Please try again later.</p></body></html>' > /usr/share/nginx/html/429.html && \
    echo '<!DOCTYPE html><html><head><title>403 Forbidden</title><style>body{font-family:Arial,sans-serif;background:#f4f4f4;color:#333;text-align:center;padding:50px;}h1{color:#e74c3c;}.ssl-badge{background:#27ae60;color:white;padding:5px 10px;border-radius:3px;font-size:12px;}</style></head><body><div class="ssl-badge">🔒 SSL Protected</div><h1>403 Forbidden</h1><p>Access denied by WAF security rules.</p></body></html>' > /usr/share/nginx/html/403.html

# Set permissions for SSL certificates
RUN chown -R nginx:nginx /etc/ssl/private && \
    chmod 600 /etc/ssl/private/fullstyle.key && \
    chmod 644 /etc/ssl/certs/fullstyle.crt

# Expose both HTTP and HTTPS ports
EXPOSE 80 443

# Health check with SSL awareness
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ssl-status || exit 1

CMD ["nginx", "-g", "daemon off;"]