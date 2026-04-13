from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import base64
import json
import time
import io

app = Flask(__name__)

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=700,700')
    return webdriver.Chrome(options=options)

@app.route('/convert', methods=['POST'])
def convert():
    try:
        raw = request.get_data(as_text=True)
        data = json.loads(raw)
        if isinstance(data, str):
            data = json.loads(data)

        html = data.get('html', '')
        if not html:
            return jsonify({'error': 'No HTML provided'}), 400

        driver = get_driver()
        driver.get('data:text/html;charset=utf-8,' + html)
        time.sleep(2)
        png_bytes = driver.get_screenshot_as_png()
        driver.quit()

        # Convert PNG → WEBP
        img = Image.open(io.BytesIO(png_bytes))
        webp_buffer = io.BytesIO()
        img.save(webp_buffer, format='WEBP', quality=90)
        webp_bytes = webp_buffer.getvalue()

        img_base64 = base64.b64encode(webp_bytes).decode('utf-8')
        return jsonify({'webp_base64': img_base64, 'status': 'ok'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
