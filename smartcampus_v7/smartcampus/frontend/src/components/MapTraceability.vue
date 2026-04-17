<template>
  <div class="map-trace-container">
    <div
      ref="previewPane"
      class="map-partial"
      @scroll="updatePreviewScrollState"
      @pointerdown="onPreviewPointerDown"
      @pointermove="onPreviewPointerMove"
      @pointerup="onPreviewPointerUp"
      @pointercancel="resetPreviewPointer"
    >
      <div class="map-inner">
        <img
          :src="campusMapUrl"
          alt="校园安全态势地图"
          class="map-img"
          draggable="false"
        />
        <div
          v-for="dot in aggregatedAlertDots"
          :key="dot.id"
          class="alert-dot"
          :class="[
            dot.level === 'high' ? 'dot-high' : 'dot-medium',
            dot.trafficType === 'internal' ? 'dot-internal' : 'dot-external'
          ]"
          :style="{ left: dot.x, top: dot.y }"
        >
          <span class="dot-core"></span>
          <span class="dot-ripple"></span>
          <span class="dot-label">{{ dot.label }}</span>
        </div>
      </div>

      <div class="scroll-fade scroll-fade-top" :class="{ visible: canScrollUp }"></div>
      <div class="scroll-fade scroll-fade-bottom" :class="{ visible: canScrollDown }"></div>

      <div class="zoom-hint">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
        <span>点击放大全图，滑动查看全貌</span>
      </div>

      <div class="map-title">安全态势地理溯源</div>
    </div>

    <transition name="modal-fade">
      <div v-if="showFullscreen" class="modal-overlay" @click.self="closeFullscreen">
        <div class="modal-content">
          <div class="modal-header">
            <h3 class="modal-title">校园安全态势全图</h3>
            <button class="modal-close" @click="closeFullscreen">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>

          <div
            ref="modalMapWrapper"
            class="modal-map-wrapper"
            @pointerdown="startPan"
            @pointermove="onPan"
            @pointerup="endPan"
            @pointerleave="endPan"
            @pointercancel="endPan"
          >
            <div class="modal-map-inner" :style="modalMapStyle">
              <img
                :src="campusMapUrl"
                alt="校园安全态势地图"
                class="modal-map-img"
                draggable="false"
              />
              <div
                v-for="dot in aggregatedAlertDots"
                :key="`modal-${dot.id}`"
                class="alert-dot"
                :class="[
                  dot.level === 'high' ? 'dot-high' : 'dot-medium',
                  dot.trafficType === 'internal' ? 'dot-internal' : 'dot-external'
                ]"
                :style="{ left: dot.x, top: dot.y }"
              >
                <span class="dot-core"></span>
                <span class="dot-ripple"></span>
                <span class="dot-label dot-label-modal">{{ dot.label }}</span>
              </div>
            </div>
          </div>

          <div class="zoom-controls">
            <button class="zoom-btn" @click="zoomIn" title="放大">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            </button>
            <span class="zoom-level">{{ Math.round(modalZoom * 100) }}%</span>
            <button class="zoom-btn" @click="zoomOut" title="缩小">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            </button>
            <button class="zoom-btn" @click="zoomReset" title="重置">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import campusMapUrl from '@/assets/campus-map.jpg';

const INTERNAL_BUILDING_POOL = [
  { x: 45, y: 8, label: '理工楼' },
  { x: 25, y: 28, label: '本13-15' },
  { x: 65, y: 52, label: '图书馆' },
  { x: 75, y: 10, label: '前3-5' }
];

const EXTERNAL_EDGE_POOL = [
  { x: 5, y: 5, label: '左上空白' },
  { x: 92, y: 35, label: '右侧边界' },
  { x: 15, y: 92, label: '底部空白' }
];

const INTERNAL_PREFIXES = [
  '10.', '30.', '45.', '63.', '66.', '77.', '84.', '123.', '131.', '143.',
  '146.', '153.', '161.', '162.', '175.', '180.', '186.', '202.', '203.', '213.'
];

