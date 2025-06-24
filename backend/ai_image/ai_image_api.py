from flask import Flask, request, jsonify
import urllib.parse

app = Flask(__name__)

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    # 对prompt进行URL编码
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f'https://image.pollinations.ai/prompt/{encoded_prompt}'
    return jsonify({'image_url': image_url})

if __name__ == '__main__':
    app.run(debug=True)