import yaml
import requests
import os.path
import sys
from time import sleep
from urllib.parse import quote_plus
import re
import json
from bs4 import BeautifulSoup
import time
from datetime import datetime

CONFIG_YAML = os.getenv('CUSTOM_CONFIG', "config/checker.yaml")
STORES_YAML = "config/stores.yaml"
STOCK_HISTORY_FILE = "stock_history.json"
WEBHOOK_LOGS_FILE = "webhook_logs.json"

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

def load_webhook_logs():
    if os.path.exists(WEBHOOK_LOGS_FILE):
        try:
            with open(WEBHOOK_LOGS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_webhook_log(log_entry):
    logs = load_webhook_logs()
    logs.insert(0, log_entry)  # Add to beginning
    # Keep only last 100 logs
    logs = logs[:100]
    with open(WEBHOOK_LOGS_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def get_embed_color(message_type, in_stock_count=0, total_items=0):
    """Get appropriate color for Discord embed based on context"""
    if message_type == "start":
        return 0x00ff00  # Bright green for start
    elif message_type == "stop":
        return 0xff0000  # Red for stop
    elif message_type == "check_result":
        if in_stock_count == 0:
            return 0x808080  # Gray for no items in stock
        elif in_stock_count == total_items:
            return 0x00ff00  # Green for all items in stock
        else:
            return 0xffa500  # Orange for some items in stock
    return 0x7289da  # Discord default blue

def format_price_info(product_info):
    """Format price information for Discord display"""
    if not product_info:
        return "Price information unavailable"
    
    try:
        sell_price = product_info.get('sellPrice')
        buy_price = product_info.get('cashPrice') 
        exchange_price = product_info.get('exchangePrice')
        
        price_parts = []
        if sell_price and sell_price > 0:
            price_parts.append(f"🏷️ Sell: £{sell_price}")
        if buy_price and buy_price > 0:
            price_parts.append(f"💰 Buy: £{buy_price}")
        if exchange_price and exchange_price > 0:
            price_parts.append(f"🔄 Exchange: £{exchange_price}")
        
        return " • ".join(price_parts) if price_parts else "Price information unavailable"
    except:
        return "Price information unavailable"

def send_discord_webhook(config, message_type="check_result", product_summaries=None, custom_message=None):
    """Send enhanced notification via Discord webhook with images and styling"""
    if not config.get('discord_enabled'):
        return False
        
    discord_config = config.get('discord', {})
    webhook_url = discord_config.get('webhook_url')
    
    if not webhook_url:
        print("Warning: Discord webhook URL not configured")
        return False
    
    try:
        # Count in-stock items for color determination
        in_stock_count = 0
        total_items = 0
        if product_summaries:
            in_stock_count = sum(1 for _, status, _, _ in product_summaries if status == "IN STOCK")
            total_items = len(product_summaries)
        
        embed = {
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "CEX Stock Checker - Powered by uk.webuy.com",
                "icon_url": "https://uk.webuy.com/site-media/images/misc/webuy-logo.png"
            },
            "color": get_embed_color(message_type, in_stock_count, total_items),
            "thumbnail": {
                "url": "https://uk.webuy.com/site-media/images/misc/webuy-logo.png"
            }
        }
        
        if message_type == "start":
            embed["title"] = "🟢 CEX Stock Checker Started"
            embed["description"] = f"✨ **Stock monitoring is now active!**\n\n{custom_message or 'Ready to monitor your favorite CEX products'}"
        elif message_type == "stop":
            embed["title"] = "🔴 CEX Stock Checker Stopped"
            embed["description"] = f"⏹️ **Stock monitoring has been paused**\n\n{custom_message or 'Stock checker has been stopped'}"
        elif message_type == "check_result":
            # Create title with emojis based on stock status
            if in_stock_count == 0:
                title_emoji = "🚫"
                status_text = "No Items in Stock"
            elif in_stock_count == total_items:
                title_emoji = "🎉"
                status_text = "All Items in Stock!"
            else:
                title_emoji = "🟡"
                status_text = "Some Items Available"
            
            embed["title"] = f"{title_emoji} Stock Check Complete - {in_stock_count}/{total_items} {status_text}"
            
            if custom_message:
                embed["description"] = f"📅 {custom_message}"
        
        # Add product information if available
        if product_summaries and message_type == "check_result":
            fields = []
            
            # Sort products: in-stock items first
            sorted_products = sorted(product_summaries, 
                                   key=lambda x: (x[1] != "IN STOCK", x[0].get('boxName', '')))
            
            for i, (product_info, status, check_time, stock_history) in enumerate(sorted_products[:8]):  # Limit to 8 for better display
                product_name = product_info.get('boxName', 'Unknown Product')
                product_id = product_info.get('boxId', 'Unknown ID')
                product_url = f"https://uk.webuy.com/product-detail?id={product_id}"
                
                # Enhanced status indicators
                if status == "IN STOCK":
                    status_emoji = "✅"
                    status_indicator = "**🔥 AVAILABLE NOW**"
                else:
                    status_emoji = "❌"
                    status_indicator = "*Out of Stock*"
                
                # Build field value with enhanced formatting
                field_value = f"{status_emoji} {status_indicator}\n"
                
                # Add price information if available
                price_info = format_price_info(product_info)
                if price_info != "Price information unavailable":
                    field_value += f"{price_info}\n"
                
                field_value += f"🏷️ `{product_id}`\n"
                
                # Stock history with better formatting
                if stock_history:
                    last_in_stock = stock_history.get('last_in_stock', 'Never')
                    times_in_stock = stock_history.get('times_in_stock', 0)
                    
                    if last_in_stock != 'Never':
                        field_value += f"🕰️ Last seen: {last_in_stock}\n"
                    
                    if times_in_stock > 0:
                        field_value += f"📊 Times available: {times_in_stock}\n"
                
                field_value += f"\n[🔗 **View on CEX**]({product_url})"
                
                # Truncate product name if too long
                display_name = product_name[:40] + "..." if len(product_name) > 40 else product_name
                
                fields.append({
                    "name": f"{status_emoji} {display_name}",
                    "value": field_value,
                    "inline": True
                })
            
            embed["fields"] = fields
            
            # Add summary field if there are more items than displayed
            if len(product_summaries) > 8:
                remaining = len(product_summaries) - 8
                embed["fields"].append({
                    "name": "📝 Summary",
                    "value": f"Showing 8 of {len(product_summaries)} products\n{remaining} additional item(s) monitored\n\n🔄 Refresh for latest status",
                    "inline": False
                })
        
        payload = {
            "embeds": [embed],
            "username": "CEX Stock Monitor",
            "avatar_url": "https://uk.webuy.com/site-media/images/misc/webuy-logo.png",
            "content": None  # We use embeds exclusively for rich formatting
        }
        
        print(f"Sending Discord notification to webhook...")
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        # Log the webhook attempt
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "message_type": message_type,
            "status": "success" if response.status_code == 204 else "failed",
            "status_code": response.status_code,
            "payload": payload,
            "response": response.text if response.status_code != 204 else None
        }
        save_webhook_log(log_entry)
        
        if response.status_code == 204:
            print("Discord notification sent successfully")
            return True
        else:
            print(f"Discord notification failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"Failed to send Discord notification: {str(e)}")
        # Log the error
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "message_type": message_type,
            "status": "error",
            "error": str(e)
        }
        save_webhook_log(log_entry)
        return False

