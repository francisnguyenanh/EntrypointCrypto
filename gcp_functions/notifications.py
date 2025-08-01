# Notifications module for GCP Functions
# Tối ưu cho cost và đơn giản

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

# Email configuration from environment
EMAIL_CONFIG = {
    'enabled': os.environ.get('EMAIL_ENABLED', 'False').lower() == 'true',
    'smtp_server': os.environ.get('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.environ.get('EMAIL_SMTP_PORT', '587')),
    'sender': os.environ.get('EMAIL_SENDER'),
    'password': os.environ.get('EMAIL_PASSWORD'),
    'recipient': os.environ.get('EMAIL_RECIPIENT')
}

def send_simple_notification(subject, message, urgent=False):
    """Send simple email notification - cost optimized"""
    try:
        if not EMAIL_CONFIG['enabled']:
            logger.info(f"📧 {subject}: {message}")
            return True
        
        if not all([EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'], EMAIL_CONFIG['recipient']]):
            logger.warning("Email configuration incomplete")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender']
        msg['To'] = EMAIL_CONFIG['recipient']
        msg['Subject'] = f"{'🚨 URGENT - ' if urgent else '📊 '}{subject}"
        
        # Simple body
        body = f"""
Crypto Trading Bot - GCP Functions

{message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Environment: {'TESTNET' if os.environ.get('BINANCE_SANDBOX', 'True') == 'True' else 'LIVE'}

---
Automated Trading System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'])
            server.send_message(msg)
        
        logger.info(f"📧 Email sent: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return False

def send_trade_notification(trade_data):
    """Send trade notification"""
    try:
        subject = f"Trade Executed - {trade_data['symbol']}"
        message = f"""
Symbol: {trade_data['symbol']}
Type: {trade_data['type']}
Quantity: {trade_data['quantity']:,.6f}
Price: ¥{trade_data['price']:,.4f}
Value: ¥{trade_data['value_jpy']:,.2f}
Order ID: {trade_data['order_id']}
        """
        
        return send_simple_notification(subject, message)
        
    except Exception as e:
        logger.error(f"Trade notification error: {e}")
        return False

def send_error_notification(error_message):
    """Send error notification"""
    return send_simple_notification("Trading Error", error_message, urgent=True)
