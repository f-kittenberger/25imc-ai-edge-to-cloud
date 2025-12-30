from flask import Flask, request
import base64
from edge_infer_face import infer


app = Flask(__name__)

@app.route("/frame", methods=["POST"])
def frame():
    data = request.data.decode()
    jpg = base64.b64decode(data.split(",")[1])

    with open("frame.jpg", "wb") as f:
        f.write(jpg)

    infer("frame.jpg")
    return "ok"

if __name__ == "__main__":
    app.run(port=9001)
