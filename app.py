from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import base64
import json
import time
import io
import tempfile
import os

app = Flask(__name__)

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1080,1350')
    options.add_argument('--force-device-scale-factor=1')
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

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            tmp_path = f.name

        driver = get_driver()
        driver.get(f'file://{tmp_path}')
        driver.set_window_size(1080, 1350)

        driver.execute_script("""
            return new Promise((resolve) => {
                const img = document.querySelector('img');
                if (!img) return resolve();
                if (img.complete) return resolve();
                img.onload = resolve;
                img.onerror = resolve;
                setTimeout(resolve, 5000);
            });
        """)

        driver.execute_script("document.body.style.overflow='hidden'")
        time.sleep(2)

        png_bytes = driver.get_screenshot_as_png()
        driver.quit()
        os.unlink(tmp_path)

        img = Image.open(io.BytesIO(png_bytes))
        img = img.crop((0, 0, 1080, 1350))
        img = img.convert('RGB')
        jpeg_buffer = io.BytesIO()
        img.save(jpeg_buffer, format='JPEG', quality=92)
        jpeg_bytes = jpeg_buffer.getvalue()

        img_base64 = base64.b64encode(jpeg_bytes).decode('utf-8')
        return jsonify({'webp_base64': img_base64, 'status': 'ok'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
