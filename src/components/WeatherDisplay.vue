<template>
  <div class="weather-display">
    <div class="weather-card">
      <!-- 天气主要信息 -->
      <div class="weather-main">
        <div class="weather-icon">{{ getWeatherIcon(weather) }}</div>
        <div class="weather-primary">
          <div class="weather-condition">{{ weather }}</div>
          <div class="temperature-display">{{ temperature }}</div>
        </div>
      </div>
      
      <!-- 详细信息 -->
      <div class="weather-details">
        <div class="detail-item">
          <div class="detail-icon">💧</div>
          <div class="detail-content">
            <span class="detail-label">湿度</span>
            <span class="detail-value">{{ humidity }}</span>
          </div>
        </div>
        <div class="detail-item">
          <div class="detail-icon">💨</div>
          <div class="detail-content">
            <span class="detail-label">风力</span>
            <span class="detail-value">{{ windPower }}</span>
          </div>
        </div>
      </div>
      
      <!-- 位置信息 -->
      <div class="location-info">
        <div class="location-icon">📍</div>
        <div class="location-text">{{ province }}{{ city }}{{ county }}</div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'WeatherDisplay',
  props: {
    weather: {
      type: String,
      default: ''
    },
    temperature: {
      type: String,
      default: ''
    },
    humidity: {
      type: String,
      default: ''
    },
    windPower: {
      type: String,
      default: ''
    },
    province: {
      type: String,
      default: ''
    },
    city: {
      type: String,
      default: ''
    },
    county: {
      type: String,
      default: ''
    }
  },
  methods: {
    getWeatherIcon(weather: string): string {
      const weatherIconMap: { [key: string]: string } = {
        '晴': '☀️',
        '阴': '☁️',
        '雾': '🌫️',
        '雪': '❄️',
        '多云': '🌤️',
        '雨': '🌧️'
      };

      // 如果找不到对应的图标，返回默认的多云图标
      return weatherIconMap[weather] || '🌤️';
    }
  }
});
</script>

<style scoped>
.weather-display {
  position: fixed;
  right: 40px;
  top: 40px;
  z-index: 10;
  user-select: none;
}

.weather-card {
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(10px);
  border-radius: 14px;
  padding: 18px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
  min-width: 220px;
  color: #ffffff;
  user-select: text;
  transition: all 0.3s ease;
}

.weather-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

.weather-main {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.weather-icon {
  font-size: 48px;
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3));
}

.weather-primary {
  flex: 1;
}

.weather-condition {
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 4px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.temperature-display {
  font-size: 32px;
  font-weight: 300;
  color: #64b5f6;
  font-family: 'Segoe UI', 'Arial', monospace;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  transition: color 0.2s ease;
}

.temperature-display:hover {
  color: #90caf9;
}

.weather-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-item:hover .detail-value {
  color: #64b5f6;
  transition: color 0.2s ease;
}

.detail-icon {
  font-size: 20px;
  width: 24px;
  text-align: center;
  filter: drop-shadow(0 1px 4px rgba(0, 0, 0, 0.3));
}

.detail-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 1;
}

.detail-label {
  font-size: 16px;
  color: #b0bec5;
  font-weight: 400;
}

.detail-value {
  font-size: 16px;
  color: #ffffff;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  transition: color 0.2s ease;
}

.location-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.location-icon {
  font-size: 16px;
  filter: drop-shadow(0 1px 4px rgba(0, 0, 0, 0.3));
}

.location-text {
  font-size: 14px;
  color: #b0bec5;
  font-weight: 400;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .weather-display {
    right: 20px;
    top: 20px;
  }

  .weather-card {
    min-width: 220px;
    padding: 16px 20px;
  }

  .weather-icon {
    font-size: 40px;
  }

  .weather-condition {
    font-size: 20px;
  }

  .temperature-display {
    font-size: 28px;
  }

  .detail-icon {
    font-size: 18px;
  }

  .detail-label, .detail-value {
    font-size: 14px;
  }

  .location-text {
    font-size: 12px;
  }
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  .weather-card {
    background: rgba(20, 20, 20, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.05);
  }
  
  .weather-card:hover {
    background: rgba(25, 25, 25, 0.7);
  }
}
</style>
