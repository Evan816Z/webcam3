import os
import re
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# 图片存储目录
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
os.makedirs(IMAGE_DIR, exist_ok=True)

# 日志存储
log_entries = []


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/logs')
def get_logs():
    after = request.args.get('after', '0', type=int)
    new_logs = log_entries[after:]
    return jsonify({'logs': new_logs, 'total': len(log_entries)})


@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'error': '未收到图片'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    # 用时间戳 + 摄像头标签命名，避免冲突
    camera_label = request.form.get('camera_label', '').strip()
    label_slug = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5-]', '_', camera_label)[:40] if camera_label else ''

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    base_name = f'{timestamp}_{label_slug}' if label_slug else timestamp
    filename = f'{base_name}.jpg'
    filepath = os.path.join(IMAGE_DIR, filename)
    file.save(filepath)

    # 保存设备信息
    device_info = request.form.get('device_info', '')
    if device_info:
        info_filename = f'{base_name}.txt'
        info_filepath = os.path.join(IMAGE_DIR, info_filename)
        with open(info_filepath, 'w', encoding='utf-8') as f:
            f.write(device_info)

    now = datetime.now().strftime('%H:%M:%S')
    print(f'[上传成功] {filename}')

    log_msg = {'time': now, 'filename': filename}
    if device_info:
        try:
            info = json.loads(device_info)
            log_msg['device'] = info.get('userAgent', '')
            log_msg['platform'] = info.get('platform', '')
            log_msg['screen'] = f"{info.get('screenWidth', '')}x{info.get('screenHeight', '')}"
            log_msg['touch'] = info.get('touchSupport', '')
        except:
            pass

    log_entries.append(log_msg)
    return jsonify({'filename': filename, 'path': filepath})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
