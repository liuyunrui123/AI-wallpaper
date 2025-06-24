# from flask import Flask, jsonify
# import requests

# app = Flask(__name__)

# API_KEY = 'your_api_key'  # Replace with your actual API key
# BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'

# @app.route('/weather/<city>', methods=['GET'])
# def get_weather(city):
#     params = {
#         'q': city,
#         'appid': API_KEY,
#         'units': 'metric'
#     }
#     response = requests.get(BASE_URL, params=params)
    
#     if response.status_code == 200:
#         data = response.json()
#         weather_info = {
#             'city': data['name'],
#             'temperature': data['main']['temp'],
#             'description': data['weather'][0]['description'],
#             'humidity': data['main']['humidity'],
#             'wind_speed': data['wind']['speed']
#         }
#         return jsonify(weather_info), 200
#     else:
#         return jsonify({'error': 'City not found'}), 404

# if __name__ == '__main__':
#     app.run(debug=True)


from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/weather', methods=['GET'])
def get_weather():
    # 假数据，后续可替换为高德天气API返回的数据
    fake_weather = {
        "city": "北京",
        "weather": "晴",
        "temperature": "28°C",
        "humidity": "40%",
        "wind": "西南风 3级",
        "update_time": "2025-06-14 10:00:00"
    }
    return jsonify(fake_weather)

if __name__ == '__main__':
    app.run(port=5001)
