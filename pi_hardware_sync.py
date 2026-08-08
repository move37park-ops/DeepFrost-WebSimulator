import time
import threading
from flask import Flask, jsonify
try:
    from gpiozero import OutputDevice, LED
    # 팬(또는 릴레이) 연결 핀: GPIO 18, 동작 표시(추론) LED: GPIO 23
    fan = OutputDevice(18)
    # 추론 깜빡임용 LED가 있다면 사용
    try:
        infer_led = LED(23)
    except:
        infer_led = None
    hardware_available = True
except Exception as e:
    print(f"[경고] GPIO 모듈 로드 실패 (라즈베리파이 환경이 아니거나 권한 부족): {e}")
    fan = None
    infer_led = None
    hardware_available = False

app = Flask(__name__)
last_tick_time = 0
is_inferring = False

def hardware_watchdog():
    global is_inferring
    while True:
        # 마지막으로 추론 프레임을 받은 지 2초가 지나면 멈춤
        if is_inferring and (time.time() - last_tick_time > 2.0):
            is_inferring = False
            if hardware_available and fan:
                fan.off()
            print("\n[PI 하드웨어] 💤 추론 요청 없음. (CPU IDLE -> 쿨링팬 정지)")
        time.sleep(0.5)

threading.Thread(target=hardware_watchdog, daemon=True).start()

@app.route('/infer/tick', methods=['GET'])
def infer_tick():
    global last_tick_time, is_inferring
    last_tick_time = time.time()
    
    if not is_inferring:
        is_inferring = True
        if hardware_available and fan:
            fan.on()
        print("\n[PI 하드웨어] 🚀 실시간 영상 수신 중! (추론 연산 부하 -> 쿨링팬 100% 가동!)")
        
    # 만약 LED가 있다면 한 번 깜빡이게 함 (비동기)
    if hardware_available and infer_led:
        def blink():
            infer_led.on()
            time.sleep(0.1)
            infer_led.off()
        threading.Thread(target=blink).start()
        
    return jsonify({"status": "ok", "action": "infer_tick", "hardware": hardware_available})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "hardware": hardware_available})

if __name__ == '__main__':
    print("="*60)
    print(" 🍓 물리적 라즈베리파이 하드웨어(추론 모방) 서버 시작 🍓 ")
    print("="*60)
    print(" - 포트: 5001")
    print(" - 쿨링팬 제어 핀: BCM GPIO 18")
    print(" - 상태 표시 LED (옵션): BCM GPIO 23")
    print("="*60)
    app.run(host='0.0.0.0', port=5001, debug=False)
