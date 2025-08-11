# 🚀 CEX Stock Checker - Server Deployment Guide

## Quick Start with Docker Compose

### **🚀 Super Quick Deploy (No Git Clone Required)**
```bash
# Download standalone compose file
wget https://raw.githubusercontent.com/klueanon/cex-uk-stock-checker/main/docker-compose.standalone.yml

# Deploy immediately
docker-compose -f docker-compose.standalone.yml up -d
```

### **📦 Traditional Method**

#### 1. **Clone the Repository**
```bash
git clone https://github.com/klueanon/cex-uk-stock-checker.git
cd cex-uk-stock-checker
```

#### 2. **Choose Your Deployment Method**

**Option A: Basic Setup**
```bash
# Builds from GitHub automatically
docker-compose up -d
```

**Option B: Production (Recommended)**
```bash
# Create required directories
mkdir -p config data

# Set proper permissions (Linux/macOS)
sudo chown -R 1000:1000 config data

# Start with production settings
docker-compose -f docker-compose.prod.yml up -d
```

### 3. **Initial Configuration**

**If using standalone method:**
```bash
# Config directories are created automatically
# Configure everything via web UI at http://your-server:5000/settings
```

**If cloned repository:**
```bash
# Copy example config
cp config/checker.yaml.example config/checker.yaml

# Edit configuration (optional - can be done via web UI)
nano config/checker.yaml
```

## 🌐 Access Your Application

- **Web Interface:** http://your-server:5000
- **Settings Page:** http://your-server:5000/settings
- **API Endpoints:**
  - `/api/webhook_logs` - View Discord webhook history
  - `/api/next_check_time` - Get countdown timer info
  - `/api/stock_history` - View stock tracking data

## ⚙️ Configuration

### **Discord Setup (Required)**
1. Go to your Discord server
2. Server Settings → Integrations → Webhooks
3. Create webhook → Copy URL
4. In web UI: Settings → paste webhook URL → Save

### **Notification Modes**
- **All Checks:** Get notified on every stock check
- **Stock Changes:** Only get notified when items are in stock

### **Adding Products**
1. Find CEX product ID from URL: `https://uk.webuy.com/product-detail/?id=PRODUCT_ID`
2. Add via web UI dashboard
3. Example IDs:
   - `SHDDSYNDS1821P8BDL` (Synology NAS)
   - `SPHAPP14P128GBSBL` (iPhone 14 Pro)

## 📊 Monitoring & Logs

### **Container Logs**
```bash
# View live logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100
```

### **Health Check**
```bash
# Check container status
docker-compose ps

# Manual health check
curl http://localhost:5000/
```

### **Discord Webhook Logs**
View delivery status and history in the web UI at `/settings`

## 🔧 Management Commands

### **Start/Stop/Restart**
```bash
# Stop application
docker-compose down

# Start application
docker-compose up -d

# Restart application
docker-compose restart

# Rebuild and restart (after code updates)
docker-compose up --build -d
```

### **Updates**
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### **Backup Configuration**
```bash
# Backup your data
tar -czf cex-backup-$(date +%Y%m%d).tar.gz config/ data/
```

## 🛡️ Security & Production

### **Firewall (Ubuntu/Debian)**
```bash
# Allow web access
sudo ufw allow 5000

# Or restrict to specific IPs
sudo ufw allow from YOUR_IP to any port 5000
```

### **Reverse Proxy (Optional)**
For HTTPS and custom domain, use Nginx or Traefik:

```nginx
# /etc/nginx/sites-available/cex-stock-checker
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **Environment Variables**
```bash
# Custom port
export PORT=8080

# Custom config path  
export CUSTOM_CONFIG=/path/to/config.yaml
```

## 🆘 Troubleshooting

### **Common Issues**

1. **Port 5000 in use:**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "8080:5000"  # Use port 8080 instead
   ```

2. **Permission denied:**
   ```bash
   # Fix data directory permissions
   sudo chown -R 1000:1000 config data
   ```

3. **Discord webhooks not working:**
   - Check webhook URL is correct
   - Verify Discord server permissions
   - Check webhook logs in settings page

4. **Container won't start:**
   ```bash
   # Check logs for errors
   docker-compose logs cex-stock-checker
   
   # Rebuild container
   docker-compose up --build -d
   ```

## 📈 Features Overview

- ✅ **Discord Rich Embeds** with colors, emojis, and product details
- ✅ **Real-time Web Dashboard** with countdown timers
- ✅ **Smart Notifications** (all checks vs stock changes only)
- ✅ **Webhook Logs** with delivery status tracking
- ✅ **Start/Stop Notifications** for monitoring lifecycle
- ✅ **Stock History Tracking** with timestamps and counts
- ✅ **Auto-refresh UI** with live updates
- ✅ **Production Ready** with health checks and logging
- ✅ **Easy Configuration** via web interface

## 🎯 Next Steps

1. **Configure Discord webhook** in settings
2. **Add your favorite CEX products** to monitor  
3. **Choose notification preferences**
4. **Start the stock checker** and enjoy automated monitoring!

---

**Happy Stock Hunting!** 🛍️📱💻