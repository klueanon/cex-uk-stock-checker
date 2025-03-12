# CEX Stock Checker

A Python script to monitor stock availability of products on CEX (uk.webuy.com) with email notifications.

## Features

- Monitor multiple products simultaneously
- Check specific stores or general availability
- Email notifications when items come in stock
- Configurable check intervals
- Detailed logging of stock status

## Setup

1. Clone the repository:
```bash
git clone https://github.com/klueanon/cex-stock-checker.git
cd cex-stock-checker
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install pyyaml requests beautifulsoup4
```

4. Create your configuration:
```bash
cp config/checker.template.yaml config/checker.yaml
```

5. Edit `config/checker.yaml` with your settings:
- Add product IDs to monitor
- Configure email settings (Gmail recommended)
- Adjust check interval if desired

### Email Setup (Gmail)

1. Enable 2-Step Verification in your Google Account
2. Generate an App Password:
   - Go to Google Account settings
   - Navigate to Security
   - Under "2-Step Verification", click on "App passwords"
   - Select "Mail" and generate a new password
3. Use this App Password in your `config/checker.yaml`

## Usage

1. Activate the virtual environment:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Run the script:
```bash
python3 stock_check.py
```

The script will:
- Send a startup notification
- Check stock status at configured intervals
- Send notifications for any changes
- Continue running until stopped (Ctrl+C)

## Docker Support

Build the image:
```bash
docker build -t cex-stock-checker .
```

Run the container:
```bash
docker run -v $(pwd)/config:/app/config cex-stock-checker
```

## Configuration

Example `checker.yaml`:
```yaml
items:
  - PRODUCT_ID_HERE  # Example: SHDDSYNDS1821P8BDL

request_delay: 1800  # 30 minutes
send_email_notification: true
send_email_enabled: true

email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  smtp_username: "your.email@gmail.com"
  smtp_password: "your-app-password"
  from_email: "your.email@gmail.com"
  to_email: "recipient@example.com"
```

## License

MIT License
