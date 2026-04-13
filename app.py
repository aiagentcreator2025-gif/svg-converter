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
    options.add_argument('--window-size=700,700')
    options.add_argument('--allow-file-access-from-files')
    options.add_argument('--disable-web-security')
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

        # Write HTML to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            tmp_path = f.name

        driver = get_driver()
        driver.get(f'file://{tmp_path}')

        # Wait for image to load
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
        time.sleep(2)

        png_bytes = driver.get_screenshot_as_png()
        driver.quit()
        os.unlink(tmp_path)

        # Convert PNG → WEBP
        img = Image.open(io.BytesIO(png_bytes))
        img = img.crop((0, 0, 700, 700))
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
