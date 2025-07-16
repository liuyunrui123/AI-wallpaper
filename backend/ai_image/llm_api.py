
import requests
import urllib.parse
import os
import logging

# 经过实际测试的绘画提示词生成推荐模型 (按优先级排序)
RECOMMENDED_DRAWING_MODELS = [
    "gpt-4",        # 最佳选择 - 质量高、速度快、稳定
    "mistral",      # 备选1 - 质量稳定、描述丰富
    "llama-roblox", # 备选2 - 速度快、质量好
    "qwen-coder",   # 备选3 - 简洁实用
    "openai"        # 备选4 - 基础可用
]

def is_valid_english_prompt(text):
    """检查生成的文本是否为有效的英文提示词"""
    if not text or len(text.strip()) < 5:
        return False

    # 检查是否包含过多中文字符
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    if chinese_chars > len(text) * 0.1:  # 中文字符超过10%则认为无效
        return False

    # 检查是否包含明显的解释性文字
    invalid_phrases = ['以下是', '这是', 'here is', 'this is', '：', '。', '，']
    if any(phrase in text.lower() for phrase in invalid_phrases):
        return False

    return True

def generate_drawing_prompt(instruction, model="auto"):
    """
    生成英文AI绘画提示词

    Args:
        instruction: 完整的AI指令（可以是简单描述或详细指令）
        model: 使用的模型，auto会按推荐顺序尝试

    Returns:
        英文绘画提示词字符串
    """
    # 如果是简单描述（不包含"请根据"等指令关键词），自动添加指令前缀
    if not any(keyword in instruction for keyword in ["请根据", "生成专业", "只输出英文", "要求："]):
        instruction = f"将以下描述转换为专业的英文AI绘画提示词，只输出英文提示词，不要输出任何解释或其他内容：{instruction}"

    if model == "auto":
        # 按推荐顺序尝试模型
        for model_name in RECOMMENDED_DRAWING_MODELS:
            try:
                result = generate_text_with_model(instruction, model_name, "creative")
                if is_valid_english_prompt(result):
                    logging.info(f"使用模型: {model_name}")
                    return result.strip()
            except Exception as e:
                logging.warning(f"模型 {model_name} 失败: {e}")
                continue

        # 如果所有模型都失败，抛出异常
        raise Exception("所有推荐模型都无法生成有效的绘画提示词")
    else:
        # 使用指定模型
        result = generate_text_with_model(instruction, model, "creative")
        if not is_valid_english_prompt(result):
            raise Exception(f"模型 {model} 生成的结果不符合要求: {result}")
        return result.strip()

# 经过实际测试的可用模型列表 (2025-01-16 测试)
AVAILABLE_MODELS = {
    # 免费且稳定的模型
    "openai": "OpenAI GPT-4o Mini (免费推荐)",
    "gpt-4": "OpenAI GPT-4 (免费)",
    "mistral": "Mistral Small 3.1 24B (免费)",
    "llama-roblox": "Llama 3.1 8B FP8 (免费)",
    "phi": "Phi-4 Mini Instruct (免费)",
    "qwen-coder": "Qwen 2.5 Coder 32B (免费，适合编程)",
    "llamascout": "Llama 4 Scout 17B (免费)",

    # 高级模型 (目前可用)
    "deepseek": "DeepSeek V3 (高级)",
    "deepseek-reasoning": "DeepSeek R1 0528 (推理模型)",
    "openai-large": "OpenAI GPT-4.1 (高级)"
}

# 不可用的模型
UNAVAILABLE_MODELS = {
    "grok": "xAI Grok-3 Mini (需要付费)",
    "gemini-2.0-flash-thinking-exp": "Gemini 模型 (不支持)"
}

def get_recommended_models():
    """获取推荐的模型列表"""
    free_models = [
        "openai",      # GPT-4o Mini - 最稳定推荐
        "gpt-4",       # GPT-4 - 质量高
        "mistral",     # Mistral - 多语言支持好
        "qwen-coder",  # Qwen - 编程任务推荐
        "phi"          # Phi-4 - 轻量快速
    ]

    advanced_models = [
        "deepseek",           # DeepSeek V3 - 中文理解好
        "deepseek-reasoning", # DeepSeek R1 - 推理能力强
        "openai-large"        # GPT-4.1 - 最强性能
    ]

    return {
        "free": free_models,
        "advanced": advanced_models,
        "default": "openai"
    }