def should_send_notification(config, message_type, in_stock_items=None):
    """Determine if notification should be sent based on config"""
    if not config.get('discord_enabled'):
        return False
    
    notification_mode = config.get('notification_mode', 'all_checks')  # 'all_checks' or 'stock_changes'
    
    if message_type in ['start', 'stop']:
        return True
    
    if notification_mode == 'all_checks':
        return True
    elif notification_mode == 'stock_changes' and in_stock_items and len(in_stock_items) > 0:
        return True
    
    return False

# Email functionality removed - Discord only

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

def check(web_mode=False, running_flag=None):
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
    
    # Send startup notification only if not in web mode
    if not web_mode:
        startup_message = (
            f"Checking {len(items)} item(s) every {delay} seconds\n"
            f"Items being monitored:\n"
        )
        for item_id in items:
            startup_message += f"- {item_id}\n"
        send_discord_webhook(config, "start", custom_message=startup_message)
    
    check_count = 0
    while True:
        # Check running flag for web mode
        if web_mode and running_flag and not running_flag():
            print("Stopping stock checker (web mode)")
            break
            
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
        
        # Prepare notification message
        summary_message = f"Check #{check_count} completed at {current_time}\nNext check: {next_check_time}"
        
        print(f"Check completed at {current_time}")
        print(f"Next check in {delay} seconds ({next_check_time})")
        
        # Send Discord notification based on configuration
        in_stock_items = [item for item in check_summary if item[1] == "IN STOCK"]
        if should_send_notification(config, "check_result", in_stock_items):
            send_discord_webhook(config, "check_result", product_summaries=check_summary, custom_message=summary_message)
        
        sys.stdout.flush()  # Ensure output is written immediately
        
        # Sleep with interruption checking for web mode
        if web_mode and running_flag:
            for _ in range(delay):
                if not running_flag():
                    print("Stopping stock checker during sleep (web mode)")
                    return
                sleep(1)
        else:
            sleep(delay)

if __name__ == "__main__":
    try:
        check()
    except KeyboardInterrupt:
        print("\nStopping stock checker...")
        # Send stop notification
        try:
            with open(CONFIG_YAML, "r") as f:
                config = yaml.safe_load(f)
            send_discord_webhook(config, "stop", custom_message="Stock checker stopped manually")
        except:
            pass
        sys.exit(0)
