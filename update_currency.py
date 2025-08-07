#!/usr/bin/env python3
"""
Script để cập nhật tất cả ký hiệu ¥ thành base_currency động trong app.py
"""

import re

def update_currency_symbols():
    # Đọc file app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup original
    with open('app_backup.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Pattern để tìm các f-string có ¥
    patterns = [
        # f"...¥{variable}..." -> f"...{base_currency} {variable}..."
        (r'f"([^"]*?)¥\{([^}]+)\}([^"]*?)"', r'f"\1{base_currency} {\2}\3"'),
        # f'...¥{variable}...' -> f'...{base_currency} {variable}...'
        (r"f'([^']*?)¥\{([^}]+)\}([^']*?)'", r"f'\1{base_currency} {\2}\3'"),
    ]
    
    # Áp dụng các pattern
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Thêm base_currency = TRADING_CONFIG.get('base_currency', 'JPY') vào các hàm cần thiết
    lines = content.split('\n')
    updated_lines = []
    
    for i, line in enumerate(lines):
        updated_lines.append(line)
        
        # Nếu dòng có {base_currency} nhưng chưa có khai báo base_currency
        if '{base_currency}' in line and 'def ' not in line:
            # Tìm hàm chứa dòng này
            func_start = i
            while func_start >= 0 and not lines[func_start].strip().startswith('def '):
                func_start -= 1
            
            if func_start >= 0:
                # Kiểm tra xem trong hàm đã có khai báo base_currency chưa
                has_base_currency = False
                for j in range(func_start, i):
                    if 'base_currency = TRADING_CONFIG.get(' in lines[j]:
                        has_base_currency = True
                        break
                
                # Nếu chưa có, thêm vào
                if not has_base_currency:
                    indent = len(line) - len(line.lstrip())
                    if indent > 0:
                        base_currency_line = ' ' * indent + "base_currency = TRADING_CONFIG.get('base_currency', 'JPY')"
                        updated_lines.insert(-1, base_currency_line)
    
    # Ghi file mới
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(updated_lines))
    
    print("✅ Đã cập nhật tất cả ký hiệu ¥ thành base_currency động")
    print("✅ File backup được lưu tại app_backup.py")

if __name__ == "__main__":
    update_currency_symbols()
