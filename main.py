import cv2
import sys
from flask import Flask, Response, render_template_string
import threading
import face_recognition
import pickle
import os
from datetime import datetime

app = Flask(__name__)

# Global camera object
camera = None
camera_lock = threading.Lock()

# Face recognition globals
approved_faces = {}
ENCODINGS_FILE = "approved_faces.pkl"
last_recognition_result = {"status": "WAITING", "name": None, "timestamp": None}
recognition_lock = threading.Lock()

def load_approved_faces():
    """Load approved face encodings from file"""
    global approved_faces
    
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, 'rb') as f:
            approved_faces = pickle.load(f)
        print(f"✅ Loaded {len(approved_faces)} approved face(s): {', '.join(approved_faces.keys())}")
        return True
    else:
        print("⚠️  No approved faces found. Run enroll.py to add approved users.")
        return False

def initialize_camera():
    """Initialize the USB camera"""
    global camera
    
    camera = cv2.VideoCapture(0)
    
    if not camera.isOpened():
        print("Error: Could not open camera")
        print("Make sure your USB camera is connected")
        return False
    
    # Set camera properties
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)
    
    print("Camera opened successfully!")
    return True

def recognize_face(frame):
    """Recognize faces in the frame and compare with approved faces"""
    global last_recognition_result
    
    # Convert BGR to RGB for face_recognition
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Detect face locations and encodings
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    
    result = {"status": "NO_FACE", "name": None, "timestamp": datetime.now()}
    
    if len(face_locations) == 0:
        return result, face_locations
    
    # Check each detected face
    for face_encoding in face_encodings:
        # Compare with approved faces
        if approved_faces:
            matches = face_recognition.compare_faces(
                list(approved_faces.values()), 
                face_encoding,
                tolerance=0.6  # Lower = stricter matching
            )
            
            # Find the best match
            if True in matches:
                match_index = matches.index(True)
                name = list(approved_faces.keys())[match_index]
                result = {"status": "APPROVED", "name": name, "timestamp": datetime.now()}
                
                # Print approval message
                print(f"🔓 APPROVED - Access granted to: {name} at {result['timestamp'].strftime('%H:%M:%S')}")
                break
            else:
                result = {"status": "UNKNOWN", "name": None, "timestamp": datetime.now()}
                print(f"🔒 UNKNOWN FACE DETECTED - Access denied at {result['timestamp'].strftime('%H:%M:%S')}")
        else:
            result = {"status": "NO_ENROLLED", "name": None, "timestamp": datetime.now()}
    
    with recognition_lock:
        last_recognition_result = result
    
    return result, face_locations

def generate_frames():
    """Generate frames from the camera for streaming with face recognition"""
    global camera
    frame_count = 0
    
    while True:
        with camera_lock:
            if camera is None or not camera.isOpened():
                break
            
            success, frame = camera.read()
            if not success:
                break
            
            # Perform face recognition every 10 frames (for performance)
            if frame_count % 10 == 0 and approved_faces:
                result, face_locations = recognize_face(frame)
                
                # Draw rectangles and labels on detected faces
                for (top, right, bottom, left) in face_locations:
                    # Choose color based on recognition result
                    if result["status"] == "APPROVED":
                        color = (0, 255, 0)  # Green for approved
                        label = f"✓ {result['name']}"
                    elif result["status"] == "UNKNOWN":
                        color = (0, 0, 255)  # Red for unknown
                        label = "✗ UNKNOWN"
                    else:
                        color = (255, 255, 0)  # Yellow for detected but not processed
                        label = "Detecting..."
                    
                    # Draw rectangle
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    
                    # Draw label background
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                    
                    # Draw label text
                    cv2.putText(frame, label, (left + 6, bottom - 6),
                               cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            
            frame_count += 1
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
        
        # Yield frame in byte format for streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# HTML template for the web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>SmartLock - Face Recognition</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: white;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1 {
            margin-bottom: 10px;
        }
        .container {
            max-width: 800px;
            text-align: center;
        }
        img {
            width: 100%;
            max-width: 640px;
            border: 2px solid #333;
            border-radius: 8px;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
        }
        .status.approved {
            background-color: #2d5016;
            border: 2px solid #4caf50;
        }
        .status.unknown {
            background-color: #5d1616;
            border: 2px solid #f44336;
        }
        .status.waiting {
            background-color: #2a2a2a;
            border: 2px solid #666;
        }
        .info {
            margin-top: 20px;
            padding: 10px;
            background-color: #2a2a2a;
            border-radius: 5px;
            font-size: 14px;
        }
        .enrolled-users {
            margin-top: 15px;
            padding: 10px;
            background-color: #1f1f1f;
            border-radius: 5px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 SmartLock - Face Recognition System</h1>
        <p style="color: #888; margin-top: 0;">Real-time face detection and recognition</p>
        
        <img src="{{ url_for('video_feed') }}" alt="Camera Stream">
        
        <div class="info">
            <p><strong>System Status:</strong> Active</p>
            <p>Green box = Approved access | Red box = Unknown person</p>
        </div>
        
        <div class="enrolled-users">
            <p><strong>📋 Enrolled Users:</strong> {{ enrolled_users }}</p>
            <p style="color: #888; font-size: 12px; margin-top: 10px;">
                Run <code>python enroll.py</code> to add new users
            </p>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """Main page with video stream"""
    enrolled_users = ", ".join(approved_faces.keys()) if approved_faces else "None (Run enroll.py)"
    return render_template_string(HTML_TEMPLATE, enrolled_users=enrolled_users)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def main():
    """
    SmartLock system with face recognition
    Stream live video and recognize approved faces
    """
    print("\n" + "="*50)
    print("🔐 SmartLock - Face Recognition System")
    print("="*50)
    
    # Load approved faces
    load_approved_faces()
    
    # Initialize camera
    if not initialize_camera():
        sys.exit(1)
    
    # Get local IP address
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("\n" + "="*50)
    print("🎥 Web Server Started!")
    print("="*50)
    print(f"\nAccess the camera stream from your browser:")
    print(f"  • Local:   http://localhost:5000")
    print(f"  • Network: http://{local_ip}:5000")
    print("\n📋 Enrolled users:", ", ".join(approved_faces.keys()) if approved_faces else "None")
    print("\n💡 Tip: Run 'python enroll.py' to add approved users")
    print("\nPress Ctrl+C to stop the server")
    print("="*50 + "\n")
    print("🔍 Face recognition active. Watching for faces...\n")
    
    try:
        # Run Flask app
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if camera is not None:
            camera.release()
        print("Camera released")

if __name__ == "__main__":
    main()
