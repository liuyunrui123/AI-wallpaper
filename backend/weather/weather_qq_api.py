import requests
from flask import jsonify, request

def get_qq_weather(province, city, county):
    url = "https://wis.qq.com/weather/common"
    params = {
        "source": "pc",
        "weather_type": "observe",
        "province": province,
        "city": city,
        "county": county
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data.get("status") == 200:
            observe = data["data"].get("observe", {})
            if observe.get("weather") == "" and observe.get("update_time") == "":
                return {"error": "天气信息获取失败"}
            return {
                "weather": observe.get("weather", "未知"),
                "temperature": observe.get("degree", "--") + "°C",
                "humidity": observe.get("humidity", "--"),
                "wind_direction": observe.get("wind_direction_name", "--"),
                "wind_power": observe.get("wind_power", "--"),
                "update_time": observe.get("update_time", "--"),
                "raw": observe
            }
        else:
            return {"error": data.get("message", "接口异常")}
    except Exception as e:
        return {"error": str(e)}



if __name__ == "__main__":
    # 测试获取天气信息
    ret = get_qq_weather(province="四川", city="成都", county="成华区")
    print(ret)

    # 测试其他城市
    ret = get_qq_weather(province="广东", city="广州", county="")
    print(ret)
    ret = get_qq_weather(province="北京", city="北京", county="昌平区")
    print(ret)

# Flask 路由示例
# from flask import Blueprint
# qq_weather_bp = Blueprint('qq_weather', __name__)

# @qq_weather_bp.route('/api/qq-weather', methods=['GET'])
# def qq_weather_api():
#     province = request.args.get('province', '四川')
#     city = request.args.get('city', '成都')
#     county = request.args.get('county', '成华区')
#     result = get_qq_weather(province, city, county)
#     return jsonify(result)

