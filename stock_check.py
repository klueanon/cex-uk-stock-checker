import yaml
import requests
import smtplib
import os.path
import sys
from time import sleep
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote_plus
import re
import json
from bs4 import BeautifulSoup
import time
from datetime import datetime

CONFIG_YAML = os.getenv('CUSTOM_CONFIG', "config/checker.yaml")
STORES_YAML = "config/stores.yaml"
STOCK_HISTORY_FILE = "stock_history.json"

CEX_WEB_URL = "https://uk.webuy.com"
PRODUCT_URL = f"{CEX_WEB_URL}/product-detail"

def get_request(product_id, store_id=None):
    # Construct URL based on whether store_id is provided
    if store_id:
        url = f"https://uk.webuy.com/product-detail?id={product_id}&storeId={store_id}"
    else:
        url = f"https://uk.webuy.com/product-detail?id={product_id}"

    # Headers to simulate a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

    # Make the request
    response = requests.get(url, headers=headers, allow_redirects=True)
    print(f"Making request to: {url}")
    print(f"Response status: {response.status_code}")

    # Check if we were redirected to the error page
    if response.url != url:
        print(f"Redirected to: {response.url}")
        if "error" in response.url or response.url == "https://uk.webuy.com/error":
            print("Product does not exist (redirected to error page)")
            return None
        elif "product-detail" not in response.url:
            print("Product does not exist (redirected to non-product page)")
            return None

    # Try to decode the response
    try:
        decoded_text = response.text
    except UnicodeDecodeError as e:
        print(f"Warning: Error decoding response: {e}")
        decoded_text = response.content.decode('utf-8', errors='ignore')

    # Save response to debug file
    debug_file = f"debug_{product_id}.html"
    try:
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(decoded_text)
        print(f"Full response saved to {debug_file}\n")
    except Exception as e:
        print(f"Warning: Could not save debug file: {e}\n")

    # Try to get the product data from the API
    api_url = f"https://wss2.cex.uk.webuy.io/v3/boxes/{product_id}/detail"
    try:
        api_response = requests.get(api_url, headers=headers)
        if api_response.status_code == 404:
            print("Product does not exist (API returned 404)")
            return None
        elif api_response.status_code == 200:
            # Save API response for debugging
            api_file = f"debug_{product_id}_api.json"
            with open(api_file, 'w', encoding='utf-8') as f:
                f.write(api_response.text)
            print(f"API response saved to {api_file}\n")
    except Exception as e:
        print(f"Warning: Failed to check API: {e}\n")

    return response

def format_price(price_info):
    if not price_info:
        return "Price not available"
    try:
        sell_price = price_info.get('sellPrice', 'N/A')
        buy_price = price_info.get('cashPrice', 'N/A')
        exchange_price = price_info.get('exchangePrice', 'N/A')
        return f"Sell: £{sell_price}, Buy: £{buy_price}, Exchange: £{exchange_price}"
    except:
        return "Price not available"

