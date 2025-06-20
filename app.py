from flask import Flask, request, jsonify, render_template_string, send_from_directory, url_for
from flask_cors import CORS
import base64, os
from datetime import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    # List all saved images filenames
    images = os.listdir(UPLOAD_FOLDER)
    images = sorted(images, reverse=True)  # newest first

    # Generate image URLs for html
    image_urls = [url_for('uploaded_file', filename=img) for img in images]

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
      <title>Auto Camera Capture & Gallery</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          margin: 20px;
          background: #f0f0f0;
          color: #333;
        }
        h2 {
          text-align: center;
        }
        #camera {
          text-align: center;
          margin-bottom: 30px;
        }
        video, canvas {
          border: 2px solid #444;
          border-radius: 6px;
        }
        #preview {
          margin-top: 10px;
          max-width: 320px;
          border: 2px solid #007bff;
          border-radius: 6px;
          display: block;
          margin-left: auto;
          margin-right: auto;
        }
        #gallery {
          max-width: 960px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 15px;
        }
        #gallery img {
          width: 100%;
          border-radius: 8px;
          box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }
      </style>
    </head>
    <body>
      <h2>Auto Camera Capture & Uploaded Images Gallery</h2>

      <div id="camera">
        <video id="video" width="320" height="240" autoplay></video><br>
        <canvas id="canvas" width="320" height="240" style="display:none;"></canvas>
        <img id="preview" alt="Photo preview"/>
      </div>

      <h3>Gallery</h3>
      <div id="gallery">
        {% for url in image_urls %}
          <img src="{{ url }}" alt="Uploaded image">
        {% else %}
          <p>No images uploaded yet.</p>
        {% endfor %}
      </div>

      <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const preview = document.getElementById('preview');

        async function startCameraAndCapture() {
          try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;

            // Wait 2 seconds before capture to warm up camera
            await new Promise(r => setTimeout(r, 2000));

            const context = canvas.getContext('2d');
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageData = canvas.toDataURL('image/png');
            preview.src = imageData;

            // Upload image automatically
            const res = await fetch('/api/upload_photo', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ image: imageData })
            });
            const result = await res.json();
            //  alert(result.message + "\\nSaved as: " + result.filename);

            // Stop video stream after capture
            stream.getTracks().forEach(track => track.stop());

            // Reload gallery to show new image
            location.reload();

          } catch (err) {
            alert("Camera access denied or error: " + err);
          }
        }

        window.onload = () => {
          startCameraAndCapture();
        };
      </script>
    </body>
    </html>
    ''', image_urls=image_urls)


# Route to serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# API to receive and save photo
@app.route('/api/upload_photo', methods=['POST'])
def upload_photo():
    data = request.get_json()
    image_data = data.get('image')

    if not image_data or ',' not in image_data:
        return jsonify({'error': 'Invalid image data'}), 400

    header, encoded = image_data.split(',', 1)
    image_bytes = base64.b64decode(encoded)

    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, 'wb') as f:
        f.write(image_bytes)

    return jsonify({'message': 'Image saved', 'filename': filename})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Get PORT from environment or default to 5000
    app.run(host="0.0.0.0", port=port, debug=True)
