# 🚀 Google Cloud Functions Deployment Guide

## 📋 Tổng Quan
Deploy Crypto Trading Bot lên Google Cloud Functions với:
- ✅ Cost-optimized architecture  
- ✅ Simplified logic để tiết kiệm tài nguyên
- ✅ Cloud Scheduler automation
- ✅ Firestore database
- ✅ Email notifications

## 💰 Cost Optimization Features
- **Balanced approach**: 2 trades per execution cho diversification
- **Enhanced analysis**: Complex technical analysis với 1000 candles
- **Better accuracy**: Multiple indicators (RSI, MACD, BB, SMA)
- **Connection reuse**: Cached connections
- **Efficient data storage**: Firestore minimal writes

## 🏗️ Bước 1: Chuẩn Bị GCP Project

### 1.1 Tạo Project
1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới: `crypto-trading-bot`
3. Enable APIs:
   - Cloud Functions API
   - Cloud Scheduler API  
   - Firestore API
   - Cloud Build API

### 1.2 Setup Firestore
1. Vào **Firestore** → **Create database**
2. Chọn **Native mode**
3. Chọn region: `asia-southeast1` (Singapore)
4. Security rules: Start in test mode

## 🔧 Bước 2: Deploy Cloud Function

### 2.1 Chuẩn Bị Files
Files cần deploy:
```
gcp_functions/
├── main.py              # Main function code
├── requirements.txt     # Dependencies  
├── notifications.py     # Email notifications
└── .env.yaml           # Environment variables (tạo riêng)
```

### 2.2 Tạo Environment Variables File
Tạo file `.env.yaml`:
```yaml
# Binance API Configuration
BINANCE_API_KEY: "your_binance_api_key_here"
BINANCE_SECRET: "your_binance_secret_here"  
BINANCE_SANDBOX: "True"  # False for live trading

# Trading Configuration
TRADING_ENABLED: "True"

# GCP Configuration
GCP_PROJECT_ID: "your-project-id"

# Email Configuration (Optional)
EMAIL_ENABLED: "False"  # Set to True if want email
EMAIL_SMTP_SERVER: "smtp.gmail.com"
EMAIL_SMTP_PORT: "587"
EMAIL_SENDER: "your-email@gmail.com"
EMAIL_PASSWORD: "your-app-password"
EMAIL_RECIPIENT: "recipient@gmail.com"
```

### 2.3 Deploy Function - Manual Console Method

**Vì bạn sẽ deploy thủ công, hãy làm theo các bước sau:**

1. **Vào Cloud Functions Console**
   - Truy cập: https://console.cloud.google.com/functions
   - Chọn project của bạn
   - Click **CREATE FUNCTION**

2. **Configuration Tab**:
   - **Function name**: `crypto-trading-bot`
   - **Region**: `asia-southeast1` (Singapore)
   - **Trigger type**: **HTTP**
   - **Authentication**: **Allow unauthenticated invocations** ✅
   - Click **SAVE** và **NEXT**

3. **Runtime Tab**:
   - **Runtime**: `Python 3.9`
   - **Entry point**: `crypto_trading_main`
   - **Memory allocated**: `512 MB`
   - **Timeout**: `540` seconds
   - **Maximum instances**: `1` (để control cost)

4. **Environment Variables**:
   Click **Runtime, build, connections and security settings** → **Environment variables**
   ```
   BINANCE_API_KEY = your_binance_api_key_here
   BINANCE_SECRET = your_binance_secret_here
   BINANCE_SANDBOX = True
   TRADING_ENABLED = True
   GCP_PROJECT_ID = your-project-id
   EMAIL_ENABLED = False
   ```

5. **Source Code**:
   - **Source code**: Inline editor
   - **main.py**: Copy toàn bộ nội dung từ file `main.py`
   - **requirements.txt**: Copy nội dung từ file `requirements.txt`
   - Click **ADD FILE** → **notifications.py**: Copy nội dung từ file `notifications.py`

6. **Deploy**:
   - Click **DEPLOY** (có thể mất 2-3 phút)
   - Đợi status chuyển thành ✅

7. **Get Function URL**:
   - Sau khi deploy xong, click vào function name
   - Tab **TRIGGER** → copy **Trigger URL**
   - URL sẽ có dạng: `https://asia-southeast1-PROJECT_ID.cloudfunctions.net/crypto-trading-bot`

## ⏰ Bước 3: Setup Cloud Scheduler

### 3.1 Tạo Scheduled Job - Manual Console
1. **Vào Cloud Scheduler Console**
   - Truy cập: https://console.cloud.google.com/cloudscheduler
   - Chọn project của bạn
   - Click **CREATE JOB**

2. **Define the schedule**:
   - **Name**: `crypto-trading-schedule`
   - **Region**: `asia-southeast1`
   - **Description**: `Automated crypto trading bot execution`
   - **Frequency**: `0 */1 * * *` (mỗi giờ)
   - **Timezone**: `Asia/Ho_Chi_Minh`

