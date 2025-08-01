"""
Module xử lý lệnh stop cho trading bot
"""
import time
import threading


def listen_for_stop_command(bot_running_ref):
    """
    Lắng nghe lệnh stop từ user
    bot_running_ref: reference đến BOT_RUNNING variable
    """
    while bot_running_ref['value']:
        try:
            # Sử dụng select trên Unix để không block
            import select
            import sys
            
            # Kiểm tra nếu có input sẵn sàng
            if select.select([sys.stdin], [], [], 0.1) == ([sys.stdin], [], []):
                user_input = sys.stdin.readline().strip().lower()
                if user_input == "stop":
                    print("\n🛑 Nhận lệnh dừng bot từ user...")
                    print("⌛ Đang hoàn thành cycle hiện tại và dừng bot...")
                    bot_running_ref['value'] = False
                    break
            else:
                time.sleep(0.1)
        except (EOFError, OSError):
            # Trường hợp không có input hoặc lỗi OS
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Nhận tín hiệu ngắt từ bàn phím...")
            bot_running_ref['value'] = False
            break
        except ImportError:
            # Fallback cho Windows hoặc môi trường không hỗ trợ select
            try:
                user_input = input().strip().lower()
                if user_input == "stop":
                    print("\n🛑 Nhận lệnh dừng bot từ user...")
                    print("⌛ Đang hoàn thành cycle hiện tại và dừng bot...")
                    bot_running_ref['value'] = False
                    break
            except (EOFError, KeyboardInterrupt):
                bot_running_ref['value'] = False
                break


def start_stop_listener(bot_running_ref):
    """Khởi động thread lắng nghe lệnh stop"""
    print("💡 Để dừng bot bất cứ lúc nào, hãy gõ 'stop' và nhấn Enter")
    stop_listener = threading.Thread(target=listen_for_stop_command, args=(bot_running_ref,), daemon=True)
    stop_listener.start()
    return stop_listener
