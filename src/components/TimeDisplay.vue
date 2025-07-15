<template>
  <div class="time-display">
    <div class="time-container">
      <!-- 主时间显示 -->
      <div class="main-time">
        <div class="time-digits">
          <span class="hour">{{ formattedTime.hour }}</span>
          <span class="separator" :class="{ 'blink': showSeparator }">:</span>
          <span class="minute">{{ formattedTime.minute }}</span>
          <!-- <span class="separator" :class="{ 'blink': showSeparator }">:</span>
          <span class="second">{{ formattedTime.second }}</span> -->
        </div>
        <div class="period">{{ formattedTime.period }}</div>
      </div>
      
      <!-- 日期显示 -->
      <div class="date-info">
        <div class="weekday">{{ formattedDate.weekday }}</div>
        <div class="date-details">
          <span class="month-year">{{ formattedDate.monthYear }}</span>
          <span class="dot">•</span>
          <span class="date-main">{{ formattedDate.date }}</span>
        </div>
      </div>
      

    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted } from 'vue';

export default defineComponent({
  name: 'TimeDisplay',
  setup() {
    const currentTime = ref(new Date());
    const showSeparator = ref(true);
    let timeInterval: NodeJS.Timeout | null = null;
    let blinkInterval: NodeJS.Timeout | null = null;

    const formattedTime = ref({
      hour: '00',
      minute: '00',
      second: '00',
      period: '上午'
    });

    const formattedDate = ref({
      date: '1',
      weekday: 'Monday',
      monthYear: 'January 2024'
    });

    const updateTime = () => {
      const now = new Date();
      currentTime.value = now;
      
      // 格式化时间
      const hour24 = now.getHours();
      const hour12 = hour24 === 0 ? 12 : hour24 > 12 ? hour24 - 12 : hour24;
      const minute = now.getMinutes();
      const second = now.getSeconds();
      
      formattedTime.value = {
        hour: hour12.toString().padStart(2, '0'),
        minute: minute.toString().padStart(2, '0'),
        second: second.toString().padStart(2, '0'),
        period: hour24 >= 12 ? '下午' : '上午'
      };

      // 格式化日期 - 中文版本
      const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
      const months = ['1月', '2月', '3月', '4月', '5月', '6月',
                     '7月', '8月', '9月', '10月', '11月', '12月'];
      
      formattedDate.value = {
        date: now.getDate().toString() + '日',
        weekday: weekdays[now.getDay()],
        monthYear: `${now.getFullYear()}年 ${months[now.getMonth()]}`
      };
    };

    const startBlinking = () => {
      blinkInterval = setInterval(() => {
        showSeparator.value = !showSeparator.value;
      }, 1000);
    };

    onMounted(() => {
      updateTime();
      timeInterval = setInterval(updateTime, 1000);
      startBlinking();
    });

    onUnmounted(() => {
      if (timeInterval) {
        clearInterval(timeInterval);
      }
      if (blinkInterval) {
        clearInterval(blinkInterval);
      }
    });

    return {
      formattedTime,
      formattedDate,
      showSeparator
    };
  }
});
</script>

<style scoped>
.time-display {
  position: fixed;
  right: 40px;
  top: 340px;
  z-index: 15;
  user-select: none;
}

.time-container {
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(10px);
  border-radius: 14px;
  padding: 18px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
  min-width: 220px;
}



.main-time {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
}

.time-digits {
  display: flex;
  align-items: baseline;
  font-family: 'Segoe UI', 'Arial', monospace;
  font-weight: 300;
  color: #ffffff;
}

.hour, .minute, .second {
  font-size: 36px;
  line-height: 1;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  transition: color 0.2s ease;
}

.hour:hover, .minute:hover, .second:hover {
  color: #64b5f6;
}

.separator {
  font-size: 36px;
  color: #64b5f6;
  margin: 0 4px;
  transition: opacity 0.2s ease;
}

.separator.blink {
  opacity: 0.3;
}

.period {
  font-size: 20px;
  color: #b0bec5;
  font-weight: 500;
  margin-left: 8px;
  align-self: flex-start;
  margin-top: 8px;
}

.date-info {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 16px;
  text-align: left;
}

.date-main {
  font-weight: 400;
}

.date-details {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  color: #b0bec5;
}

.weekday {
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 8px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.dot {
  color: #64b5f6;
  font-weight: bold;
}

.month-year {
  font-weight: 400;
}



/* 响应式设计 */
@media (max-width: 768px) {
  .time-display {
    right: 20px;
    top: 300px;
  }

  .time-container {
    padding: 20px 24px;
  }

  .hour, .minute, .second, .separator {
    font-size: 28px;
  }

  .weekday {
    font-size: 20px;
  }

  .period {
    font-size: 16px;
  }
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  .time-container {
    background: rgba(20, 20, 20, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.05);
  }
}
</style>
