#!/usr/bin/env python3
"""
Test script for Discord webhook functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_check import send_discord_webhook

def test_discord_webhook():
    """Test Discord webhook with sample data"""
    
    # Test configuration
    config = {
        'discord_enabled': True,
        'send_discord_notification': True,
        'discord': {
            'webhook_url': input("Enter your Discord webhook URL (or press Enter to skip): ").strip()
        }
    }
    
    if not config['discord']['webhook_url']:
        print("No webhook URL provided, skipping Discord test")
        return
    
    print("Testing Discord webhook...")
    
    # Sample product data
    product_summaries = [
        (
            {'boxName': 'Test Gaming Laptop', 'boxId': 'SLAPGAMINGLAP123'},
            'IN STOCK',
            '2024-01-01 12:00:00',
            {'last_in_stock': '2024-01-01 12:00:00', 'times_in_stock': 3}
        ),
        (
            {'boxName': 'Test Graphics Card', 'boxId': 'SGCNVIDIA4090RTX'},
            'OUT OF STOCK',
            '2024-01-01 12:00:00',
            {'last_in_stock': '2023-12-15 08:30:00', 'times_in_stock': 1}
        )
    ]
    
    try:
        # Test with product summaries
        send_discord_webhook(
            config, 
            "Test message from CEX Stock Checker", 
            True, 
            "1/2 IN STOCK", 
            product_summaries
        )
        print("✅ Discord webhook test completed successfully!")
        print("Check your Discord channel for the test notification.")
        
    except Exception as e:
        print(f"❌ Discord webhook test failed: {e}")

if __name__ == "__main__":
    test_discord_webhook()