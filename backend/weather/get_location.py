import requests

def get_location_by_ip(ip='', timeout=5):
    url = 'https://api.vore.top/api/IPdata?ip=' + ip
    try:
        resp = requests.get(url, timeout=timeout)
        data = resp.json()
        if data.get('code') == 200:
            ipdata = data.get('ipdata', {})
            # info1: 省，info2: 市/区，info3: 区（有些直辖市 info3 为空）
            province = ipdata.get('info1', '')
            city = ipdata.get('info2', '')
            county = ipdata.get('info3', '')
            # 兼容直辖市，保证三个字段都返回
            if not county:
                county = city
                city = province.replace('省', '').replace('市', '')
            return {
                'province': province,
                'city': city,
                'county': county
            }
        else:
            return {'province': '', 'city': '', 'county': '', 'error': data.get('msg', '接口异常')}
    except Exception as e:
        return {'province': '', 'city': '', 'county': '', 'error': str(e)}

# 示例用法
if __name__ == "__main__":

    # 根据IP获取省市区信息的功能
    location_info = get_location_by_ip(ip='121.8.215.106')  # 留空则自动获取公网IP
    if 'error' in location_info:
        print("获取省市区信息失败:", location_info['error'])
    else:
        print("省市区信息:", location_info)