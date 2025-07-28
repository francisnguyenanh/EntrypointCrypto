"""
Notification Manager cho Lambda version
- Sử dụng SNS thay vì email trực tiếp
- Tối ưu cho serverless environment
"""

import boto3
import json
import logging
from datetime import datetime
from typing import Dict, Optional

from lambda_config import LAMBDA_CONFIG, MONITORING_CONFIG

logger = logging.getLogger(__name__)

class LambdaNotificationManager:
    """Quản lý notifications cho Lambda Trading Bot"""
    
    def __init__(self):
        """Initialize SNS client"""
        try:
            self.sns = boto3.client(
                'sns',
                region_name=LAMBDA_CONFIG['aws_region']
            )
            
            # SNS topic ARNs
            self.trade_topic = MONITORING_CONFIG.get('trade_notifications_topic')
            self.error_topic = MONITORING_CONFIG.get('error_notifications_topic')
            
            logger.info("Lambda Notification Manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize notification manager: {e}")
            # Don't raise - notifications are not critical for trading
            self.sns = None
    
    def send_trade_notification(self, trade_data: Dict) -> bool:
        """Gửi thông báo trading"""
        try:
            if not self.sns or not self.trade_topic:
                logger.warning("SNS not configured for trade notifications")
                return False
            
            # Tạo message
            message = self._format_trade_message(trade_data)
            
            # Gửi SNS
            response = self.sns.publish(
                TopicArn=self.trade_topic,
                Message=json.dumps(message, default=str),
                Subject=f"🚀 Trading Alert: {trade_data.get('symbol', 'Unknown')}"
            )
            
            logger.info(f"Trade notification sent: {response['MessageId']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")
            return False
    
    def send_error_notification(self, error_msg: str, error_type: str = "ERROR") -> bool:
        """Gửi thông báo lỗi"""
        try:
            if not self.sns or not self.error_topic:
                logger.warning("SNS not configured for error notifications")
                return False
            
            message = {
                'timestamp': datetime.now().isoformat(),
                'error_type': error_type,
                'error_message': error_msg,
                'service': 'Lambda Trading Bot',
                'environment': 'production' if not LAMBDA_CONFIG.get('sandbox') else 'testnet'
            }
            
            response = self.sns.publish(
                TopicArn=self.error_topic,
                Message=json.dumps(message, default=str),
                Subject=f"🚨 Trading Bot Error: {error_type}"
            )
            
            logger.info(f"Error notification sent: {response['MessageId']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
            return False
    
    def send_emergency_notification(self, message: str) -> bool:
        """Gửi thông báo emergency"""
        try:
            if not self.sns:
                logger.warning("SNS not configured for emergency notifications")
                return False
            
            emergency_message = {
                'timestamp': datetime.now().isoformat(),
                'alert_type': 'EMERGENCY',
                'message': message,
                'service': 'Lambda Trading Bot',
                'action_required': True
            }
            
            # Gửi tới cả 2 topics nếu có
            topics = [self.trade_topic, self.error_topic]
            success_count = 0
            
            for topic in topics:
                if topic:
                    try:
                        response = self.sns.publish(
                            TopicArn=topic,
                            Message=json.dumps(emergency_message, default=str),
                            Subject="🚨 EMERGENCY: Trading Bot Alert"
                        )
                        success_count += 1
                        logger.info(f"Emergency notification sent to {topic}: {response['MessageId']}")
                    except Exception as e:
                        logger.error(f"Failed to send emergency notification to {topic}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending emergency notification: {e}")
            return False
    
    def send_performance_alert(self, metrics: Dict) -> bool:
        """Gửi cảnh báo performance"""
        try:
            if not self.sns or not self.error_topic:
                return False
            
            # Kiểm tra các metrics đáng lo ngại
            alerts = []
            
            execution_time = metrics.get('execution_duration_seconds', 0)
            if execution_time > MONITORING_CONFIG['alert_on_execution_time']:
                alerts.append(f"High execution time: {execution_time}s")
            
            error_rate = metrics.get('error_rate_percent', 0)
            if error_rate > MONITORING_CONFIG['alert_on_error_rate']:
                alerts.append(f"High error rate: {error_rate}%")
            
            if not alerts:
                return True  # No alerts needed
            
            message = {
                'timestamp': datetime.now().isoformat(),
                'alert_type': 'PERFORMANCE',
                'alerts': alerts,
                'metrics': metrics,
                'service': 'Lambda Trading Bot'
            }
            
            response = self.sns.publish(
                TopicArn=self.error_topic,
                Message=json.dumps(message, default=str),
                Subject="⚠️ Performance Alert: Trading Bot"
            )
            
            logger.info(f"Performance alert sent: {response['MessageId']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending performance alert: {e}")
            return False
    
    def _format_trade_message(self, trade_data: Dict) -> Dict:
        """Format trade data cho notification"""
        try:
            status = trade_data.get('status', 'unknown')
            symbol = trade_data.get('symbol', 'Unknown')
            
            if status == 'success':
                emoji = "✅"
                title = "Trade Executed Successfully"
            else:
                emoji = "❌"  
                title = "Trade Failed"
            
            message = {
                'timestamp': datetime.now().isoformat(),
                'title': f"{emoji} {title}",
                'symbol': symbol,
                'status': status,
                'details': {}
            }
            
            # Thêm details cho successful trades
            if status == 'success':
                message['details'] = {
                    'quantity': trade_data.get('quantity', 0),
                    'price': trade_data.get('price', 0),
                    'total_cost': trade_data.get('total_cost', 0),
                    'stop_loss': trade_data.get('stop_loss', 0),
                    'take_profit_1': trade_data.get('tp1_price', 0),
                    'take_profit_2': trade_data.get('tp2_price', 0),
                    'buy_order_id': trade_data.get('buy_order_id', ''),
                    'sl_order_id': trade_data.get('sl_order_id', '')
                }
            else:
                message['details'] = {
                    'error': trade_data.get('error', 'Unknown error')
                }
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting trade message: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'title': "Trade Notification",
                'raw_data': trade_data
            }
    
    def send_analysis_summary(self, analysis_result: Dict) -> bool:
        """Gửi summary của market analysis"""
        try:
            if not self.sns or not self.trade_topic:
                return False
            
            recommendations = analysis_result.get('recommendations', [])
            summary = analysis_result.get('analysis_summary', {})
            
            message = {
                'timestamp': datetime.now().isoformat(),
                'title': "📊 Market Analysis Complete",
                'summary': {
                    'symbols_analyzed': summary.get('analyzed_count', 0),
                    'opportunities_found': summary.get('opportunities_found', 0),
                    'recommendations': len(recommendations)
                },
                'top_recommendations': [
                    {
                        'symbol': rec.get('symbol', ''),
                        'confidence': rec.get('confidence_score', 0),
                        'signal': rec.get('signal', '')
                    }
                    for rec in recommendations[:3]  # Top 3
                ]
            }
            
            response = self.sns.publish(
                TopicArn=self.trade_topic,
                Message=json.dumps(message, default=str),
                Subject="📊 Market Analysis Summary"
            )
            
            logger.info(f"Analysis summary sent: {response['MessageId']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending analysis summary: {e}")
            return False
