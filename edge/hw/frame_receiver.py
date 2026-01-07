from flask import Flask, request
import base64
import cv2
import numpy as np
import os

CURRENT_FRAME_PATH = "/tmp/frame.jpg"

app = Flask(__name__)

@app.route("/frame", methods=["POST"])
def frame():
    data = request.data.decode()
    if "," not in data:
        return "invalid data", 400
    try:
        jpg = base64.b64decode(data.split(",", 1)[1])
    except Exception as e:
        print("base64 decode failed:", e, flush=True)
        return "bad image", 400

    npimg = np.frombuffer(jpg, dtype=np.uint8)
    image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    if image is None:
        print("cv2.imdecode failed", flush=True)
        return "bad jpeg", 400

    cv2.imwrite(CURRENT_FRAME_PATH, image)
    print("wrote /tmp/frame.jpg", flush=True)
    return "ok"

if __name__ == "__main__":
    app.run(port=9001, host="0.0.0.0")






