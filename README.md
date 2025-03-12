# CEX Stock Checker

A Python script to monitor stock availability of products on CEX (uk.webuy.com) and send email notifications when items come in stock.

## Features

- Monitor multiple products simultaneously
- Email notifications for stock changes
- Combined status updates in a single email
- Stock history tracking
- Color-coded status indicators
- Configurable check intervals

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cex-stock-checker.git
cd cex-stock-checker
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a config file:
```bash
cp config/checker.yaml.example config/checker.yaml
```

5. Set up environment variables:
```bash
export GMAIL_USERNAME="your.email@gmail.com"
export GMAIL_APP_PASSWORD="your-app-specific-password"
export NOTIFICATION_EMAIL="notifications@example.com"
```

Note: For Gmail, you need to:
1. Enable 2-Step Verification
2. Generate an App Password (Gmail > Account > Security > App Passwords)

## Configuration

Edit `config/checker.yaml` to:
- Add product IDs to monitor
- Set check interval (in seconds)
- Configure email settings

Example configuration:
```yaml
items:
  - SHDDSYNDS1821P8BDL  # Synology Disk Station DS1821+ 8bay NAS Enclosure
  - SHDDWD3TBWD30REDA   # WD Red WD30EFRX 3TB NAS 3.5" SATA

request_delay: 1800  # 30 minutes
send_email_notification: true
send_email_enabled: true

store_ids: []  # Empty for general availability
proceed_prompt_enabled: false

email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  smtp_username: "${GMAIL_USERNAME}"
  smtp_password: "${GMAIL_APP_PASSWORD}"
  from_email: "${GMAIL_USERNAME}"
  to_email: "${NOTIFICATION_EMAIL}"
```

## Usage

Run the script:
```bash
source venv/bin/activate
python3 stock_check.py
```

The script will:
1. Send a startup notification
2. Check stock status every 30 minutes (configurable)
3. Send email notifications with:
   - Stock status for all monitored items
   - Price information
   - Stock history
   - Links to product pages

## License

MIT License
