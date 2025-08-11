# CEX Stock Checker - Docker Setup

This document explains how to run the CEX Stock Checker with its web UI using Docker.

## Quick Start

1. **Clone the repository and navigate to it:**
   ```bash
   git clone https://github.com/yourusername/cex-stock-checker.git
   cd cex-stock-checker
   ```

2. **Set up configuration** (optional):
   ```bash
   cp .env.example .env
   # Edit .env if needed for custom config paths
   ```

3. **Start the application:**
   ```bash
   docker-compose up -d
   ```

4. **Access the web interface:**
   Open your browser to http://localhost:5000

## Environment Setup

### Discord Notification Configuration

This application uses Discord webhooks for notifications:

1. **Go to your Discord server**
2. **Navigate to Server Settings > Integrations**
3. **Click "Webhooks" > "Create Webhook"**
4. **Choose a channel and copy the webhook URL**
5. **In the web interface:**
   - Go to Settings
   - Enable Discord notifications
   - Paste your webhook URL
   - Choose notification mode (every check or stock changes only)
   - Save settings

## Docker Commands

### Using Docker Compose (Recommended)

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Rebuild after code changes
docker-compose up --build -d
```

### Using Docker directly

```bash
# Build the image
docker build -t cex-stock-checker .

# Run the container
docker run -d \
  --name cex-stock-checker \
  -p 5000:5000 \
  -e GMAIL_USERNAME="your.email@gmail.com" \
  -e GMAIL_APP_PASSWORD="your-app-password" \
  -e NOTIFICATION_EMAIL="notifications@example.com" \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  cex-stock-checker
```

## Web Interface Features

### Dashboard
- **View all monitored products** with real-time stock status
- **Add new products** by entering CEX product IDs
- **Remove products** from monitoring
- **Start/Stop the stock checker** service
- **Next check countdown timer** when running
- **Auto-refresh** when checker is running
- **Latest Discord webhook preview**

### Settings
- **Configure check intervals** (minimum 60 seconds)
- **Discord webhook notifications** (enable/disable)
- **Notification modes**: Send on every check or only when items are in stock
- **Discord webhook URL configuration**
- **Webhook logs history** with delivery status
- **Discord setup instructions**

### Product Management
- **Add products** by CEX product ID (e.g., SHDDSYNDS1821P8BDL)
- **View product details** including name, stock status, and history
- **Quick links** to CEX product pages
- **Stock history tracking** (last in stock, times in stock)

## Data Persistence

The following directories are mounted as volumes for data persistence:

- `./config` - Configuration files
- `./data` - Stock history, debug files, and logs

## Configuration

The application uses the `config/checker.yaml` configuration:

```yaml
items:
  - SHDDSYNDS1821P8BDL  # Product IDs to monitor

request_delay: 1800  # Check interval in seconds (30 minutes)

# Discord notifications
discord_enabled: true

# Notification modes:
# - 'all_checks': Send notification for every check (default)
# - 'stock_changes': Only send notification when items are in stock
notification_mode: "all_checks"

store_ids: []  # Empty for general availability

discord:
  webhook_url: ""  # Discord webhook URL for notifications
```

## Health Checks

The Docker Compose setup includes health checks:
- **Endpoint:** http://localhost:5000/
- **Interval:** Every 30 seconds
- **Timeout:** 10 seconds
- **Retries:** 3 attempts

## Troubleshooting

### Check logs:
```bash
docker-compose logs -f cex-stock-checker
```

### Check container status:
```bash
docker-compose ps
```

### Restart the application:
```bash
docker-compose restart
```

### Reset everything:
```bash
docker-compose down
docker-compose up --build -d
```

## Ports

- **5000** - Web interface (http://localhost:5000)

## Security Notes

- Environment variables are used for sensitive data (passwords)
- The application runs as non-root in the container
- Only necessary ports are exposed
- Health checks ensure the service is running properly