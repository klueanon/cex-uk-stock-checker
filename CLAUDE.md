# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- **Web UI (Development)**: `python app.py` - Runs Flask dev server on port 5001
- **Web UI (Production)**: `python run.py` - Runs with Gunicorn on configurable port
- **Command Line**: `python stock_check.py` - Runs stock checker in CLI mode
- **Docker**: `docker-compose up -d` - Runs containerized application on port 5000

### Testing
- **Discord Test**: `python test_discord.py` - Tests Discord webhook notifications

### Dependencies
- **Install**: `pip install -r requirements.txt`
- **Core deps**: requests, beautifulsoup4, PyYAML, Flask, gunicorn
- **Test Discord**: `python test_discord.py` - Tests Discord webhook notifications

## Architecture Overview

### Core Components
- **stock_check.py**: Main stock checking engine with CEX API integration, email/Discord notifications
- **app.py**: Flask web UI for managing products and viewing status  
- **run.py**: Production runner using Gunicorn
- **templates/**: HTML templates for web interface (base.html, index.html, settings.html)

### Data Flow
1. **Product monitoring**: Checks CEX UK API (`https://wss2.cex.uk.webuy.io/v3/boxes/{id}/detail`)
2. **Stock detection**: Combines API data with HTML parsing for availability
3. **Notifications**: Sends Discord webhook notifications with rich embeds
4. **History tracking**: Maintains JSON files with stock history and webhook logs per product

### Key Architecture Patterns
- **Dual mode**: CLI mode (`stock_check.py`) vs Web UI mode (`app.py`)
- **Threading**: Web UI runs stock checker in background thread
- **Configuration**: YAML-based config (Discord-only, no email)
- **Persistence**: JSON files for stock history and webhook logs, YAML for configuration
- **Real-time UI**: Next check countdown timer and webhook log preview

## Configuration

### Environment Setup
- Copy `config/checker.yaml.example` to `config/checker.yaml`
- Configure Discord webhook URL in web UI settings
- No environment variables required (all configuration via web UI)

### Key Config Sections
- **items**: Array of CEX product IDs to monitor
- **request_delay**: Check interval in seconds (minimum 60)
- **discord_enabled**: Boolean to enable/disable Discord notifications
- **notification_mode**: 'all_checks' (every check) or 'stock_changes' (only when in stock)
- **discord.webhook_url**: Discord webhook URL for notifications
- **store_ids**: Optional array for specific store monitoring (empty = general availability)

## File Structure
- **config/**: Configuration files (YAML)
- **data/**: Stock history, webhook logs, and debug files (Docker volume)
- **templates/**: Flask HTML templates
- **debug_*.html**: Per-product HTML responses for debugging
- **stock_history.json**: Global stock history tracking
- **webhook_logs.json**: Discord webhook delivery logs (last 100)

## Notification System
- **Discord-only**: Uses webhooks for all notifications
- **Rich embeds**: Product details, stock status, and direct CEX links
- **Smart notifications**: Choose between all checks or stock-change-only mode
- **Status tracking**: Start/stop notifications and delivery logs
- **UI integration**: Real-time webhook logs and latest notification preview