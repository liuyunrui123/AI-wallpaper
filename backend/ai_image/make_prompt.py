import random
from datetime import datetime

# 简单按季节模拟日落时间（实际应用需接入天文API）
def get_sunset_hour():
    month = datetime.now().month
    if 3 <= month <= 5:   # 春季：约18:30-19:00日落
        return 18 + 0.5  # 18:30
    elif 6 <= month <= 8: # 夏季：约19:00-19:30日落
        return 19
    elif 9 <= month <= 11: # 秋季：约17:30-18:00日落
        return 17 + 0.75 # 17:45
    else:                # 冬季：约16:30-17:00日落
        return 16 + 0.75 # 16:45

def get_time_mood():
    # 获取当前时间的小时数,带小数点
    current_hour = datetime.now().hour + datetime.now().minute / 60.0  # 转换为小时带小数点
    sunset_hour = get_sunset_hour()
    if 3 <= current_hour < 6:
        return "dawn"
    elif 6 <= current_hour < 9:
        return "early_morning"
    elif 9 <= current_hour < 12:
        return "late_morning"
    elif 12 <= current_hour < 15:
        return "early_afternoon"
    elif 15 <= current_hour < sunset_hour - 1:
        return "late_afternoon"
    elif sunset_hour - 1 <= current_hour < sunset_hour:  # 日落前1小时
        return "sunset_start"
    elif sunset_hour <= current_hour < sunset_hour + 0.5:  # 日落时刻±30分钟
        return "sunset_peak"
    elif sunset_hour + 0.5 <= current_hour < sunset_hour + 1:  # 日落后1小时内
        return "sunset_end"
    elif sunset_hour + 1 <= current_hour < 24:
        return "night"
    else:
        return "midnight"

def get_weather_key(weather: str) -> str:
    if '雨' in weather:
        return '雨'
    elif '云' in weather:
        return '多云'
    elif '雪' in weather:
        return '雪'
    elif '雾' in weather:
        return '雾'
    elif '阴' in weather:
        return '阴'
    else:
        return '晴'

