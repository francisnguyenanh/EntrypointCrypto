# CRYPTO BASE CURRENCY TP/SL CALCULATION PLAN

## VẤN ĐỀ:
- JPY (fiat): 0.4% TP = khoảng 4 JPY per 1000 JPY (ổn định)
- ETH: 0.4% TP = 0.004 ETH per 1 ETH (có thể quá ít hoặc quá nhiều tùy ETH price)
- BTC: 0.4% TP = 0.004 BTC per 1 BTC (có thể quá ít hoặc quá nhiều tùy BTC price)

## GIẢI PHÁP:
1. **Dynamic TP/SL dựa vào base_currency type**
2. **Adjust percentages cho crypto base currencies**
3. **Consider volatility của base_currency**

## CẢI TIẾN:
1. Detect base_currency type (fiat vs crypto)
2. Adjust TP/SL percentages accordingly
3. Consider current market volatility
4. Maintain reasonable risk/reward ratios
