from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import base64
import json
import os
import glob

app = Flask(__name__)

def find_chromium():
    patterns = [
        '/opt/render/.cache/ms-playwright/chromium-*/chrome-linux/chrome',
        '/opt/render/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
    ]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return None

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

        chromium_path = find_chromium()

        with sync_playwright() as p:
            launch_args = {
                'args': ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            }
            if chromium_path:
                launch_args['executable_path'] = chromium_path

            browser = p.chromium.launch(**launch_args)
            page = browser.new_page(viewport={'width': 700, 'height': 700})
            page.set_content(html, wait_until='networkidle')
            screenshot = page.screenshot(
                type='webp',
                quality=90,
                clip={'x': 0, 'y': 0, 'width': 700, 'height': 700}
            )
            browser.close()

        img_base64 = base64.b64encode(screenshot).decode('utf-8')
        return jsonify({'webp_base64': img_base64, 'status': 'ok'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