export default {
  name: 'MapTraceability',
  props: {
    alerts: { type: Array, default: () => [] }
  },
  data() {
    return {
      campusMapUrl,
      showFullscreen: false,
      modalZoom: 1,
      previewPointer: null,
      canScrollUp: false,
      canScrollDown: true,
      isPanning: false,
      panStartX: 0,
      panStartY: 0,
      panScrollLeft: 0,
      panScrollTop: 0
    };
  },
  computed: {
    modalMapStyle() {
      return {
        transform: `scale(${this.modalZoom})`,
        transformOrigin: 'top left'
      };
    },
    aggregatedAlertDots() {
      const aggregated = new Map();

      this.alerts.forEach((alert) => {
        const srcIp = alert.src_ip || '';
        if (!srcIp) return;

        const trafficType = this.isInternalIp(srcIp) ? 'internal' : 'external';
        const key = srcIp;
        const existing = aggregated.get(key);

        if (existing) {
          existing.count += Number(alert.count || 1);
          if (alert.level === 'high') existing.level = 'high';
          if (String(alert.time || '') >= String(existing.time || '')) {
            existing.time = alert.time || existing.time;
            existing.type = alert.type || existing.type;
          }
          return;
        }

        const anchor = this.pickAnchor(srcIp, trafficType);
        const offset = this.getDeterministicOffset(srcIp, trafficType === 'internal' ? 1.2 : 1.0);

        aggregated.set(key, {
          id: srcIp,
          x: `${this.clampPercent(anchor.x + offset.x)}%`,
          y: `${this.clampPercent(anchor.y + offset.y)}%`,
          level: alert.level || 'medium',
          trafficType,
          label: trafficType === 'internal' ? '内网流量' : '外部流量',
          count: Number(alert.count || 1),
          time: alert.time || '',
          type: alert.type || '未知威胁'
        });
      });

      return Array.from(aggregated.values());
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.updatePreviewScrollState();
      window.addEventListener('resize', this.handleResize);
    });
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
  },
  methods: {
    isInternalIp(ip) {
      return typeof ip === 'string' && INTERNAL_PREFIXES.some((prefix) => ip.startsWith(prefix));
    },
    clampPercent(value) {
      return Math.min(96, Math.max(4, Number(value.toFixed(1))));
    },
    hashString(seed) {
      let hash = 0;
      for (let i = 0; i < seed.length; i += 1) {
        hash = ((hash << 5) - hash + seed.charCodeAt(i)) | 0;
      }
      return Math.abs(hash);
    },
    pickAnchor(seed, trafficType) {
      const pool = trafficType === 'internal' ? INTERNAL_BUILDING_POOL : EXTERNAL_EDGE_POOL;
      const octets = typeof seed === 'string' ? seed.split('.').map((part) => Number(part) || 0) : [];
      const featureHash = octets.length >= 4
        ? (octets[2] * 31 + octets[3] * 17 + octets[0])
        : this.hashString(seed);
      const index = Math.abs(featureHash) % pool.length;
      return pool[index];
    },
    getDeterministicOffset(seed, range) {
      const hash = this.hashString(seed);
      const x = ((((hash & 0xff) / 255) - 0.5) * 2 * range);
      const y = (((((hash >> 8) & 0xff) / 255) - 0.5) * 2 * range);
      return {
        x: Number(x.toFixed(2)),
        y: Number(y.toFixed(2))
      };
    },
    onPreviewPointerDown(event) {
      this.previewPointer = {
        x: event.clientX,
        y: event.clientY,
        moved: false
      };
    },
    onPreviewPointerMove(event) {
      if (!this.previewPointer) return;
      const dx = Math.abs(event.clientX - this.previewPointer.x);
      const dy = Math.abs(event.clientY - this.previewPointer.y);
      if (dx > 8 || dy > 8) {
        this.previewPointer.moved = true;
      }
    },
    onPreviewPointerUp() {
      if (this.previewPointer && !this.previewPointer.moved) {
        this.openFullscreen();
      }
      this.resetPreviewPointer();
    },
    resetPreviewPointer() {
      this.previewPointer = null;
    },
    updatePreviewScrollState() {
      const pane = this.$refs.previewPane;
      if (!pane) return;
      this.canScrollUp = pane.scrollTop > 6;
      this.canScrollDown = pane.scrollTop + pane.clientHeight < pane.scrollHeight - 6;
    },
    handleResize() {
      this.updatePreviewScrollState();
    },
    openFullscreen() {
      this.showFullscreen = true;
      this.modalZoom = 1;
      document.body.style.overflow = 'hidden';
      this.$nextTick(() => {
        const wrapper = this.$refs.modalMapWrapper;
        if (!wrapper) return;
        wrapper.scrollTop = 0;
        wrapper.scrollLeft = 0;
      });
    },
    closeFullscreen() {
      this.showFullscreen = false;
      this.isPanning = false;
      document.body.style.overflow = '';
    },
    zoomIn() {
      this.modalZoom = Math.min(3, this.modalZoom + 0.25);
    },
    zoomOut() {
      this.modalZoom = Math.max(0.75, this.modalZoom - 0.25);
    },
    zoomReset() {
      this.modalZoom = 1;
    },
    startPan(event) {
      if (!this.showFullscreen) return;
      const wrapper = this.$refs.modalMapWrapper;
      if (!wrapper) return;
      this.isPanning = true;
      this.panStartX = event.clientX;
      this.panStartY = event.clientY;
      this.panScrollLeft = wrapper.scrollLeft;
      this.panScrollTop = wrapper.scrollTop;
      wrapper.setPointerCapture?.(event.pointerId);
    },
    onPan(event) {
      if (!this.isPanning) return;
      const wrapper = this.$refs.modalMapWrapper;
      if (!wrapper) return;
      const dx = event.clientX - this.panStartX;
      const dy = event.clientY - this.panStartY;
      wrapper.scrollLeft = this.panScrollLeft - dx;
      wrapper.scrollTop = this.panScrollTop - dy;
    },
    endPan(event) {
      if (!this.isPanning) return;
      const wrapper = this.$refs.modalMapWrapper;
      wrapper?.releasePointerCapture?.(event.pointerId);
      this.isPanning = false;
    }
  }
};
</script>