def load_stock_history():
    if os.path.exists(STOCK_HISTORY_FILE):
        try:
            with open(STOCK_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_stock_history(history):
    with open(STOCK_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def update_stock_history(product_id, in_stock):
    history = load_stock_history()
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    
    if product_id not in history:
        history[product_id] = {
            'last_in_stock': None,
            'last_check': current_time,
            'times_in_stock': 0
        }
    
    if in_stock:
        history[product_id]['last_in_stock'] = current_time
        history[product_id]['times_in_stock'] += 1
    
    history[product_id]['last_check'] = current_time
    save_stock_history(history)
    return history[product_id]

def create_html_message(product_info, stock_status, check_time, stock_history=None):
    product_name = product_info.get('boxName', 'Unknown Product')
    product_id = product_info.get('boxId', 'Unknown ID')
    price_info = format_price(product_info)
    product_url = f"https://uk.webuy.com/product-detail/?id={product_id}"
    
    # Set colors based on stock status
    status_color = '#28a745' if stock_status == "IN STOCK" else '#dc3545'
    
    # Format stock history information
    history_html = ""
    if stock_history:
        last_in_stock = stock_history.get('last_in_stock', 'Never')
        times_in_stock = stock_history.get('times_in_stock', 0)
        history_html = f"""
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
            <h4 style="margin: 0 0 10px 0;">Stock History</h4>
            <p style="margin: 5px 0;"><strong>Last In Stock:</strong> {last_in_stock or 'Never'}</p>
            <p style="margin: 5px 0;"><strong>Times In Stock:</strong> {times_in_stock}</p>
        </div>
        """
    
    html = f"""
    <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <h3 style="margin-top: 0;">{product_name}</h3>
        <p><strong>Status:</strong> <span style="color: {status_color}">{stock_status}</span></p>
        <p><strong>Price Information:</strong><br>{price_info}</p>
        <p><strong>Check Time:</strong><br>{check_time}</p>
        <p><strong>Product ID:</strong><br>{product_id}</p>
        <p><a href="{product_url}" style="color: #007bff; text-decoration: none;">View on CEX →</a></p>
        {history_html}
    </div>
    """
    return html

def send_email(config, message, is_html=False, stock_status=None):
    if not config.get('send_email_notification') or not config.get('send_email_enabled'):
        return
        
    email_config = config.get('email', {})
    
    required_settings = ['smtp_server', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email', 'to_email']
    missing_settings = [setting for setting in required_settings if not email_config.get(setting)]
    if missing_settings:
        print(f"Warning: Missing email settings: {', '.join(missing_settings)}")
        return
    
    msg = MIMEMultipart('alternative')
    
    # Set subject based on stock status
    if stock_status:
        msg['Subject'] = f"[{stock_status}] CEX Stock Checker Update"
    else:
        msg['Subject'] = "CEX Stock Checker Update"
        
    msg['From'] = email_config.get('from_email')
    msg['To'] = email_config.get('to_email')
    
    # Add both plain text and HTML versions
    text_part = MIMEText(message.replace('<br>', '\n').replace('→', '->'), 'plain')
    msg.attach(text_part)
    
    if is_html:
        html_part = MIMEText(message, 'html')
        msg.attach(html_part)
    
    try:
        print(f"Sending email notification to {email_config.get('to_email')}...")
        # Try SSL first
        try:
            with smtplib.SMTP_SSL(email_config.get('smtp_server'), 465) as server:
                server.login(email_config.get('smtp_username'), email_config.get('smtp_password'))
                server.send_message(msg)
                print("Email notification sent successfully via SSL")
                return
        except Exception as ssl_e:
            print(f"SSL connection failed, trying TLS: {str(ssl_e)}")
            
        # Fall back to TLS if SSL fails
        with smtplib.SMTP(email_config.get('smtp_server'), email_config.get('smtp_port')) as server:
            server.starttls()
            server.login(email_config.get('smtp_username'), email_config.get('smtp_password'))
            server.send_message(msg)
            print("Email notification sent successfully via TLS")
    except smtplib.SMTPAuthenticationError as e:
        print("\nFailed to authenticate with Gmail:")
        print("1. Make sure you're using an App Password and not your regular password")
        print("2. Verify that 2-Step Verification is enabled on your Google Account")
        print("3. Check that the App Password is correctly copied into the config file")
        print("4. Make sure there are no extra spaces in the App Password")
        print(f"\nError details: {str(e)}")
        print("\nCurrent settings:")
        print(f"SMTP Server: {email_config.get('smtp_server')}")
        print(f"Username: {email_config.get('smtp_username')}")
        print(f"Password length: {len(email_config.get('smtp_password'))} characters")
    except Exception as e:
        print(f"Failed to send email notification: {str(e)}")
        print("Check your email configuration in config/checker.yaml")

def check_stock(product_id, store_id=None):
    url = f"https://uk.webuy.com/product-detail?id={product_id}"
    if store_id:
        url += f"&storeId={store_id}"
    
    print(f"Making request to: {url}")
    response = requests.get(url)
    print(f"Response status: {response.status_code}")
    print(f"Redirected to: {response.url}")
    
    # Save full response for debugging
    debug_file = f"debug_{product_id}.html"
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"Full response saved to {debug_file}")
    
    # Extract product information from API
    api_url = f"https://wss2.cex.uk.webuy.io/v3/boxes/{product_id}/detail"
    api_response = requests.get(api_url)
    api_data = api_response.json() if api_response.ok else {}
    
    # Save API response for debugging
    debug_api_file = f"debug_{product_id}_api.json"
    with open(debug_api_file, "w") as f:
        json.dump(api_data, f, indent=2)
    print(f"API response saved to {debug_api_file}")
    
    # Extract product name and stock info
    product_info = None
    if 'response' in api_data and 'data' in api_data['response']:
        box_details = api_data['response']['data'].get('boxDetails', [])
        if box_details and len(box_details) > 0:
            product_info = box_details[0]
            product_name = product_info.get('boxName')
            print(f"Product Name: {product_name}")
            
            # Check API stock info
            quantity = product_info.get('ecomQuantityOnHand', 0)
            out_of_stock = product_info.get('outOfStock', True)
            web_sell_allowed = product_info.get('webSellAllowed', False)
            
            print("API Stock Info:")
            print(f"  - Quantity Available: {quantity}")
            print(f"  - Out of Stock Flag: {1 if out_of_stock else 0}")
            print(f"  - Web Sell Allowed: {1 if web_sell_allowed else 0}")
            
            if quantity > 0 and not out_of_stock and web_sell_allowed:
                print("API indicates product is in stock")
                in_stock = True
            else:
                print("API indicates product is out of stock")
                in_stock = False
    
    if not product_info:
        print("Failed to get product info from API")
        return False, {"boxName": "Unknown Product", "boxId": product_id}, None
    
    # Parse HTML response
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check for key elements
    buy_button = soup.find('button', {'data-testid': 'add-to-basket-button'})
    out_of_stock_msg = soup.find('div', {'data-testid': 'out-of-stock-message'})
    price_indicator = soup.find('div', {'data-testid': 'price'})
    quantity_selector = soup.find('div', {'data-testid': 'quantity-selector'})
    
    print(f"Buy button found: {bool(buy_button)}")
    print(f"Out of stock message found: {bool(out_of_stock_msg)}")
    print(f"Price indicator found: {bool(price_indicator)}")
    print(f"Quantity selector found: {bool(quantity_selector)}")
    
    # Check for reviews to determine if product has been in stock before
    reviews_section = soup.find('div', {'data-testid': 'reviews'})
    has_reviews = bool(reviews_section and reviews_section.find_all('div', {'data-testid': 'review'}))
    
    # Load or initialize stock history
    history_file = f"stock_history_{product_id}.json"
    try:
        with open(history_file, 'r') as f:
            stock_history = json.load(f)
    except FileNotFoundError:
        stock_history = {
            'last_in_stock': None,
            'times_in_stock': 0,
            'first_seen': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    # Update stock history based on current check and reviews
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    if in_stock:
        stock_history['last_in_stock'] = current_time
        stock_history['times_in_stock'] += 1
    
    # If product has reviews but no last_in_stock date, set it to "Previously in stock"
    if has_reviews and not stock_history['last_in_stock']:
        stock_history['last_in_stock'] = "Previously in stock"
        stock_history['times_in_stock'] = max(1, stock_history['times_in_stock'])
    
    # Save updated stock history
    with open(history_file, 'w') as f:
        json.dump(stock_history, f, indent=2)
    
    # Determine final stock status
    if in_stock:
        print("Final stock status: IN STOCK")
    else:
        print("Final stock status: OUT OF STOCK")
    
    return in_stock, product_info, stock_history

def check():
    print(f"Using config file: {CONFIG_YAML}")
    
    try:
        with open(CONFIG_YAML, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        sys.exit("No configuration file found.")
    except yaml.YAMLError as e:
        sys.exit(f"Error reading configuration: {e}")
    
    items = config.get('items', [])
    store_ids = config.get('store_ids')
    delay = config.get('request_delay', 1800)  # Default to 30 minutes
    
    print(f"Found {len(items)} item(s) in check list")
    print(f"Will check every {delay} seconds")
    
    # Send startup notification
    startup_message = (
        f"CEX Stock Checker Started\n"
        f"Checking {len(items)} item(s) every {delay} seconds\n"
        f"Items being monitored:\n"
    )
    for item_id in items:
        startup_message += f"- {item_id}\n"
    send_email(config, startup_message)
    
    check_count = 0
    while True:
        check_count += 1
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"\nStarting check #{check_count} at {current_time}")
        
        # Initialize check summary
        check_summary = []
        in_stock_count = 0
        
        for item_id in items:
            if store_ids:
                for store_id in store_ids:
                    in_stock, product_info, stock_history = check_stock(item_id, store_id)
                    if in_stock:
                        in_stock_count += 1
                        message = f"Product {item_id} is in stock at store {store_id}!"
                        print(message)
                        check_summary.append((product_info, "IN STOCK", current_time, stock_history))
                    else:
                        # Check if the debug file exists to determine if product exists
                        debug_file = f"debug_{item_id}.html"
                        if not os.path.exists(debug_file):
                            status = f"Product {item_id} does not exist"
                        else:
                            status = f"Product {item_id} is currently out of stock at store {store_id}"
                        print(status)
                        check_summary.append((product_info, "OUT OF STOCK", current_time, stock_history))
                    sleep(2)  # Small delay between store checks
            else:
                in_stock, product_info, stock_history = check_stock(item_id)
                if in_stock:
                    in_stock_count += 1
                    message = f"Product {item_id} is in stock!"
                    print(message)
                    check_summary.append((product_info, "IN STOCK", current_time, stock_history))
                else:
                    # Check if the debug file exists to determine if product exists
                    debug_file = f"debug_{item_id}.html"
                    if not os.path.exists(debug_file):
                        status = f"Product {item_id} does not exist"
                    else:
                        status = f"Product {item_id} is currently out of stock"
                    print(status)
                    check_summary.append((product_info, "OUT OF STOCK", current_time, stock_history))
                sleep(2)  # Small delay between item checks
        
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        next_check_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + delay))
        
        # Create summary HTML email
        summary_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">CEX Stock Check Summary</h2>
                <p style="font-size: 1.2em; margin-bottom: 20px;">
                    <strong>{in_stock_count}/{len(items)} Products In Stock</strong>
                </p>
                <p>Check #{check_count} completed at {current_time}</p>
        """
        
        for product_info, status, check_time, stock_history in check_summary:
            if product_info:
                summary_html += create_html_message(product_info, status, check_time, stock_history)
        
        summary_html += f"""
                <p style="margin-top: 20px;">Next check scheduled for {next_check_time}</p>
            </div>
        </body>
        </html>
        """
        
        print(f"Check completed at {current_time}")
        print(f"Next check in {delay} seconds ({next_check_time})")
        
        # Send combined summary email with stock ratio in subject
        stock_status = f"{in_stock_count}/{len(items)} IN STOCK"
        send_email(config, summary_html, is_html=True, stock_status=stock_status)
        
        sys.stdout.flush()  # Ensure output is written immediately
        sleep(delay)

if __name__ == "__main__":
    try:
        check()
    except KeyboardInterrupt:
        print("\nStopping stock checker...")
        sys.exit(0)
