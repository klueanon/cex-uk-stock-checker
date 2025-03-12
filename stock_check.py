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

CONFIG_YAML = os.getenv('CUSTOM_CONFIG', "config/checker.yaml")
STORES_YAML = "config/stores.yaml"

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

def check_stock(product_id, store_id=None):
    # Make the request
    response = get_request(product_id, store_id)
    
    # If response is None, product doesn't exist
    if response is None:
        print("Final stock status: PRODUCT NOT FOUND\n")
        return False

    # Check response status
    if response.status_code != 200:
        print(f"Product not found (Status code: {response.status_code})")
        print("Final stock status: PRODUCT NOT FOUND\n")
        return False

    # Check if the API response exists and get product name
    api_file = f"debug_{product_id}_api.json"
    product_name = None
    if os.path.exists(api_file):
        try:
            with open(api_file, 'r', encoding='utf-8') as f:
                api_data = json.load(f)
            if not api_data or 'response' not in api_data or not api_data['response'].get('data'):
                print("Product does not exist (no data in API response)")
                print("Final stock status: PRODUCT NOT FOUND\n")
                return False
            
            # Extract product details from API response
            box_details = api_data['response']['data'].get('boxDetails', [])
            if box_details and len(box_details) > 0:
                product_info = box_details[0]
                product_name = product_info.get('boxName')
                if product_name:
                    print(f"Product Name: {product_name}")
                
                # Check stock from API
                ecom_quantity = product_info.get('ecomQuantityOnHand', 0)
                out_of_stock = product_info.get('outOfStock', 1)
                web_sell_allowed = product_info.get('webSellAllowed', 0)
                
                print(f"API Stock Info:")
                print(f"  - Quantity Available: {ecom_quantity}")
                print(f"  - Out of Stock Flag: {out_of_stock}")
                print(f"  - Web Sell Allowed: {web_sell_allowed}")
                
                if ecom_quantity > 0 and not out_of_stock and web_sell_allowed:
                    print("API indicates product is in stock")
                else:
                    print("API indicates product is out of stock")
            else:
                print("Product does not exist (no box details in API response)")
                print("Final stock status: PRODUCT NOT FOUND\n")
                return False
        except Exception as e:
            print(f"Warning: Failed to read API response: {e}")

    # Get the page text
    page_text = response.text.lower()

    # Check for error messages indicating product doesn't exist
    error_messages = [
        'product not found',
        'page not found',
        'item not found',
        '404',
        'does not exist',
        'no longer available',
        'no results found',
        'cannot find the page',
        'page you are looking for is not available'
    ]

    if any(msg in page_text for msg in error_messages):
        print("Product does not exist")
        print("Final stock status: PRODUCT NOT FOUND\n")
        return False

    # Check for buy buttons
    buy_button_found = any(pattern in page_text for pattern in [
        'add to basket',
        'buy now',
        'add to cart',
        'purchase',
        'class="buy"',
        'data-buy',
        'addtobasket',
        'buynow'
    ])
    print(f"Buy button found: {buy_button_found}")

    # Check for out of stock messages
    out_of_stock_found = any(pattern in page_text for pattern in [
        'out of stock',
        'notify me',
        'email when available',
        'currently unavailable',
        'not available',
        'sold out',
        'notifyme',
        'notify-me'
    ])
    print(f"Out of stock message found: {out_of_stock_found}")

    # Check for price indicators
    price_found = any(pattern in page_text for pattern in [
        '£',
        'gbp',
        'price',
        'class="amount"',
        'data-price',
        'data-amount'
    ])
    print(f"Price indicator found: {price_found}")

    # Check for quantity selectors
    quantity_found = any(pattern in page_text for pattern in [
        'quantity',
        'qty',
        'amount',
        'class="quantity"',
        'data-qty',
        'data-quantity'
    ])
    print(f"Quantity selector found: {quantity_found}")

    # Check if this is just the initial page load without data
    if not any([buy_button_found, price_found, quantity_found, out_of_stock_found]):
        print("No product data found (likely non-existent product)")
        print("Final stock status: PRODUCT NOT FOUND\n")
        return False

    # Determine if product is in stock based on both API and HTML indicators
    api_in_stock = False
    if os.path.exists(api_file):
        try:
            with open(api_file, 'r', encoding='utf-8') as f:
                api_data = json.load(f)
            box_details = api_data['response']['data'].get('boxDetails', [])
            if box_details and len(box_details) > 0:
                product_info = box_details[0]
                api_in_stock = (
                    product_info.get('ecomQuantityOnHand', 0) > 0 and
                    not product_info.get('outOfStock', 1) and
                    product_info.get('webSellAllowed', 0)
                )
        except Exception:
            pass

    html_in_stock = (
        price_found and
        (buy_button_found or quantity_found) and
        not out_of_stock_found
    )

    in_stock = api_in_stock or html_in_stock
    print(f"Final stock status: {'IN STOCK' if in_stock else 'OUT OF STOCK'}\n")
    return in_stock

def send_email(config, message):
    if not config.get('send_email_notification') or not config.get('send_email_enabled'):
        return
        
    email_config = config.get('email', {})
    
    # Check if all required email settings are present
    required_settings = ['smtp_server', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email', 'to_email']
    missing_settings = [setting for setting in required_settings if not email_config.get(setting)]
    if missing_settings:
        print(f"Warning: Missing email settings: {', '.join(missing_settings)}")
        return
    
    msg = MIMEText(message)
    msg['Subject'] = 'CEX Stock Checker Update'
    msg['From'] = email_config.get('from_email')
    msg['To'] = email_config.get('to_email')
    
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
        check_summary = f"Stock Check #{check_count} - {current_time}\n\n"
        
        for item_id in items:
            if store_ids:
                for store_id in store_ids:
                    if check_stock(item_id, store_id):
                        message = f"Product {item_id} is in stock at store {store_id}!"
                        print(message)
                        check_summary += f"{message}\n"
                        # Send immediate notification for in-stock items
                        send_email(config, f"IN STOCK ALERT: {message}")
                    else:
                        # Check if the debug file exists to determine if product exists
                        debug_file = f"debug_{item_id}.html"
                        if not os.path.exists(debug_file):
                            status = f"Product {item_id} does not exist"
                        else:
                            status = f"Product {item_id} is currently out of stock at store {store_id}"
                        print(status)
                        check_summary += f"{status}\n"
                    sleep(2)  # Small delay between store checks
            else:
                if check_stock(item_id):
                    message = f"Product {item_id} is in stock!"
                    print(message)
                    check_summary += f"{message}\n"
                    # Send immediate notification for in-stock items
                    send_email(config, f"IN STOCK ALERT: {message}")
                else:
                    # Check if the debug file exists to determine if product exists
                    debug_file = f"debug_{item_id}.html"
                    if not os.path.exists(debug_file):
                        status = f"Product {item_id} does not exist"
                    else:
                        status = f"Product {item_id} is currently out of stock"
                    print(status)
                    check_summary += f"{status}\n"
                sleep(2)  # Small delay between item checks
        
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        next_check_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + delay))
        
        check_summary += f"\nCheck completed at {current_time}"
        check_summary += f"\nNext check scheduled for {next_check_time}"
        
        print(f"Check completed at {current_time}")
        print(f"Next check in {delay} seconds ({next_check_time})")
        
        # Send check summary email
        send_email(config, check_summary)
        
        sys.stdout.flush()  # Ensure output is written immediately
        sleep(delay)

if __name__ == "__main__":
    try:
        check()
    except KeyboardInterrupt:
        print("\nStopping stock checker...")
        sys.exit(0)
