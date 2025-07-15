import requests

def get_location_by_iqiyi_api(ip='', timeout=3):
    """
    通过爱奇艺API获取IP位置信息
    """
    url = f'https://mesh.if.iqiyi.com/aid/ip/info?version=1.1.1&ip={ip}'
    try:
        resp = requests.get(url, timeout=timeout)
        data = resp.json()
        if data.get('code') == '0' and data.get('msg') == 'success':
            location_data = data.get('data', {})
            province = location_data.get('provinceCN', '')
            city = location_data.get('cityCN', '')
            county = location_data.get('countyCN', '')

            return {
                'province': province,
                'city': city,
                'county': county
            }
        else:
            return {'province': '', 'city': '', 'county': '', 'error': data.get('msg', '接口异常')}
    except Exception as e:
        return {'province': '', 'city': '', 'county': '', 'error': str(e)}

def get_location_by_vore_api(ip='', timeout=3):
    """
    通过vore API获取IP位置信息（原有方法）
    """
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

def get_location_by_ip(ip='', timeout=5):
    """
    获取IP位置信息，优先使用爱奇艺API，失败时使用备用API
    """
    # 首先尝试使用爱奇艺API
    result = get_location_by_iqiyi_api(ip, timeout)

    # 如果爱奇艺API失败，使用原有的vore API作为备用
    if 'error' in result:
        print(f"爱奇艺API获取位置失败: {result['error']}, 尝试使用备用API")
        result = get_location_by_vore_api(ip, timeout)
        if 'error' in result:
            print(f"备用API也失败: {result['error']}")

    return result

# 示例用法
if __name__ == "__main__":
    # 测试IP地址
    # test_ip = '121.8.215.106' # 广州市增城区
    test_ip = '111.199.188.85' # 北京昌平

    print("=== 测试爱奇艺API ===")
    iqiyi_result = get_location_by_iqiyi_api(ip=test_ip)
    if 'error' in iqiyi_result:
        print("爱奇艺API获取失败:", iqiyi_result['error'])
    else:
        print("爱奇艺API结果:", iqiyi_result)

    print("\n=== 测试备用API ===")
    vore_result = get_location_by_vore_api(ip=test_ip)
    if 'error' in vore_result:
        print("备用API获取失败:", vore_result['error'])
    else:
        print("备用API结果:", vore_result)

    print("\n=== 测试主函数（自动选择最佳API） ===")
    location_info = get_location_by_ip(ip=test_ip)  # 留空则自动获取公网IP
    if 'error' in location_info:
        print("获取省市区信息失败:", location_info['error'])
    else:
        print("最终结果:", location_info)