def test_model(model_name, test_prompt="Hello"):
    """测试单个模型是否可用"""
    encoded_prompt = urllib.parse.quote(test_prompt)
    url = f"https://text.pollinations.ai/{encoded_prompt}?model={model_name}"

    try:
        proxies = {'http': None, 'https': None}
        response = requests.get(url, proxies=proxies, timeout=10)

        if response.status_code == 200:
            return True, response.text[:50] + "..." if len(response.text) > 50 else response.text
        elif response.status_code == 402:
            return False, "需要付费"
        else:
            return False, f"状态码: {response.status_code}"
    except Exception as e:
        return False, f"错误: {str(e)[:50]}"

def choose_best_model(task_type="general"):
    """根据任务类型选择最佳模型"""
    recommendations = get_recommended_models()

    if task_type == "coding":
        return "qwen-coder"
    elif task_type == "reasoning":
        return "deepseek-reasoning"
    elif task_type == "chinese":
        return "deepseek"
    elif task_type == "creative":
        return "gpt-4"
    else:
        return recommendations["default"]

def generate_text_with_model(prompt, model="auto", task_type="general"):
    """生成文本，支持模型验证"""

    # 自动选择模型
    if model == "auto":
        model = choose_best_model(task_type)
        logging.info(f"自动选择模型: {model} (任务类型: {task_type})")

    # 检查模型是否在已知可用列表中
    if model not in AVAILABLE_MODELS:
        if model in UNAVAILABLE_MODELS:
            raise Exception(f"模型 {model} 不可用")
        else:
            raise Exception(f"未知模型 {model}")

    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://text.pollinations.ai/{encoded_prompt}?model={model}"

    try:
        # 禁用代理
        proxies = {
            'http': None,
            'https': None,
        }

        response = requests.get(url, proxies=proxies, timeout=30)

        if response.status_code == 402:
            raise Exception(f"模型 {model} 需要付费")

        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise Exception(f"请求失败: {e}")


def test_all_models():
    """测试所有模型的可用性"""
    print("正在测试模型可用性...\n")

    test_prompt = "Hello"
    all_models = {**AVAILABLE_MODELS, **UNAVAILABLE_MODELS}

    working_models = []
    failed_models = []

    for model_name, description in all_models.items():
        print(f"测试 {model_name} ({description})...", end=" ")
        is_working, result = test_model(model_name, test_prompt)

        if is_working:
            print("✓ 可用")
            print(f"  响应: {result}")
            working_models.append(model_name)
        else:
            print("✗ 不可用")
            print(f"  原因: {result}")
            failed_models.append(model_name)
        print()

    print(f"\n可用模型 ({len(working_models)}个):")
    for model in working_models:
        print(f"  - {model}")

    print(f"\n不可用模型 ({len(failed_models)}个):")
    for model in failed_models:
        print(f"  - {model}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 运行模型测试
        test_all_models()
    else:
        # 正常使用示例
        prompt = "介绍下自己"

        print("=== 智能模型选择测试 ===\n")

        # 测试自动模型选择
        test_cases = [
            ("介绍下自己", "auto", "general"),
            ("写一个Python函数计算斐波那契数列", "auto", "coding"),
            ("解释量子力学的基本原理", "auto", "reasoning"),
            ("写一首关于春天的诗", "auto", "creative")
        ]

        for test_prompt, model, task_type in test_cases:
            print(f"任务: {test_prompt}")
            output_text = generate_text_with_model(test_prompt, model, task_type)
            print(f"响应: {output_text[:100]}...")
            print("-" * 50)

        print("\n=== 绘画提示词生成 ===")
        test_description = "傍晚太阳落山的美丽景色"
        draw_output = generate_drawing_prompt(test_description)
        print(f"中文描述: {test_description}")
        print(f"英文提示词: {draw_output}")

        print("\n=== 推荐模型列表 ===")
        recommendations = get_recommended_models()
        print(f"免费模型: {', '.join(recommendations['free'])}")
        print(f"高级模型: {', '.join(recommendations['advanced'])}")
        print(f"默认模型: {recommendations['default']}")