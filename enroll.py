#!/usr/bin/env python3
"""
Enrollment script to register approved faces for the smart lock system.
Run this script to capture and save face encodings of authorized users.
"""

import cv2
import face_recognition
import pickle
import os
import sys

ENCODINGS_FILE = "approved_faces.pkl"

def capture_and_encode_face(name):
    """Capture face from camera and generate encoding"""
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return None
    
    print(f"\n📸 Capturing face for: {name}")
    print("=" * 50)
    print("Position your face in front of the camera")
    print("Press SPACE to capture when ready")
    print("Press 'q' to cancel")
    print("=" * 50 + "\n")
    
    face_encoding = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error reading frame")
            break
        
        # Convert BGR to RGB for face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces in the frame
        face_locations = face_recognition.face_locations(rgb_frame)
        
        # Draw rectangles around detected faces
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, "Face Detected", (left, top - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Display instructions
        cv2.putText(frame, "Press SPACE to capture", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Press Q to cancel", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show the frame
        cv2.imshow('Enroll Face - SmartLock', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        # Capture on SPACE
        if key == ord(' '):
            if len(face_locations) == 0:
                print("⚠️  No face detected! Please try again.")
                continue
            elif len(face_locations) > 1:
                print("⚠️  Multiple faces detected! Please ensure only one person is in frame.")
                continue
            else:
                # Generate face encoding
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                if len(face_encodings) > 0:
                    face_encoding = face_encodings[0]
                    print("✅ Face captured successfully!")
                    
                    # Save the image for reference
                    filename = f"{name.replace(' ', '_')}_enrolled.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"📁 Reference image saved as: {filename}")
                    break
        
        # Cancel on 'q'
        elif key == ord('q'):
            print("❌ Enrollment cancelled")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    return face_encoding

def load_approved_faces():
    """Load existing approved face encodings"""
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, 'rb') as f:
            return pickle.load(f)
    return {}

def save_approved_faces(approved_faces):
    """Save approved face encodings to file"""
    with open(ENCODINGS_FILE, 'wb') as f:
        pickle.dump(approved_faces, f)
    print(f"💾 Encodings saved to {ENCODINGS_FILE}")

def main():
    print("\n" + "=" * 50)
    print("🔐 SmartLock - Face Enrollment System")
    print("=" * 50)
    
    # Load existing approved faces
    approved_faces = load_approved_faces()
    
    if approved_faces:
        print(f"\n📋 Currently enrolled users: {', '.join(approved_faces.keys())}")
    else:
        print("\n📋 No users enrolled yet")
    
    # Get name for new enrollment
    name = input("\nEnter name for new user (or 'quit' to exit): ").strip()
    
    if name.lower() == 'quit':
        print("Exiting enrollment system")
        return
    
    if not name:
        print("❌ Error: Name cannot be empty")
        return
    
    if name in approved_faces:
        overwrite = input(f"⚠️  User '{name}' already exists. Overwrite? (yes/no): ").strip().lower()
        if overwrite != 'yes':
            print("Enrollment cancelled")
            return
    
    # Capture and encode face
    face_encoding = capture_and_encode_face(name)
    
    if face_encoding is not None:
        # Add to approved faces
        approved_faces[name] = face_encoding
        
        # Save to file
        save_approved_faces(approved_faces)
        
        print("\n" + "=" * 50)
        print(f"✅ SUCCESS: {name} has been enrolled!")
        print(f"📊 Total enrolled users: {len(approved_faces)}")
        print("=" * 50 + "\n")
    else:
        print("❌ Enrollment failed")

if __name__ == "__main__":
    main()