3. **Configure the execution**:
   - **Target Type**: **HTTP**
   - **URL**: Paste Function Trigger URL từ step 2.7
   - **HTTP Method**: **POST**
   - **Headers**: 
     ```
     Content-Type: application/json
     ```
   - **Body**:
     ```json
     {"action": "analyze_and_trade"}
     ```

4. **Click CREATE**

5. **Test Job**:
   - Click vào job name vừa tạo
   - Click **RUN NOW** để test
   - Check **History** tab để xem kết quả

### 3.2 Test Scheduler
- Trong Cloud Scheduler Console, click **RUN NOW**
- Check function logs: Cloud Functions Console → Function → **LOGS** tab
- Verify execution: Firestore Console → **Data** tab để xem trades

## 🧪 Bước 4: Testing

### 4.1 Test Function Directly - Manual Console Testing
**Sử dụng GCP Console để test:**

1. **Vào Cloud Functions Console**
2. **Click vào function name** `crypto-trading-bot`
3. **Tab TESTING**:

**Test 1: Check Balance**
```json
{"action": "get_balance"}
```
Click **TEST THE FUNCTION**

**Test 2: Analysis Only**
```json
{"action": "analyze_only"}
```
Click **TEST THE FUNCTION**

**Test 3: Full Trading**
```json
{"action": "analyze_and_trade"}
```
Click **TEST THE FUNCTION**

4. **Xem kết quả trong Output section**
5. **Check logs trong LOGS tab**

### 4.2 Monitor Logs
- **Cloud Functions Console** → Function → Logs
- **Firestore Console** → Data để xem trades

## 💰 Bước 5: Cost Monitoring

### 5.1 Set Budget Alerts - Manual Console
1. **Vào Billing Console**
   - Truy cập: https://console.cloud.google.com/billing
   - Chọn **Budgets & alerts**
   - Click **CREATE BUDGET**

2. **Budget setup**:
   - **Name**: `Crypto Trading Bot Budget`
   - **Budget amount**: `$10` per month
   - **Include projects**: Chọn project của bạn
   - **Services**: All services
   - **Alert thresholds**: 50%, 75%, 90%, 100%
   - **Email recipients**: Nhập email của bạn
   - Click **FINISH**

### 5.2 Monitor Usage
- **Cloud Functions** → Metrics
- **Firestore** → Usage
- Expected cost: $2-5/month

## 📊 Bước 6: Monitoring & Maintenance

### 6.1 Logs Monitoring
```bash
# View function logs
gcloud functions logs read crypto-trading-bot --region=asia-southeast1

# Follow real-time logs  
gcloud functions logs tail crypto-trading-bot --region=asia-southeast1
```

### 6.2 Function Metrics
- **Invocations**: Số lần chạy
- **Duration**: Thời gian thực thi
- **Memory usage**: RAM sử dụng
- **Errors**: Số lần lỗi

### 6.3 Firestore Data Structure
```
Collections:
├── account_snapshots/     # Balance history
├── analysis/             # Market analysis results  
├── trades/               # Executed trades
└── execution_logs/       # Function execution logs
```

## ⚙️ Bước 7: Configuration Tuning

### 7.1 Adjust Frequency
```bash
# Chạy mỗi 30 phút (tiết kiệm hơn)
0 */30 * * *

# Chỉ chạy trong giờ trading (9AM-9PM)  
0 9-21 * * *

# Chỉ chạy các ngày trong tuần
0 9-21 * * 1-5
```

### 7.2 Resource Optimization
```yaml
# Function settings cho cost optimization
Memory: 256MB      # Giảm từ 512MB
Timeout: 300s      # Giảm từ 540s
Max instances: 1   # Prevent parallel execution
```

## 🔒 Bước 8: Security Best Practices

### 8.1 API Keys Security
- Không commit .env.yaml vào git
- Sử dụng Secret Manager thay vì env vars
- Rotate API keys định kỳ

### 8.2 Function Security  
- Enable authentication nếu cần
- Restrict source IPs
- Monitor unusual activity

## 🎯 Summary

Sau khi deploy xong:

✅ **Cost-optimized**: ~$2-5/month
✅ **Auto-trading**: Chạy theo schedule
✅ **Monitoring**: Logs + Firestore data
✅ **Notifications**: Email alerts
✅ **Scalable**: GCP infrastructure

**Expected Performance**:
- Execution time: 60-120 seconds (due to enhanced analysis)
- Memory usage: 300-500MB (due to 1000 candles data)
- Cost per execution: ~$0.002
- Monthly cost: $3-8 (still much cheaper than VPS)
- Accuracy: Higher due to comprehensive analysis

🎉 **Ready for production trading!**
