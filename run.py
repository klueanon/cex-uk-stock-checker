#!/usr/bin/env python3
"""
Production runner for CEX Stock Checker web application using Gunicorn
"""

import os
import multiprocessing

def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1

if __name__ == '__main__':
    # Set up Gunicorn configuration
    workers = number_of_workers()
    port = os.environ.get('PORT', '5000')
    
    # Run with Gunicorn for production
    cmd = f"gunicorn --workers {workers} --bind 0.0.0.0:{port} --timeout 120 app:app"
    print(f"Starting CEX Stock Checker with command: {cmd}")
    os.system(cmd)