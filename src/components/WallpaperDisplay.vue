<template>
  <div class="wallpaper-display">
    <img
      :src="wallpaperUrl"
      alt="Wallpaper"
      class="wallpaper-image"
      :class="{ 'fade-in': imgLoaded }"
      @load="onImgLoad"
      @error="onImgError"
      key="wallpaper-{{wallpaperUrl}}"
      v-show="imgLoaded"
    />
    <div v-if="showLoading && !imgLoaded" class="img-loading">
      <div class="spinner"></div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, watch } from 'vue';

export default defineComponent({
  name: 'WallpaperDisplay',
  props: {
    wallpaperUrl: {
      type: String,
      required: true
    },
    title: {
      type: String,
      default: 'Beautiful Wallpaper'
    },
    description: {
      type: String,
      default: 'A stunning view to brighten your day.'
    },
    showLoading: {
      type: Boolean,
      default: false
    }
  },
  setup(props) {
    const imgLoaded = ref(false);
    const onImgLoad = () => {
      imgLoaded.value = true;
    };
    const onImgError = () => {
      imgLoaded.value = false;
    };
    watch(() => props.wallpaperUrl, () => {
      imgLoaded.value = false;
    });
    return { imgLoaded, onImgLoad, onImgError, showLoading: props.showLoading };
  }
});
</script>

<style scoped>
.wallpaper-display {
  position: fixed;
  left: 0;
  top: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  z-index: 1;
}

.wallpaper-image {
  width: 100vw;
  height: 100vh;
  object-fit: cover;
  object-position: center;
  display: block;
  user-select: none;
  opacity: 0;
  transition: opacity 0.8s cubic-bezier(0.4,0,0.2,1);
}
.wallpaper-image.fade-in {
  opacity: 1;
}

.img-loading {
  position: absolute;
  left: 0; top: 0; width: 100vw; height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #222;
  z-index: 2;
}
.spinner {
  border: 6px solid #f3f3f3;
  border-top: 6px solid #3498db;
  border-radius: 50%;
  width: 60px;
  height: 60px;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>