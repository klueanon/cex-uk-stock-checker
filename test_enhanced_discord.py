#!/usr/bin/env python3
"""
Enhanced Discord Webhook Test Script
Tests the new rich Discord notifications with images and styling
"""

import yaml
import time
from stock_check import send_discord_webhook

def load_test_config():
    """Load configuration or create a test one"""
    try:
        with open('config/checker.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except:
        # Create a test config if file doesn't exist
        config = {
            'discord_enabled': True,
            'discord': {
                'webhook_url': input("Enter your Discord webhook URL: ").strip()
            }
        }
        
        if not config['discord']['webhook_url']:
            print("No webhook URL provided. Exiting.")
            return None
            
    return config

def create_test_product_summaries():
    """Create sample product data for testing"""
    return [
        (
            {
                'boxName': 'iPhone 14 Pro 128GB Space Black Unlocked',
                'boxId': 'SPHAPP14P128GBSBL',
                'sellPrice': 899.00,
                'cashPrice': 650.00,
                'exchangePrice': 720.00,
                'imageUrls': ['/site-media/images/products/iphone14pro.jpg']
            },
            "IN STOCK",
            "2025-01-11 20:30:00",
            {
                'last_in_stock': '2025-01-11 20:30:00',
                'times_in_stock': 5
            }
        ),
        (
            {
                'boxName': 'Sony PlayStation 5 Console',
                'boxId': 'SCOSONPS5C825GB',
                'sellPrice': 479.99,
                'cashPrice': 320.00,
                'exchangePrice': 380.00
            },
            "OUT OF STOCK",
            "2025-01-11 20:30:00",
            {
                'last_in_stock': '2025-01-10 14:22:15',
                'times_in_stock': 12
            }
        ),
        (
            {
                'boxName': 'MacBook Air M2 13" 256GB Space Grey',
                'boxId': 'SCOAPPMBA13256GBSG',
                'sellPrice': 1299.00,
                'cashPrice': 890.00,
                'exchangePrice': 1050.00
            },
            "IN STOCK",
            "2025-01-11 20:30:00",
            {
                'last_in_stock': '2025-01-11 20:30:00',
                'times_in_stock': 3
            }
        ),
        (
            {
                'boxName': 'Nintendo Switch OLED Console White',
                'boxId': 'SCONINSWOLEDW',
                'sellPrice': 309.99,
                'cashPrice': 185.00,
                'exchangePrice': 220.00
            },
            "OUT OF STOCK",
            "2025-01-11 20:30:00",
            {
                'last_in_stock': 'Never',
                'times_in_stock': 0
            }
        )
    ]

def test_enhanced_notifications():
    """Test all types of enhanced Discord notifications"""
    print("🚀 Testing Enhanced Discord Notifications")
    print("=" * 50)
    
    config = load_test_config()
    if not config:
        return
    
    # Test 1: Start notification with enhanced styling
    print("\n1. Testing START notification...")
    success = send_discord_webhook(
        config, 
        "start", 
        custom_message="Monitoring 4 premium tech products\n• iPhone 14 Pro\n• PlayStation 5\n• MacBook Air M2\n• Nintendo Switch OLED"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    time.sleep(2)
    
    # Test 2: Stock check results with mixed status
    print("\n2. Testing STOCK CHECK with mixed results...")
    product_summaries = create_test_product_summaries()
    success = send_discord_webhook(
        config,
        "check_result",
        product_summaries=product_summaries,
        custom_message="Stock check completed at 2025-01-11 20:30:00\nNext check: 2025-01-11 21:00:00"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    time.sleep(2)
    
    # Test 3: All items in stock (best case scenario)
    print("\n3. Testing ALL ITEMS IN STOCK scenario...")
    all_in_stock = [(item[0], "IN STOCK", item[2], item[3]) for item in product_summaries[:2]]
    success = send_discord_webhook(
        config,
        "check_result", 
        product_summaries=all_in_stock,
        custom_message="🎉 Great news! All monitored items are now available!"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    time.sleep(2)
    
    # Test 4: No items in stock
    print("\n4. Testing NO ITEMS IN STOCK scenario...")
    all_out_of_stock = [(item[0], "OUT OF STOCK", item[2], item[3]) for item in product_summaries[:2]]
    success = send_discord_webhook(
        config,
        "check_result",
        product_summaries=all_out_of_stock,
        custom_message="No items currently available - will keep monitoring"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    time.sleep(2)
    
    # Test 5: Stop notification
    print("\n5. Testing STOP notification...")
    success = send_discord_webhook(
        config,
        "stop",
        custom_message="Stock monitoring paused by user\nTotal checks completed: 47\nItems found in stock: 8"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    print("\n" + "=" * 50)
    print("🎊 Enhanced notification testing complete!")
    print("\nNew Features Demonstrated:")
    print("• 🎨 Dynamic colors based on stock status")
    print("• 🖼️  Thumbnails and hero images")
    print("• 💰 Price information display")  
    print("• 📊 Enhanced formatting with emojis")
    print("• 🔗 Direct links to CEX product pages")
    print("• 📈 Stock history tracking")
    print("• ⚡ Priority sorting (in-stock items first)")
    print("• 🏷️  Product ID display")
    print("• 🎯 Visual status indicators")

if __name__ == "__main__":
    test_enhanced_notifications()