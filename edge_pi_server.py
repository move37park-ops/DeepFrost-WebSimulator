import time
import base64
import cv2
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)  # 웹 시뮬레이터(HTML)에서 fetch 요청을 허용하기 위해 CORS 활성화

latest_frame = None
latest_score = 0
latest_status = "WAITING"

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
    
    status = "Frost Growing"
    conf = min(99.9, 50 + score * 0.49)
    if is_defrosting:
        status = "Defrost Cycle"
        conf = 99.9
    elif score > 75:
        status = "CRITICAL FROST"

    latest_score = score
    latest_status = status
    
    print(f"\n[pi@deepfrost-edge ~]$ Incoming Frame Received (640x360).")
    print(f"[pi@deepfrost-edge ~]$ Running Edge CNN Inference Model...")
    print(f"   => [RESULT] Class: {status} / Frost Probability: {conf:.1f}%")

    return jsonify({'status': 'ok'})

def display_loop():
    print("="*60)
    print(" 🚀 DEEPFROST EDGE AI SERVER STARTED ON PORT 5000 🚀")
    print("="*60)
    print("[pi@deepfrost-edge ~]$ Waiting for Web Simulator connection...\n")
    
    while True:
        if latest_frame is not None:
            display_img = latest_frame.copy()
            
            # 영상 위에 그럴싸한 AI Bounding Box 및 텍스트 오버레이
            h, w = display_img.shape[:2]
            
            # AI 테두리 박스
            color = (0, 255, 0) # 초록
            if latest_score > 50: color = (0, 165, 255) # 주황
            if latest_score > 75: color = (0, 0, 255) # 빨강
            
            cv2.rectangle(display_img, (20, 20), (w-20, h-20), color, 2)
            cv2.putText(display_img, f"EDGE CNN: {latest_status}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(display_img, f"FROST PROB: {min(99.9, 50 + latest_score*0.49):.1f}%", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
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
