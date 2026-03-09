import cv2
import numpy as np
import torch
import base64
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from model.model import Mini_Xception
from face_detector.face_detector import HaarCascadeDetector, DnnDetector
from face_alignment.face_alignment import FaceAlignment
from utils import get_label_emotion, histogram_equalization
import torchvision.transforms.transforms as transforms

# 1. Initialize App & Device
app = FastAPI()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Allow CORS for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Load Models Globaly (So we don't reload on every request)
print("Loading models...")
mini_xception = Mini_Xception().to(device)
mini_xception.eval()

# Load weights (Adjust path as needed)
checkpoint = torch.load('checkpoint/model_weights/weights_epoch_75.pth.tar', map_location=device)
mini_xception.load_state_dict(checkpoint['mini_xception'])

face_alignment = FaceAlignment()
# Using Haar for speed in API, or switch to DnnDetector
face_detector = HaarCascadeDetector('face_detector') 
print("Models loaded successfully.")

@app.websocket("/ws/emotion")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # 1. Receive frame from React (base64 string)
            data = await websocket.receive_text()
            
            # 2. Decode base64 to OpenCV image
            # Remove "data:image/jpeg;base64," prefix if present
            if ',' in data:
                data = data.split(',')[1]
            
            image_bytes = base64.b64decode(data)
            np_arr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            # 3. Process Frame (Your existing logic)
            # Detect faces
            faces = face_detector.detect_faces(frame)
            
            response_data = []

            if len(faces) > 0:
                # Process the largest face only for stability
                face = faces[0] 
                (x, y, w, h) = face

                # Alignment & Preprocessing
                input_face = face_alignment.frontalize_face(face, frame)
                input_face = cv2.resize(input_face, (48, 48))
                input_face = histogram_equalization(input_face)
                
                # Transform for PyTorch
                input_face = transforms.ToTensor()(input_face).to(device)
                input_face = torch.unsqueeze(input_face, 0)

                # Inference
                with torch.no_grad():
                    emotion_tensor = mini_xception(input_face)
                    softmax = torch.nn.Softmax(dim=1)
                    emotions_soft = softmax(emotion_tensor).squeeze().cpu().numpy()
                    
                    # Get top emotion
                    emotion_idx = np.argmax(emotions_soft)
                    emotion_label = get_label_emotion(emotion_idx)
                    confidence = round(float(emotions_soft[emotion_idx]), 2)

                    response_data = {
                        "status": "success",
                        "emotion": emotion_label,
                        "confidence": confidence,
                        "box": [int(x), int(y), int(w), int(h)]
                    }
            else:
                response_data = {"status": "no_face"}

            # 4. Send result back to React
            await websocket.send_json(response_data)

    except Exception as e:
        print(f"Connection closed: {e}")