<style scoped>
.map-trace-container {
  width: 100%;
  height: 100%;
}

.map-partial {
  position: relative;
  height: 320px;
  overflow-y: auto;
  overflow-x: hidden;
  border-radius: 24px;
  background: var(--glass-bg, rgba(255,255,255,0.55));
  backdrop-filter: var(--glass-blur, blur(12px));
  -webkit-backdrop-filter: var(--glass-blur, blur(12px));
  border: 1px solid var(--glass-border, rgba(218,212,200,0.4));
  box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04));
  cursor: pointer;
  scroll-behavior: smooth;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.map-partial::-webkit-scrollbar {
  width: 0;
  height: 0;
}

.map-partial:hover {
  transform: translateY(-2px);
  box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)), 0 8px 24px rgba(0,0,0,0.06);
}

.map-inner {
  position: relative;
  width: 100%;
  min-height: 520px;
}

.map-img {
  width: 100%;
  height: auto;
  display: block;
  pointer-events: none;
  user-select: none;
}

.alert-dot {
  position: absolute;
  width: 0;
  height: 0;
  z-index: 5;
  transform: translate(-50%, -50%);
}

.dot-core {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  top: -5px;
  left: -5px;
  z-index: 2;
}

.dot-ripple {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  top: -5px;
  left: -5px;
  z-index: 1;
  animation: ripple 2.6s ease-out infinite;
}

.dot-label {
  position: absolute;
  top: 10px;
  left: 12px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
  background: rgba(255,255,255,0.88);
  color: var(--clay-text-secondary, #55534e);
  border: 1px solid rgba(218,212,200,0.75);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.45), 0 1px 2px rgba(0,0,0,0.08);
}

.dot-label-modal {
  font-size: 11px;
}

.dot-high.dot-internal .dot-core,
.dot-medium.dot-internal .dot-core {
  background: #fc7981;
  box-shadow: 0 0 0 4px rgba(252, 121, 129, 0.16), 0 0 8px rgba(252, 121, 129, 0.38);
}

.dot-high.dot-internal .dot-ripple,
.dot-medium.dot-internal .dot-ripple {
  border: 2px solid rgba(252, 121, 129, 0.45);
}

.dot-high.dot-external .dot-core,
.dot-medium.dot-external .dot-core {
  background: #fbbd41;
  box-shadow: 0 0 0 4px rgba(251, 189, 65, 0.18), 0 0 8px rgba(251, 189, 65, 0.42);
}

.dot-high.dot-external .dot-ripple,
.dot-medium.dot-external .dot-ripple {
  border: 2px solid rgba(208, 138, 17, 0.6);
  animation-duration: 1.7s;
}

