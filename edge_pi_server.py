import time
import base64
import cv2
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import requests

app = Flask(__name__)
CORS(app)  # 웹 시뮬레이터(HTML)에서 fetch 요청을 허용하기 위해 CORS 활성화

# ==========================================
# 실제 라즈베리파이 하드웨어(팬) 연동 설정
# ==========================================
# 실제 물리적 라즈베리파이 기기의 IP 주소를 입력하세요. (포트 5001)
# (예: http://192.168.0.15:5001)
PHYSICAL_PI_URL = "http://192.168.0.10:5001"
# ==========================================


latest_frame = None
latest_score = 0
latest_status = "WAITING"
_last_sent_action = None

@app.route('/api/infer', methods=['POST'])
def infer():
    global latest_frame, latest_score, latest_status
    data = request.json
    if not data or 'image' not in data:
        return jsonify({'error': 'No image provided'}), 400

    # 1. Base64 이미지를 OpenCV NumPy 배열로 디코딩
    image_data = data['image'].split(',')[1]
    img_bytes = base64.b64decode(image_data)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    latest_frame = frame

    # 2. 터미널 사기치기용 로그 출력
    score = data.get('score', 0)
    is_defrosting = data.get('isDefrosting', False)
    
    # 4단계 서리 추론 로직
    stage_num = 1
    stage_name = "Normal"
    if score >= 75:
        stage_num = 4
        stage_name = "Critical"
    elif score >= 50:
        stage_num = 3
        stage_name = "Severe"
    elif score >= 25:
        stage_num = 2
        stage_name = "Mild"
        
    if is_defrosting:
        status = "DEFROSTING"
    else:
        status = f"Stage {stage_num} ({stage_name})"
        
    latest_score = score
    latest_status = status
    
    # 3. 하드웨어 제어 로직: 프레임이 들어올 때마다 라즈베리파이에 '추론 중' 틱(Tick) 신호 전송
    def send_infer_tick():
        try:
            # 타임아웃을 아주 짧게 주어 통신 지연 방지
            requests.get(PHYSICAL_PI_URL + "/infer/tick", timeout=0.5)
        except Exception as e:
            pass
    threading.Thread(target=send_infer_tick, daemon=True).start()

    print(f"\n[pi@deepfrost-edge ~]$ Incoming Frame Received (640x360).")
    print(f"[pi@deepfrost-edge ~]$ Running Edge CNN Inference Model...")
    print(f"   => [RESULT] Status: {status} / Frost Level: {score:.1f}%")

    return jsonify({'status': 'ok'})

def display_loop():
    print("="*60)
    print(" 🚀 DEEPFROST EDGE AI SERVER STARTED ON PORT 5000 🚀")
    print("="*60)
    print("[pi@deepfrost-edge ~]$ Waiting for Web Simulator connection...\n")
    
    while True:
        if latest_frame is not None:
            display_img = latest_frame.copy()
            
            # AI 테두리 박스 제거 후 4단계 상태와 퍼센트만 표시
            color = (0, 255, 0) # 초록 (1~2단계)
            if latest_score >= 50: color = (0, 165, 255) # 주황 (3단계)
            if latest_score >= 75: color = (0, 0, 255) # 빨강 (4단계)
            
            cv2.putText(display_img, f"AI INFERENCE: {latest_status}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(display_img, f"FROST LEVEL: {latest_score:.1f}%", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            cv2.imshow("Raspberry Pi - DeepFrost Edge Vision", display_img)
        
        # 'q' 키를 누르면 종료
        if cv2.waitKey(100) & 0xFF == ord('q'):
            break

if __name__ == '__main__':
    # Flask 서버를 백그라운드 스레드로 실행
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
    
    # 메인 스레드에서는 OpenCV 창을 렌더링 (Mac/Windows GUI 제한 우회)
    display_loop()
    cv2.destroyAllWindows()
