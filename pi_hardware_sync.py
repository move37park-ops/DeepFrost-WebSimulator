import time
from flask import Flask, jsonify
try:
    from gpiozero import OutputDevice
    # 기본 팬(또는 릴레이/트랜지스터) 연결 핀: GPIO 18 (BCM 기준)
    # 핀 번호가 다르다면 이 부분을 수정하세요!
    fan = OutputDevice(18)
    hardware_available = True
except Exception as e:
    print(f"[경고] GPIO 모듈 로드 실패 (라즈베리파이 환경이 아니거나 권한 부족): {e}")
    fan = None
    hardware_available = False

app = Flask(__name__)

@app.route('/fan/on', methods=['GET'])
def fan_on():
    if hardware_available and fan:
        fan.on()
    print("\n[PI 하드웨어] 🌀 엣지 노트북으로부터 명령 수신: 팬 작동 시작! (제상 가동)")
    return jsonify({"status": "ok", "action": "fan_on", "hardware": hardware_available})

@app.route('/fan/off', methods=['GET'])
def fan_off():
    if hardware_available and fan:
        fan.off()
    print("\n[PI 하드웨어] 🛑 엣지 노트북으로부터 명령 수신: 팬 작동 정지. (착상/일반 가동)")
    return jsonify({"status": "ok", "action": "fan_off", "hardware": hardware_available})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "hardware": hardware_available})

if __name__ == '__main__':
    print("="*60)
    print(" 🍓 물리적 라즈베리파이 하드웨어 동기화 서버 시작 🍓 ")
    print("="*60)
    print(" - 포트: 5001")
    print(" - 제어 핀: BCM GPIO 18")
    print(" - 이 스크립트를 실제 라즈베리파이 안에서 실행해두세요.")
    print("="*60)
    # 모든 IP에서 접속 가능하도록 0.0.0.0 개방
    app.run(host='0.0.0.0', port=5001, debug=False)