@keyframes ripple {
  0% {
    transform: scale(1);
    opacity: 0.85;
  }
  100% {
    transform: scale(4.6);
    opacity: 0;
  }
}

.scroll-fade {
  position: sticky;
  left: 0;
  right: 0;
  height: 28px;
  z-index: 7;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.scroll-fade.visible {
  opacity: 1;
}

.scroll-fade-top {
  top: 0;
  margin-bottom: -28px;
  background: linear-gradient(to bottom, rgba(250,249,247,0.95), rgba(250,249,247,0));
}

.scroll-fade-bottom {
  bottom: 0;
  margin-top: -28px;
  background: linear-gradient(to top, rgba(250,249,247,0.95), rgba(250,249,247,0));
}

.zoom-hint {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.74);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid var(--glass-border, rgba(218,212,200,0.4));
  font-size: 12px;
  font-weight: 600;
  color: var(--clay-text-secondary, #55534e);
  z-index: 10;
  pointer-events: none;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.map-title {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 20px;
  background: linear-gradient(to top, rgba(250,249,247,0.92) 0%, rgba(250,249,247,0.6) 70%, transparent 100%);
  font-size: 14px;
  font-weight: 700;
  color: var(--clay-text, #000);
  z-index: 8;
  letter-spacing: -0.28px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  box-sizing: border-box;
}

.modal-content {
  position: relative;
  width: 92vw;
  max-width: 1200px;
  height: 88vh;
  background: var(--glass-bg-heavy, rgba(255,255,255,0.72));
  backdrop-filter: var(--glass-blur, blur(12px));
  -webkit-backdrop-filter: var(--glass-blur, blur(12px));
  border-radius: 24px;
  border: 1px solid var(--glass-border, rgba(218,212,200,0.4));
  box-shadow: var(--clay-shadow), 0 16px 64px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--clay-border-light, #eee9df);
  flex-shrink: 0;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--clay-text, #000);
  letter-spacing: -0.36px;
}

.modal-close {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--glass-border, rgba(218,212,200,0.4));
  background: rgba(250,249,247,0.6);
  color: var(--clay-text-secondary, #55534e);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-close:hover {
  background: var(--clay-pomegranate-bg, #fff0f1);
  color: var(--clay-pomegranate, #fc7981);
  transform: rotateZ(-8deg) translateY(-2px);
  box-shadow: rgb(0,0,0) -3px 3px;
}

.modal-map-wrapper {
  flex: 1;
  overflow: auto;
  cursor: grab;
  scroll-behavior: smooth;
  padding: 16px;
  user-select: none;
}

.modal-map-wrapper:active {
  cursor: grabbing;
}

.modal-map-wrapper::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.modal-map-wrapper::-webkit-scrollbar-thumb {
  background: var(--clay-border, #dad4c8);
  border-radius: 6px;
}

.modal-map-inner {
  position: relative;
  width: max-content;
  min-width: 100%;
  transition: transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-map-img {
  width: min(100%, 1100px);
  height: auto;
  display: block;
  border-radius: 16px;
  pointer-events: none;
  user-select: none;
}

.zoom-controls {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border, rgba(218,212,200,0.4));
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  z-index: 20;
}

.zoom-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--glass-border, rgba(218,212,200,0.4));
  background: rgba(250,249,247,0.6);
  color: var(--clay-text-secondary, #55534e);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.zoom-btn:hover {
  background: var(--clay-ube-bg, #f3eeff);
  color: var(--clay-ube, #43089f);
  transform: translateY(-1px);
  box-shadow: var(--clay-shadow);
}

.zoom-level {
  font-size: 12px;
  font-weight: 600;
  color: var(--clay-text-muted, #9f9b93);
  font-family: var(--clay-mono, 'Space Mono', monospace);
  min-width: 40px;
  text-align: center;
}

.modal-fade-enter-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-active .modal-content {
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
}

.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-leave-active .modal-content {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-fade-enter-from {
  opacity: 0;
}

.modal-fade-enter-from .modal-content {
  transform: scale(0.92);
}

@media (max-width: 900px) {
  .map-partial {
    height: 300px;
  }

  .map-inner {
    min-height: 480px;
  }

  .zoom-hint {
    left: 12px;
    right: 12px;
    justify-content: center;
  }

  .dot-label {
    display: none;
  }
}
</style>
