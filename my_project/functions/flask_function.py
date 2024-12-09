from flask import Flask, request, jsonify, send_from_directory, render_template, url_for
import os
import cv2 as cv
import numpy as np
from netlify import handler

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

UPLOAD_FOLDER1 = 'uploads1'
os.makedirs(UPLOAD_FOLDER1, exist_ok=True)
app.config['UPLOAD_FOLDER1'] = UPLOAD_FOLDER1

@app.route('/')
def index():
    files = sorted(os.listdir(app.config['UPLOAD_FOLDER']), key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)))
    return render_template("index.html", files=files)

@app.route('/upload', methods=['POST'])
def upload_handle():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    file_path = os.path.join(app.config['UPLOAD_FOLDER1'], file.filename)
    file.save(file_path)

    file1 = file_path
    img = cv.imread(file1)
    
    hsv_img = cv.cvtColor(img, cv.COLOR_BGR2HSV)

    lower_thresh = np.array([36, 30, 30])
    higher_thresh = np.array([70, 255, 255])

    mask = cv.inRange(hsv_img, lower_thresh, higher_thresh)

    green = np.zeros_like(img, np.uint8)
    green[mask > 0] = img[mask > 0]

    green_map = np.zeros_like(img, np.uint8)
    green_map[mask > 0] = (0, 255, 0)
    green_pixel = np.count_nonzero(mask)
    total_pixel = mask.size
    print('number of green pixels', green_pixel)
    print('total_pixels:', total_pixel)
    cv.addWeighted(img, .7, green_map, 0.3, 0, green_map)
    cv.imwrite('static/uploads/img1.jpg', img)
    cv.imwrite('static/uploads/img2.jpg', green_map)
    cv.imwrite('static/uploads/img3.jpg', green)

    return jsonify({'message': 'File uploaded successfully', 'file_path': url_for('uploaded_file', filename=file.filename)}), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/image')
def disp():
    files = sorted(os.listdir(app.config['UPLOAD_FOLDER']), key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
    if files:
        urls = [url_for('uploaded_file', filename=file) for file in files[:4]]  # Get URLs for the first four files
        return jsonify({'urls': urls})
    else:
        return jsonify({'error': 'No files found'}), 404

sensor_data_list = []

@app.route('/sensor-data', methods=['POST'])
def receive_sensor_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    sensor_data_list.append(data)

    return jsonify({'message': 'Sensor data received successfully'}), 200

@app.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    return jsonify(sensor_data_list), 200

handler = handler(app)
