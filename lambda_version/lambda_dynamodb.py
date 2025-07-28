"""
DynamoDB Manager cho Lambda version
- Thay thế file storage bằng DynamoDB
- Tối ưu cho serverless architecture
"""

import boto3
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from boto3.dynamodb.conditions import Key, Attr

from lambda_config import DYNAMODB_TABLES, LAMBDA_CONFIG

logger = logging.getLogger(__name__)

class DynamoDBManager:
    """Quản lý DynamoDB cho Lambda Trading Bot"""
    
    def __init__(self):
        """Initialize DynamoDB connection"""
        try:
            self.dynamodb = boto3.resource(
                'dynamodb', 
                region_name=LAMBDA_CONFIG['aws_region']
            )
            
            # Initialize table references
            self.tables = {}
            for table_name, table_full_name in DYNAMODB_TABLES.items():
                self.tables[table_name] = self.dynamodb.Table(table_full_name)
            
            logger.info("DynamoDB Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB: {e}")
            raise
    
    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """Convert floats to Decimal for DynamoDB compatibility"""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(v) for v in obj]
        else:
            return obj
    
    def _convert_decimal_to_float(self, obj: Any) -> Any:
        """Convert Decimal back to float for JSON serialization"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimal_to_float(v) for v in obj]
        else:
            return obj
    
    # =============================================================================
    # SYSTEM STATUS MANAGEMENT
    # =============================================================================
    
    def get_system_status(self, status_key: str) -> Dict:
        """Lấy system status từ DynamoDB"""
        try:
            response = self.tables['system_status'].get_item(
                Key={'status_key': status_key}
            )
            
            item = response.get('Item', {})
            return self._convert_decimal_to_float(item)
            
        except Exception as e:
            logger.error(f"Error getting system status {status_key}: {e}")
            return {}
    
    def set_system_status(self, status_key: str, value: Any) -> bool:
        """Set system status trong DynamoDB"""
        try:
            item = {
                'status_key': status_key,
                'value': self._convert_floats_to_decimal(value),
                'last_updated': datetime.now().isoformat(),
                'ttl': int((datetime.now() + timedelta(days=30)).timestamp())
            }
            
            self.tables['system_status'].put_item(Item=item)
            return True
            
        except Exception as e:
            logger.error(f"Error setting system status {status_key}: {e}")
            return False
    
    # =============================================================================
    # ACCOUNT MANAGEMENT
    # =============================================================================
    
    def save_account_snapshot(self, account_info: Dict) -> bool:
        """Lưu snapshot tài khoản"""
        try:
            timestamp = datetime.now().isoformat()
            
            item = {
                'snapshot_id': f"snapshot_{int(datetime.now().timestamp())}",
                'timestamp': timestamp,
                'account_info': self._convert_floats_to_decimal(account_info),
                'ttl': int((datetime.now() + timedelta(days=7)).timestamp())  # 7 days retention
            }
            
            self.tables['account_snapshots'].put_item(Item=item)
            return True
            
        except Exception as e:
            logger.error(f"Error saving account snapshot: {e}")
            return False
    
    def get_latest_account_snapshot(self) -> Optional[Dict]:
        """Lấy snapshot tài khoản mới nhất"""
        try:
            response = self.tables['account_snapshots'].scan(
                Limit=1,
                ScanIndexForward=False
            )
            
            items = response.get('Items', [])
            if items:
                return self._convert_decimal_to_float(items[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest account snapshot: {e}")
            return None
    
    # =============================================================================
    # TRADING RECORDS
    # =============================================================================
    
    def save_trade_record(self, trade_data: Dict) -> bool:
        """Lưu record giao dịch"""
        try:
            timestamp = datetime.now().isoformat()
            trade_id = f"trade_{int(datetime.now().timestamp())}_{trade_data.get('symbol', 'unknown')}"
            
            item = {
                'trade_id': trade_id,
                'timestamp': timestamp,
                'symbol': trade_data.get('symbol', ''),
                'trade_data': self._convert_floats_to_decimal(trade_data),
                'status': trade_data.get('status', 'unknown'),
                'ttl': int((datetime.now() + timedelta(days=90)).timestamp())  # 90 days retention
            }
            
            self.tables['trades'].put_item(Item=item)
            logger.info(f"Saved trade record: {trade_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving trade record: {e}")
            return False
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Lấy các giao dịch gần đây"""
        try:
            response = self.tables['trades'].scan(
                Limit=limit,
                ScanIndexForward=False
            )
            
            items = response.get('Items', [])
            return [self._convert_decimal_to_float(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []
    
    def get_trades_by_symbol(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Lấy giao dịch theo symbol"""
        try:
            response = self.tables['trades'].scan(
                FilterExpression=Attr('symbol').eq(symbol),
                Limit=limit
            )
            
            items = response.get('Items', [])
            return [self._convert_decimal_to_float(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error getting trades for {symbol}: {e}")
            return []
    
    # =============================================================================
    # ORDER MANAGEMENT
    # =============================================================================
    
    def save_order_record(self, order_data: Dict) -> bool:
        """Lưu record order"""
        try:
            timestamp = datetime.now().isoformat()
            order_id = order_data.get('order_id', f"order_{int(datetime.now().timestamp())}")
            
            item = {
                'order_id': str(order_id),
                'timestamp': timestamp,
                'symbol': order_data.get('symbol', ''),
                'order_data': self._convert_floats_to_decimal(order_data),
                'status': order_data.get('status', 'unknown'),
                'ttl': int((datetime.now() + timedelta(days=30)).timestamp())
            }
            
            self.tables['orders'].put_item(Item=item)
            return True
            
        except Exception as e:
            logger.error(f"Error saving order record: {e}")
            return False
    
    def update_order_status(self, order_id: str, status: str, order_data: Dict) -> bool:
        """Cập nhật trạng thái order"""
        try:
            self.tables['orders'].update_item(
                Key={'order_id': str(order_id)},
                UpdateExpression='SET #status = :status, order_data = :order_data, last_updated = :timestamp',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':order_data': self._convert_floats_to_decimal(order_data),
                    ':timestamp': datetime.now().isoformat()
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"Error updating order status {order_id}: {e}")
            return False
    
    def get_active_orders(self) -> List[Dict]:
        """Lấy các orders đang active"""
        try:
            # Scan for orders with status not in completed states
            response = self.tables['orders'].scan(
                FilterExpression=Attr('status').is_in(['open', 'partial'])
            )
            
            items = response.get('Items', [])
            return [self._convert_decimal_to_float(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error getting active orders: {e}")
            return []
    
    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """Lấy order theo ID"""
        try:
            response = self.tables['orders'].get_item(
                Key={'order_id': str(order_id)}
            )
            
            item = response.get('Item')
            if item:
                return self._convert_decimal_to_float(item)
            return None
            
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    # =============================================================================
    # ANALYSIS RESULTS
    # =============================================================================
    
    def save_analysis_result(self, analysis_data: Dict) -> bool:
        """Lưu kết quả phân tích"""
        try:
            timestamp = datetime.now().isoformat()
            analysis_id = f"analysis_{int(datetime.now().timestamp())}"
            
            item = {
                'analysis_id': analysis_id,
                'timestamp': timestamp,
                'analysis_data': self._convert_floats_to_decimal(analysis_data),
                'recommendations_count': len(analysis_data.get('recommendations', [])),
                'ttl': int((datetime.now() + timedelta(days=7)).timestamp())
            }
            
            self.tables['analysis'].put_item(Item=item)
            return True
            
        except Exception as e:
            logger.error(f"Error saving analysis result: {e}")
            return False
    
    def get_recent_analysis(self, limit: int = 5) -> List[Dict]:
        """Lấy các phân tích gần đây"""
        try:
            response = self.tables['analysis'].scan(
                Limit=limit,
                ScanIndexForward=False
            )
            
            items = response.get('Items', [])
            return [self._convert_decimal_to_float(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error getting recent analysis: {e}")
            return []
    
    # =============================================================================
    # PERFORMANCE METRICS
    # =============================================================================
    
    def save_performance_metrics(self, metrics: Dict) -> bool:
        """Lưu performance metrics"""
        try:
            timestamp = datetime.now().isoformat()
            
            item = {
                'metric_id': f"metrics_{int(datetime.now().timestamp())}",
                'timestamp': timestamp,
                'metrics': self._convert_floats_to_decimal(metrics),
                'ttl': int((datetime.now() + timedelta(days=30)).timestamp())
            }
            
            # Sử dụng system_status table để lưu metrics
            self.tables['system_status'].put_item(Item=item)
            return True
            
        except Exception as e:
            logger.error(f"Error saving performance metrics: {e}")
            return False
    
    # =============================================================================
    # CLEANUP UTILITIES
    # =============================================================================
    
    def cleanup_old_records(self) -> Dict:
        """Cleanup old records (TTL sẽ tự động xử lý)"""
        # DynamoDB TTL sẽ tự động xóa các records cũ
        # Function này chỉ để manual cleanup nếu cần
        
        result = {
            'message': 'TTL-based cleanup is automatic',
            'manual_cleanup_executed': False
        }
        
        try:
            # Có thể thêm logic manual cleanup ở đây nếu cần
            logger.info("Cleanup check completed - relying on TTL")
            return result
            
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
            result['error'] = str(e)
            return result
