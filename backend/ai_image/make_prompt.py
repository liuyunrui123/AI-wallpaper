import random
import logging
from datetime import datetime
try:
    from ai_image.llm_api import generate_drawing_prompt
except ImportError:
    from llm_api import generate_drawing_prompt

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

def make_draw_prompt_rule_based(time_mood: str, weather_key: str) -> str:
    """基于规则的绘画提示词生成函数（作为降级方案）"""
    base_prompts = "4K wallpaper, beautiful landscape"
    # 动漫画风
    anime_style_prompts = ",studio ghibli-inspired magical realism"
    # 自然场景提示词字典
    scene_prompts_dict = {
        # 室内场景
        'indoor_library': "classic library setting, wooden bookshelves, reading nooks",
        'indoor_cafe': "cozy café interior, rustic furniture, warm ambiance",
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
        'underwater_temple': "coral pillars, tropical fish through arches" + anime_style_prompts,
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

def get_current_time_info() -> dict:
    """获取当前时间信息"""
    now = datetime.now()
    return {
        'month': now.month,
        'day': now.day,
        'hour': now.hour,
        'minute': now.minute
    }

def create_ai_prompt_for_drawing(weather_key: str) -> str:
    """为AI生成创建绘画提示词的指令"""
    time_info = get_current_time_info()

    weather_descriptions = {
        '晴': "晴天",
        '雨': "雨天",
        '多云': "多云",
        '阴': "阴天",
        '雾': "雾天",
        '雪': "雪天"
    }

    weather_desc = weather_descriptions.get(weather_key, "晴天")

    # 随机选择场景类型
    scene_types = [
        # 自然风景
        "山川景观（高山、峡谷、山谷）",
        "河流景观（河流、瀑布、溪流）",
        "海洋景观（海岸、海滩、悬崖）",
        "森林景观（密林、树林、竹林）",
        "草原景观（草地、平原、牧场）",
        "湖泊景观（湖泊、池塘、湿地）",
        "沙漠景观（沙丘、绿洲、戈壁）",
        "田园景观（农田、乡村、花园）",

        # 吉卜力风格二次元场景
        "吉卜力风格樱花庭院（传统石灯笼、青苔石径、花瓣轻舞飞扬）",
        "吉卜力风格天空之城（漂浮岛屿、古老机械、云海环绕）",
        "吉卜力风格魔法森林（参天古树、神秘光斑、精灵踪迹）",
        "吉卜力风格乡村小镇（欧式小屋、石板路、温暖灯光）",
        "吉卜力风格海边悬崖（草原小屋、海风吹拂、无垠海景）",
        "吉卜力风格山谷农场（梯田、风车、田园诗意）",
        "吉卜力风格秋日枫林（红叶满山、小径蜿蜒、诗意氛围）",
        "吉卜力风格湖心小岛（宁静湖面、小木屋、倒影如镜）",
        "吉卜力风格花海草原（五彩花田、微风轻抚、远山如黛）",
        "吉卜力风格古老城堡（藤蔓缠绕、时光沉淀、神秘优雅）",
        "吉卜力风格竹林小径（翠竹摇曳、光影斑驳、禅意悠远）",
        "吉卜力风格云端花园（天空花园、彩云飘渺、梦幻仙境）"
    ]

    selected_scene = random.choice(scene_types)

    # 判断是否为吉卜力风格场景
    is_ghibli_scene = "吉卜力" in selected_scene

    # 根据时间判断光照状态
    hour = time_info['hour']
    month = time_info['month']

    # 不同季节的日出日落时间
    if 6 <= month <= 8:  # 夏季
        sunrise_hour, sunset_hour = 5, 19
    elif 3 <= month <= 5 or 9 <= month <= 11:  # 春秋季
        sunrise_hour, sunset_hour = 6, 18
    else:  # 冬季
        sunrise_hour, sunset_hour = 7, 17

    # 确定光照状态和约束
    if hour < sunrise_hour or hour > sunset_hour + 1:
        lighting_constraint = f"""严格时间约束：现在是{hour}点，属于夜晚时间！
- 绝对禁止词汇：sunlight, sun, sunny, solar, sunshine, daylight, bright light
- 必须使用词汇：moonlight, starlight, artificial lighting, night lighting, dim lighting
- 如果违反此约束，生成结果将被视为错误"""
    elif sunrise_hour <= hour <= sunrise_hour + 1:
        lighting_constraint = f"时间约束：现在是{hour}点，属于日出时分，可以有sunrise、dawn light、early morning sun等初升阳光"
    elif sunset_hour - 1 <= hour <= sunset_hour:
        lighting_constraint = f"时间约束：现在是{hour}点，属于日落时分，可以有sunset、dusk light、golden hour等夕阳光线"
    else:
        lighting_constraint = f"时间约束：现在是{hour}点，属于白天时间，可以有sunlight、bright daylight等阳光"

    prompt = f"""请根据以下信息生成专业的英文AI绘画提示词，只输出英文提示词，不要输出任何解释：

当前时间：{time_info['month']}月{time_info['day']}日{time_info['hour']}点{time_info['minute']}分
当前天气：{weather_desc}
场景类型：{selected_scene}

{lighting_constraint}

要求：
1. 根据当前月份判断季节特征
2. 根据当前时间判断准确的光照情况（考虑季节影响的日出日落时间）
3. 根据天气情况调整光照描述（如雨天不能有强烈阳光，阴天光线暗淡等）
4. 生成指定场景类型的绘画提示词
5. 包含场景特色、光照、色调、氛围等关键词
6. 确保场景描述与时间天气逻辑一致
{"7. 如果是吉卜力风格场景，请添加studio ghibli style, anime style, magical realism, soft lighting, detailed animation等关键词" if is_ghibli_scene else ""}
{"8. 吉卜力场景应该包含温暖色调、柔和光线、细腻质感、诗意氛围等元素" if is_ghibli_scene else ""}"""

    return prompt

def make_draw_prompt(time_mood: str, weather_key: str) -> str:
    """
    生成绘画提示词的主函数
    优先使用AI生成（基于真实时间），失败时降级到基于规则的生成

    Args:
        time_mood: 时间情绪 (保留兼容性，但AI生成时会忽略)
        weather_key: 天气关键词 (晴, 雨, 多云, etc.)

    Returns:
        英文绘画提示词
    """
    # 创建AI生成指令
    ai_instruction = create_ai_prompt_for_drawing(weather_key)

    try:
        # 优先尝试AI生成（让AI自己判断时间和天气）
        ai_prompt = generate_drawing_prompt(ai_instruction, model="auto")
        time_info = get_current_time_info()
        logging.info(f"AI生成成功: {time_info['month']}月{time_info['day']}日{time_info['hour']}点{weather_key}天 -> {ai_prompt[:50]}...")
        return ai_prompt
    except Exception as e:
        # AI生成失败，降级到基于规则的生成
        logging.warning(f"AI生成失败: {e}")
        logging.info("降级到规则生成")
        rule_based_prompt = make_draw_prompt_rule_based(time_mood, weather_key)
        logging.info(f"规则生成完成: {rule_based_prompt[:50]}...")
        return rule_based_prompt