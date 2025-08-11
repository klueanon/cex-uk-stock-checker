from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import yaml
import os
import json
import threading
import time
from stock_check import check_stock, load_stock_history, load_webhook_logs, send_discord_webhook
import subprocess
import signal

app = Flask(__name__)
app.secret_key = 'cex-stock-checker-secret-key'

CONFIG_FILE = 'config/checker.yaml'
STOCK_HISTORY_FILE = 'stock_history.json'
WEBHOOK_LOGS_FILE = 'webhook_logs.json'

# Global variables to control the stock checker thread
stock_checker_thread = None
stock_checker_running = False
next_check_time = None

def load_config():
    """Load configuration from YAML file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    return {
        'items': [],
        'request_delay': 1800,
        'discord_enabled': True,
        'notification_mode': 'all_checks',
        'store_ids': [],
        'discord': {
            'webhook_url': ''
        }
    }

def save_config(config):
    """Save configuration to YAML file"""
    os.makedirs('config', exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

def get_product_info(product_id):
    """Get product information using the existing stock check function"""
    try:
        in_stock, product_info, stock_history = check_stock(product_id)
        return {
            'id': product_id,
            'name': product_info.get('boxName', 'Unknown Product'),
            'in_stock': in_stock,
            'stock_history': stock_history
        }
    except Exception as e:
        return {
            'id': product_id,
            'name': 'Error loading product',
            'in_stock': False,
            'error': str(e)
        }

@app.route('/')
def index():
    """Main dashboard page"""
    config = load_config()
    items = config.get('items', [])
    
    # Get product information for each item
    product_info = []
    for item_id in items:
        info = get_product_info(item_id)
        product_info.append(info)
    
    return render_template('index.html', 
                         products=product_info,
                         config=config,
                         checker_running=stock_checker_running,
                         next_check_time=next_check_time)

@app.route('/settings')
def settings():
    """Settings page"""
    config = load_config()
    webhook_logs = load_webhook_logs()
    return render_template('settings.html', config=config, webhook_logs=webhook_logs[:20])  # Show last 20 logs

@app.route('/add_item', methods=['POST'])
def add_item():
    """Add a new item to monitor"""
    product_id = request.form.get('product_id', '').strip()
    
    if not product_id:
        flash('Product ID is required', 'error')
        return redirect(url_for('index'))
    
    config = load_config()
    items = config.get('items', [])
    
    if product_id not in items:
        items.append(product_id)
        config['items'] = items
        save_config(config)
        flash(f'Added product {product_id} to monitoring list', 'success')
    else:
        flash(f'Product {product_id} is already being monitored', 'warning')
    
    return redirect(url_for('index'))

@app.route('/remove_item/<product_id>')
def remove_item(product_id):
    """Remove an item from monitoring"""
    config = load_config()
    items = config.get('items', [])
    
    if product_id in items:
        items.remove(product_id)
        config['items'] = items
        save_config(config)
        flash(f'Removed product {product_id} from monitoring list', 'success')
    
    return redirect(url_for('index'))

@app.route('/update_settings', methods=['POST'])
def update_settings():
    """Update application settings"""
    config = load_config()
    
    # Update basic settings
    config['request_delay'] = int(request.form.get('request_delay', 1800))
    config['discord_enabled'] = request.form.get('discord_enabled') == 'on'
    config['notification_mode'] = request.form.get('notification_mode', 'all_checks')
    
    # Validation: Check if Discord is properly configured
    if not config.get('discord_enabled'):
        flash('Warning: Discord notifications are disabled', 'warning')
    
    # Email settings removed - Discord only
    
    # Update Discord settings
    discord_config = config.get('discord', {})
    discord_config['webhook_url'] = request.form.get('discord_webhook_url', '').strip()
    
    config['discord'] = discord_config
    
    save_config(config)
    flash('Settings updated successfully', 'success')
    
    return redirect(url_for('settings'))

@app.route('/api/product_info/<product_id>')
def api_product_info(product_id):
    """API endpoint to get product information"""
    info = get_product_info(product_id)
    return jsonify(info)

@app.route('/api/stock_history')
def api_stock_history():
    """API endpoint to get stock history"""
    history = load_stock_history()
    return jsonify(history)

@app.route('/api/webhook_logs')
def api_webhook_logs():
    """API endpoint to get webhook logs"""
    logs = load_webhook_logs()
    return jsonify(logs[:50])  # Return last 50 logs

@app.route('/api/next_check_time')
def api_next_check_time():
    """API endpoint to get next check time"""
    global next_check_time
    return jsonify({'next_check_time': next_check_time})

@app.route('/start_checker')
def start_checker():
    """Start the stock checker in background"""
    global stock_checker_thread, stock_checker_running
    
    if not stock_checker_running:
        config = load_config()
        if not config.get('discord_enabled') or not config.get('discord', {}).get('webhook_url'):
            flash('Please configure Discord webhook URL in settings before starting', 'error')
            return redirect(url_for('settings'))
        
        stock_checker_running = True
        stock_checker_thread = threading.Thread(target=run_stock_checker, daemon=True)
        stock_checker_thread.start()
        flash('Stock checker started', 'success')
        
        # Send start notification
        items_count = len(config.get('items', []))
        delay = config.get('request_delay', 1800)
        startup_message = f"Checking {items_count} item(s) every {delay} seconds via Web UI"
        send_discord_webhook(config, "start", custom_message=startup_message)
    else:
        flash('Stock checker is already running', 'warning')
    
    return redirect(url_for('index'))

@app.route('/stop_checker')
def stop_checker():
    """Stop the stock checker"""
    global stock_checker_running
    
    if stock_checker_running:
        stock_checker_running = False
        flash('Stock checker stopped', 'success')
        
        # Send stop notification
        config = load_config()
        send_discord_webhook(config, "stop", custom_message="Stock checker stopped via Web UI")
    else:
        flash('Stock checker is not running', 'warning')
    
    return redirect(url_for('index'))

def run_stock_checker():
    """Run the stock checker in a separate thread"""
    global stock_checker_running, next_check_time
    
    from stock_check import should_send_notification, send_discord_webhook
    
    try:
        config = load_config()
        items = config.get('items', [])
        delay = config.get('request_delay', 1800)
        
        if not items:
            print("No items to check")
            return
        
        check_count = 0
        while stock_checker_running:
            check_count += 1
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"\nStarting web UI check #{check_count} at {current_time}")
            
            # Initialize check summary
            check_summary = []
            in_stock_count = 0
            
            # Check each item
            for item_id in items:
                if not stock_checker_running:
                    break
                
                try:
                    in_stock, product_info, stock_history = check_stock(item_id)
                    status = "IN STOCK" if in_stock else "OUT OF STOCK"
                    print(f"Product {item_id}: {status}")
                    
                    if in_stock:
                        in_stock_count += 1
                    
                    check_summary.append((product_info, status, current_time, stock_history))
                    time.sleep(2)  # Small delay between checks
                except Exception as e:
                    print(f"Error checking {item_id}: {e}")
            
            # Calculate next check time
            next_check_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + delay))
            
            # Send Discord notification based on configuration
            in_stock_items = [item for item in check_summary if item[1] == "IN STOCK"]
            summary_message = f"Check #{check_count} completed at {current_time}\nNext check: {next_check_time}"
            
            if should_send_notification(config, "check_result", in_stock_items):
                send_discord_webhook(config, "check_result", product_summaries=check_summary, custom_message=summary_message)
            
            print(f"Check completed at {current_time}")
            print(f"Next check in {delay} seconds ({next_check_time})")
            
            # Wait for next check
            for _ in range(delay):
                if not stock_checker_running:
                    break
                time.sleep(1)
        
    except Exception as e:
        print(f"Stock checker error: {e}")
    finally:
        stock_checker_running = False
        next_check_time = None

if __name__ == '__main__':
    # Ensure config directory exists
    os.makedirs('config', exist_ok=True)
    
    # Create default config if it doesn't exist
    if not os.path.exists(CONFIG_FILE):
        default_config = load_config()
        save_config(default_config)
    
    app.run(host='0.0.0.0', port=5001, debug=False)