def make_draw_prompt(time_mood: str, weather_key: str) -> str:
    base_prompts = "4K wallpaper, beautiful landscape"
    # 动漫画风
    anime_style_prompts = ",studio ghibli-inspired magical realism"
    # 自然场景提示词字典
    scene_prompts_dict = {
        # 室内场景
        'indoor_library': "classic library setting, wooden bookshelves, reading nooks",
        'indoor_cafe': "cozy café interior, rustic furniture, warm ambiance",
        'indoor_museum': "grand museum hall, art displays, high ceilings",
        'indoor': "cozy indoor setting, warm lights, comfortable",
        # 山地景观
        'mountain_valley': "deep mountain valley, rugged cliffs, untouched wilderness",
        'mountain_path': "winding mountain trail, rocky terrain, alpine vegetation",
        'volcano': "dormant volcano, crater formation, mineral-rich slopes",
        'mountain': "majestic mountains, serene",
        # 水域景观
        'river': "meandering river, smooth stones, gentle current",
        'waterfall': "cascading waterfall, misty basin, moss-covered rocks",
        'marsh': "tranquil marshland, reeds, still waters",
        'lake': "calm lake, reflections, peaceful water",
        # 森林景观
        'bamboo_forest': "dense bamboo grove, tall stalks, filtered light",
        'autumn_forest': "deciduous forest, multicolored foliage, fallen leaves",
        'rainforest': "tropical rainforest, dense canopy, vibrant vegetation",
        'forest': "lush green forest",
        # 沙漠景观
        'sand_dunes': "undulating sand dunes, smooth curves, wind patterns",
        'canyon': "deep canyon, stratified rock layers, narrow passages",
        'oasis': "desert oasis, palm cluster, still pool",
        'desert': "vast desert, golden sands",
        # 海洋景观
        'coral_reef': "vibrant coral reef, marine life, clear waters",
        'cliff_coast': "dramatic coastal cliffs, eroded formations, sea spray",
        'lagoon': "shallow lagoon, turquoise waters, sandy bottom",
        'ocean': "vast ocean, gentle waves, horizon, peaceful",
        # 乡村景观
        'vineyard': "orderly vineyard, grapevines, rolling hills",
        'pasture': "grazing pasture, wooden fences, grassy expanse",
        'rural': "peaceful rural landscape, fields, farmhouses",
        # 草原景观
        'grassland': "vast green grasslands, cattle and sheep in the distance, sparse trees",
        'savanna': "open savanna, scattered acacia trees, golden grasses",
        'tundra': "arctic tundra, low vegetation, permafrost patterns",
        # 道路景观
        'forest_path': "dirt path through dense woods, overgrown edges",
        'mountain_pass': "high altitude mountain passage, rocky outcrops",
        'coastal_road': "winding road along seaside cliffs, ocean views",
        # 二次元动漫画风
        'enchanted_sakura_garden': "stone lanterns, cobbled paths, petals floating on streams" + anime_style_prompts,
        'celestial_observatory': "starry dome, glowing astronomical instruments, floating golden orrery" + anime_style_prompts,
        'floating_islands': "hovering landmasses, waterfalls into mist, vine bridges" + anime_style_prompts,
        'magical_academy': "gothic spires with runes, floating books, stained glass patterns" + anime_style_prompts,
        'crystal_caverns': "bioluminescent crystals, underground pools, glowing formations" + anime_style_prompts,
        'autumn_samurai_village': "crimson maple leaves, thatched roofs, paper lanterns" + anime_style_prompts,
        'steampunk_harbor': "brass airships, clockwork cranes, steam in golden sunset" + anime_style_prompts,
        'enchanted_tea_house': "floating structure, lotus flowers, steaming teacups" + anime_style_prompts,
        'starlight_festival': "floating paper lanterns, fireworks on water, festival stalls" + anime_style_prompts,
        'fairy_forest': "glowing mushrooms, ancient trees, treehouse villages" + anime_style_prompts,
        'underwater_temple': "coral pillars, sunlight beams, tropical fish through arches" + anime_style_prompts,
        'moonlit_bamboo_grove': "silver light through bamboo, fox spirits, floating leaves" + anime_style_prompts,
        'cloud_palace': "marble on clouds, rainbow bridges, dragons around jade pillars" + anime_style_prompts,
        'winter_oni_village': "snow houses with demon masks, hot springs, orange lights in twilight" + anime_style_prompts,
    }
    # 从字典中使用随机数随机一个场景提示词
    # 随机获取一个key
    random_scene_key = random.choice(list(scene_prompts_dict.keys()))
    # 根据key获取一个值
    random_scene_prompts = scene_prompts_dict[random_scene_key]

    # 全面优化的特殊时间+天气组合
    combo_prompts = {
        # 夜晚相关
        ('night', '雨'): "rainy night, wet street, city lights reflecting on puddles, umbrellas, no stars, no moon, dark sky, gentle rain, misty, moody atmosphere",
        ('night', '雪'): "snowy night, snow falling, quiet street, soft warm lights from windows, no stars, no moon, snow covered ground, peaceful",
        ('night', '雾'): "foggy night, street lamps glowing in mist, low visibility, mysterious, no stars, no moon",
        ('night', '阴'): "overcast night, city lights, muted colors, no stars, no moon, calm",
        ('night', '多云'): "cloudy night, clouds covering the sky, faint city lights, no stars, no moon, tranquil",
        # 午夜
        ('midnight', '雨'): "midnight rain, empty street, wet asphalt, reflections, no stars, no moon, dark, gentle rain",
        ('midnight', '雪'): "midnight snow, quiet, snow covered, soft light, no stars, no moon, peaceful",
        ('midnight', '雾'): "midnight fog, mysterious, low visibility, street lights in mist, no stars, no moon",
        ('midnight', '阴'): "overcast midnight, muted colors, no stars, no moon, calm",
        ('midnight', '多云'): "cloudy midnight, clouds covering the sky, faint city lights, no stars, no moon, tranquil",
        # 傍晚日落
        ('sunset_start', '雨'): "rainy sunset, sun low behind clouds, wet ground, cozy lights, gentle rain, umbrellas",
        ('sunset_peak', '雨'): "rainy sunset, sun touching horizon behind rain clouds, wet ground, golden rain, umbrellas",
        ('sunset_end', '雨'): "rainy twilight, afterglow through rain, wet ground, street lights, gentle rain, umbrellas",
        ('sunset_start', '雪'): "snowy sunset, snowflakes in golden light, warm windows, winter scene",
        ('sunset_peak', '雪'): "snowy sunset, sun on horizon, snowflakes glowing, winter scene",
        ('sunset_end', '雪'): "snowy twilight, afterglow on snow, peaceful, winter scene",
        ('sunset_start', '雾'): "foggy sunset, sun low in mist, soft colors, mysterious",
        ('sunset_peak', '雾'): "foggy sunset, sun on horizon in mist, diffused light, mysterious",
        ('sunset_end', '雾'): "foggy twilight, afterglow in mist, soft colors, mysterious",
        ('sunset_start', '阴'): "overcast sunset, muted sun, calm",
        ('sunset_peak', '阴'): "overcast sunset, sun on horizon behind clouds, calm",
        ('sunset_end', '阴'): "overcast twilight, afterglow behind clouds, calm",
        ('sunset_start', '多云'): "cloudy sunset, dramatic clouds at golden hour, soft light",
        ('sunset_peak', '多云'): "cloudy sunset, sun on horizon with clouds, dramatic sky",
        ('sunset_end', '多云'): "cloudy twilight, afterglow with clouds, soft light",
        # 清晨
        ('dawn', '雨'): "rainy dawn, wet ground, soft light, gentle rain, misty, peaceful",
        ('dawn', '雪'): "snowy dawn, snow covered landscape, first light, quiet",
        ('dawn', '雾'): "foggy dawn, low visibility, mysterious, soft sunrise",
        ('dawn', '阴'): "overcast dawn, muted sunrise, calm",
        ('dawn', '多云'): "cloudy dawn, clouds with first light, tranquil",
        # 白天（上午/下午）
        ('early_morning', '雨'): "rainy morning, wet streets, umbrellas, gentle rain, fresh air",
        ('late_morning', '雨'): "rainy late morning, lively city, wet ground, gentle rain",
        ('early_afternoon', '雨'): "rainy afternoon, wet city, gentle rain, people with umbrellas",
        ('late_afternoon', '雨'): "rainy late afternoon, golden hour light through rain, wet ground",
        ('early_morning', '雪'): "snowy morning, fresh snow, soft sunlight, peaceful",
        ('late_morning', '雪'): "snowy late morning, bright snow, lively",
        ('early_afternoon', '雪'): "snowy afternoon, winter scene, blue sky",
        ('late_afternoon', '雪'): "snowy late afternoon, golden hour on snow",
        ('early_morning', '雾'): "foggy morning, soft sunlight through mist, mysterious",
        ('late_morning', '雾'): "foggy late morning, diffused light, low visibility",
        ('early_afternoon', '雾'): "foggy afternoon, soft daylight, mysterious",
        ('late_afternoon', '雾'): "foggy late afternoon, golden hour in mist",
        ('early_morning', '阴'): "overcast morning, muted colors, calm",
        ('late_morning', '阴'): "overcast late morning, soft light, calm",
        ('early_afternoon', '阴'): "overcast afternoon, muted colors, calm",
        ('late_afternoon', '阴'): "overcast late afternoon, golden hour, calm",
        ('early_morning', '多云'): "cloudy morning, soft clouds, fresh air",
        ('late_morning', '多云'): "cloudy late morning, lively, clear sky with clouds",
        ('early_afternoon', '多云'): "cloudy afternoon, blue sky with clouds",
        ('late_afternoon', '多云'): "cloudy late afternoon, golden hour with clouds",
    }
    if (time_mood, weather_key) in combo_prompts:
        out_prompts = f"{random_scene_prompts}, {combo_prompts[(time_mood, weather_key)]}, {base_prompts}"
        return out_prompts
    # 默认拼接
    sunset_hour = get_sunset_hour()
    time_prompts = {
        'dawn': "dawn, first light, cool sky, gentle sunrise, calm nature",
        'early_morning': "early morning, fresh air, soft sunlight, dew, peaceful",
        'late_morning': "late morning, bright sun, lively, clear sky, energetic",
        'early_afternoon': "early afternoon, vibrant daylight, blue sky, active",
        'late_afternoon': "late afternoon, warm sunlight, long shadows, golden hour",
        # 动态日落时段
        'sunset_start': f"pre-sunset, sun low at {int(sunset_hour-1)}:00, golden horizontal light",  # 日落前1小时
        'sunset_peak': "sun touching horizon, fiery sky, maximum color saturation",                 # 日落时刻±30分钟
        'sunset_end': "sun just disappeared, afterglow transitioning to twilight",                # 日落后1.5小时内
        'night': "night, moonlight, stars, deep blue sky, quiet scene",
        'midnight': "midnight, dark sky, starry, serene, calm night"
    }
    weather_modifiers = {
        '晴': "bright sunshine, clear weather",
        '雨': "gentle rain, water drops, misty",
        '多云': "soft clouds, diffused light",
        '阴': "overcast sky, muted colors",
        '雾': "foggy, low visibility, mysterious",
        '雪': "snow flakes, winter scene"
    }
    out_prompts = f"{random_scene_prompts}, {time_prompts[time_mood]}, {weather_modifiers[weather_key]}, {base_prompts}"
    return out_prompts