from flask import Flask, request, jsonify, send_file
from playwright.sync_api import sync_playwright
import base64
import json
import io

app = Flask(__name__)

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

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 700, 'height': 700})
            page.set_content(html, wait_until='networkidle')
            screenshot = page.screenshot(
                type='webp',
                quality=90,
                clip={'x': 0, 'y': 0, 'width': 700, 'height': 700}
            )
            browser.close()

        img_base64 = base64.b64encode(screenshot).decode('utf-8')

        return jsonify({
            'webp_base64': img_base64,
            'status': 'ok'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
