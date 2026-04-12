from flask import Flask, request, jsonify
import cairosvg
import base64

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.get_json(force=True)
        svg_raw = data.get('svg_raw', '')
        
        if not svg_raw:
            return jsonify({'error': 'No SVG provided'}), 400
        
        png_bytes = cairosvg.svg2png(
            bytestring=svg_raw.encode('utf-8'),
            output_width=700,
            output_height=700
        )
        
        img_base64 = base64.b64encode(png_bytes).decode('utf-8')
        
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
