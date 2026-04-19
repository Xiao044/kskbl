<template>
  <div class="map-trace-container">
    <div class="card-header">
      <h3 class="section-title">安全态势地理溯源</h3>
    </div>

    <div class="map-surface">
      <div
        ref="previewPane"
        class="map-partial"
        @pointerdown="onPreviewPointerDown"
        @pointermove="onPreviewPointerMove"
        @pointerup="onPreviewPointerUp"
        @pointercancel="resetPreviewPointer"
      >
        <div class="map-inner preview-map-inner" :style="previewMapStyle">
          <img
            :src="resolvedCampusMapUrl"
            alt="校园安全态势地图"
            class="map-img"
            :class="{ 'is-hidden': imageLoadFailed }"
            draggable="false"
            @error="handleImageError"
          />
          <div v-if="imageLoadFailed" class="map-fallback">
            校园地图资源加载失败
          </div>
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
            <span class="dot-label" :class="dot.labelSide === 'left' ? 'label-left' : 'label-right'">{{ dot.label }}</span>
          </div>
        </div>

        <div class="zoom-hint">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
          <span>点击放大全图，滑动查看全貌</span>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <transition name="modal-fade">
        <div v-if="showFullscreen" class="modal-overlay" @click.self="closeFullscreen">
          <div class="modal-content">
            <div class="modal-header">
              <h3 class="modal-title">校园安全态势全图</h3>
              <button class="modal-close" @click="closeFullscreen">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>

            <div class="modal-body">
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
                    :src="resolvedCampusMapUrl"
                    alt="校园安全态势地图"
                    class="modal-map-img"
                    :class="{ 'is-hidden': imageLoadFailed }"
                    draggable="false"
                    @error="handleImageError"
                  />
                  <div v-if="imageLoadFailed" class="map-fallback modal-map-fallback">
                    校园地图资源加载失败
                  </div>
                  <div
                    v-for="dot in aggregatedAlertDots"
                    :key="`modal-${dot.id}`"
                    class="alert-dot"
                    :class="[
                      dot.level === 'high' ? 'dot-high' : 'dot-medium',
                      dot.trafficType === 'internal' ? 'dot-internal' : 'dot-external',
                      activeDotDetail && activeDotDetail.id === dot.id ? 'is-active-dot' : ''
                    ]"
                    :style="{ left: dot.x, top: dot.y }"
                    @mouseenter="setActiveDot(dot)"
                    @click.stop="setActiveDot(dot)"
                  >
                    <span class="dot-core"></span>
                    <span class="dot-ripple"></span>
                    <span class="dot-label dot-label-modal" :class="dot.labelSide === 'left' ? 'label-left' : 'label-right'">{{ dot.label }}</span>
                  </div>
                </div>
              </div>

              <aside class="modal-side-panel">
                <div class="panel-header">
                  <div class="panel-header__text">
                    <h4 class="panel-title">告警点详情</h4>
                    <span class="panel-hint">悬停或点击地图圆点以查看</span>
                  </div>
                  <button
                    v-if="activeDotDetail"
                    class="panel-action"
                    type="button"
                    @click="openIpDetail(activeDotDetail.srcIp)"
                  >
                    查看 IP 画像
                  </button>
                </div>

                <div v-if="activeDotDetail" class="detail-card">
                  <div class="detail-current-banner">
                    <span class="detail-current-dot" :class="activeDotDetail.trafficType === 'internal' ? 'current-dot-internal' : 'current-dot-external'"></span>
                    <span class="detail-current-text">当前锁定点</span>
                  </div>

                  <div class="detail-pill-row">
                    <span class="detail-pill" :class="activeDotDetail.trafficType === 'internal' ? 'pill-internal' : 'pill-external'">
                      {{ activeDotDetail.trafficType === 'internal' ? '内部网络' : '外部网络' }}
                    </span>
                    <span class="detail-pill" :class="activeDotDetail.level === 'high' ? 'pill-high' : 'pill-medium'">
                      {{ activeDotDetail.level === 'high' ? '高危' : '中危' }}
                    </span>
                  </div>

                  <div class="detail-grid">
                    <div class="detail-item">
                      <span class="detail-label">来源 IP</span>
                      <button
                        class="detail-ip-link mono"
                        type="button"
                        @click="openIpDetail(activeDotDetail.srcIp)"
                      >
                        {{ activeDotDetail.srcIp }}
                      </button>
                    </div>
                    <div class="detail-item">
                      <span class="detail-label">区域锚点</span>
                      <span class="detail-value">{{ activeDotDetail.anchorLabel }}</span>
                    </div>
                    <div class="detail-item">
                      <span class="detail-label">威胁类型</span>
                      <span class="detail-value">{{ activeDotDetail.type }}</span>
                    </div>
                    <div class="detail-item">
                      <span class="detail-label">最近时间</span>
                      <span class="detail-value mono">{{ activeDotDetail.time || '--' }}</span>
                    </div>
                    <div class="detail-item">
                      <span class="detail-label">累计次数</span>
                      <span class="detail-value">{{ activeDotDetail.count }}</span>
                    </div>
                    <div class="detail-item">
                      <span class="detail-label">坐标位置</span>
                      <span class="detail-value mono">{{ activeDotDetail.x }} / {{ activeDotDetail.y }}</span>
                    </div>
                  </div>

                  <div class="detail-actions">
                    <button class="detail-action-btn primary" type="button" @click="openIpDetail(activeDotDetail.srcIp)">
                      跳转独立画像
                    </button>
                    <button class="detail-action-btn" type="button" @click="focusDotInMap(activeDotDetail)">
                      定位当前点
                    </button>
                  </div>
                </div>

                <div v-else class="detail-empty">
                  <div class="detail-empty__icon">◎</div>
                  <p>将鼠标移动到地图上的告警点，右侧将展示该点的来源、等级、类型与累计次数。</p>
                </div>
              </aside>
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
    </Teleport>
  </div>
</template>

<script>
const INTERNAL_BUILDING_POOL = [
  { x: 52.4, y: 8.8, label: '理工楼' },
  { x: 33.6, y: 28.4, label: '本13-15' },
  { x: 64.9, y: 51.9, label: '图书馆' },
  { x: 74.4, y: 10.9, label: '前3-5' }
];

const EXTERNAL_EDGE_POOL = [
  { x: 8, y: 8, label: '左上空白' },
  { x: 87, y: 35, label: '右侧边界' },
  { x: 18, y: 88, label: '底部空白' }
];

const INTERNAL_PREFIXES = [
  '10.', '30.', '45.', '63.', '66.', '77.', '84.', '123.', '131.', '143.',
  '146.', '153.', '161.', '162.', '175.', '180.', '186.', '202.', '203.', '213.'
];

const MAP_ALIGNMENT_OFFSET = {
  internal: { x: 7.2, y: 0.2 },
  external: { x: 2.4, y: 0 }
};

export default {
  name: 'MapTraceability',
  emits: ['view-ip'],
  props: {
    alerts: { type: Array, default: () => [] }
  },
  data() {
    return {
      campusMapUrl: `${process.env.BASE_URL || '/'}campus-map.jpg`,
      showFullscreen: false,
      imageLoadFailed: false,
      modalZoom: 1,
      activeDotDetail: null,
      previewPointer: null,
      previewInitialized: false,
      isPanning: false,
      panStartX: 0,
      panStartY: 0,
      panScrollLeft: 0,
      panScrollTop: 0
    };
  },
  computed: {
    resolvedCampusMapUrl() {
      return this.campusMapUrl;
    },
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
        const alignmentOffset = MAP_ALIGNMENT_OFFSET[trafficType] || { x: 0, y: 0 };
        const alignedX = anchor.x + offset.x + alignmentOffset.x;
        const alignedY = anchor.y + offset.y + alignmentOffset.y;

        aggregated.set(key, {
          id: srcIp,
          x: `${this.clampPercent(alignedX)}%`,
          y: `${this.clampPercent(alignedY)}%`,
          xValue: this.clampPercent(alignedX),
          yValue: this.clampPercent(alignedY),
          level: alert.level || 'medium',
          trafficType,
          label: trafficType === 'internal' ? '内网流量' : '外部流量',
          labelSide: anchor.x > 70 ? 'left' : 'right',
          anchorLabel: anchor.label,
          srcIp,
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
      this.resetPreviewViewport();
      window.addEventListener('resize', this.handleResize);
    });
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
    this.detachEscListener();
    document.body.style.overflow = '';
  },
  methods: {
    isInternalIp(ip) {
      return typeof ip === 'string' && INTERNAL_PREFIXES.some((prefix) => ip.startsWith(prefix));
    },
    clampPercent(value) {
      return Math.min(92, Math.max(8, Number(value.toFixed(1))));
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
    handleResize() {
      this.resetPreviewPointer();
      this.resetPreviewViewport();
    },
    handleKeydown(event) {
      if (event.key === 'Escape' && this.showFullscreen) {
        this.closeFullscreen();
      }
    },
    attachEscListener() {
      window.addEventListener('keydown', this.handleKeydown);
    },
    detachEscListener() {
      window.removeEventListener('keydown', this.handleKeydown);
    },
    handleImageError() {
      this.imageLoadFailed = true;
    },
    setActiveDot(dot) {
      this.activeDotDetail = {
        ...dot,
        x: `${dot.xValue?.toFixed ? dot.xValue.toFixed(1) : dot.xValue}%`,
        y: `${dot.yValue?.toFixed ? dot.yValue.toFixed(1) : dot.yValue}%`
      };
    },
    openIpDetail(ip) {
      if (!ip) return;
      if (this.showFullscreen) {
        this.closeFullscreen();
      }
      this.$emit('view-ip', ip);
    },
    resetPreviewViewport() {
      this.$nextTick(() => {
        const pane = this.$refs.previewPane;
        if (!pane) return;
        pane.scrollLeft = Math.max(0, (pane.scrollWidth - pane.clientWidth) / 2);
        if (!this.previewInitialized) {
          pane.scrollTop = Math.max(0, Math.min(220, pane.scrollHeight - pane.clientHeight));
          this.previewInitialized = true;
        }
      });
    },
    openFullscreen() {
      this.showFullscreen = true;
      this.modalZoom = 1;
      this.attachEscListener();
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
      this.activeDotDetail = null;
      this.detachEscListener();
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
    focusDotInMap(dot) {
      if (!dot || !this.showFullscreen) return;
      const wrapper = this.$refs.modalMapWrapper;
      if (!wrapper) return;

      this.$nextTick(() => {
        const centerX = wrapper.scrollWidth * ((dot.xValue || 50) / 100);
        const centerY = wrapper.scrollHeight * ((dot.yValue || 50) / 100);
        wrapper.scrollTo({
          left: Math.max(0, centerX - wrapper.clientWidth / 2),
          top: Math.max(0, centerY - wrapper.clientHeight / 2),
          behavior: 'smooth'
        });
      });
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
  padding: 24px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: var(--glass-bg, rgba(255,255,255,0.55));
  backdrop-filter: var(--glass-blur, blur(12px));
  -webkit-backdrop-filter: var(--glass-blur, blur(12px));
  border-radius: 24px;
  border: 1px solid var(--glass-border, rgba(218,212,200,0.4));
  box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04));
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.map-trace-container:hover {
  transform: translateY(-2px);
  box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)), 0 12px 28px rgba(0,0,0,0.08);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  margin: 0;
  color: #000000;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.36px;
}

.map-surface {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.map-partial {
  position: relative;
  height: 100%;
  min-height: 0;
  overflow: auto;
  border-radius: 20px;
  background: rgba(250, 249, 247, 0.5);
  border: 1px solid rgba(218,212,200,0.38);
  cursor: pointer;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.map-partial::-webkit-scrollbar {
  width: 0;
  height: 0;
}

.map-inner {
  position: relative;
  width: 176%;
  height: auto;
  aspect-ratio: 1290 / 2132;
  min-height: 0;
  margin-left: -23%;
  background:
    radial-gradient(circle at top left, rgba(245, 208, 97, 0.08), transparent 24%),
    linear-gradient(180deg, rgba(255,255,255,0.4) 0%, rgba(250, 249, 247, 0.55) 100%);
}

.preview-map-inner {
  position: relative;
}

.map-img {
  width: 100%;
  height: auto;
  display: block;
  pointer-events: none;
  user-select: none;
}

.map-img.is-hidden,
.modal-map-img.is-hidden {
  opacity: 0;
}

.map-fallback {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--clay-text-muted, #9f9b93);
  font-size: 14px;
  font-weight: 600;
  letter-spacing: -0.02em;
  z-index: 1;
  pointer-events: none;
}

.modal-map-fallback {
  border-radius: 16px;
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
  width: 14px;
  height: 14px;
  border-radius: 50%;
  top: -7px;
  left: -7px;
  z-index: 2;
}

.dot-ripple {
  position: absolute;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  top: -7px;
  left: -7px;
  z-index: 1;
  animation: ripple 2.6s ease-out infinite;
}

.dot-label {
  position: absolute;
  top: 10px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
  background: rgba(255,255,255,0.88);
  color: var(--clay-text-secondary, #55534e);
  border: 1px solid rgba(218,212,200,0.75);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.45), 0 1px 2px rgba(0,0,0,0.08);
  opacity: 0;
  visibility: hidden;
  transform: translateY(4px);
  transition: opacity 0.18s ease, transform 0.18s ease, visibility 0.18s ease;
}

.dot-label.label-right {
  left: 12px;
}

.dot-label.label-left {
  right: 12px;
}

.dot-label-modal {
  font-size: 11px;
}

.alert-dot:hover .dot-label,
.alert-dot:focus-within .dot-label {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.dot-high.dot-internal .dot-core,
.dot-medium.dot-internal .dot-core {
  background: #2fd6a3;
  box-shadow:
    inset 0 -1px 1px rgba(8, 102, 77, 0.35),
    inset 0 1px 1px rgba(210, 255, 241, 0.9),
    0 0 0 4px rgba(47, 214, 163, 0.2),
    0 0 10px rgba(47, 214, 163, 0.42);
}

.dot-high.dot-internal .dot-ripple,
.dot-medium.dot-internal .dot-ripple {
  border: 2px solid rgba(47, 214, 163, 0.56);
}

.dot-high.dot-external .dot-core,
.dot-medium.dot-external .dot-core {
  background: #f5d061;
  box-shadow:
    inset 0 -1px 1px rgba(166, 116, 7, 0.3),
    inset 0 1px 1px rgba(255, 250, 219, 0.9),
    0 0 0 5px rgba(245, 208, 97, 0.22),
    0 0 12px rgba(245, 208, 97, 0.44);
}

.dot-high.dot-external .dot-ripple,
.dot-medium.dot-external .dot-ripple {
  border: 2px solid rgba(245, 208, 97, 0.58);
  animation-duration: 1.55s;
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

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 2147483647;
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

.modal-body {
  flex: 1;
  min-height: 0;
  display: flex;
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
  flex: 1 1 auto;
  overflow: auto;
  cursor: grab;
  scroll-behavior: smooth;
  padding: 16px;
  user-select: none;
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-side-panel {
  width: 320px;
  flex: 0 0 320px;
  border-left: 1px solid var(--clay-border-light, #eee9df);
  background: rgba(255, 255, 255, 0.42);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 24px 20px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.panel-header__text {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.panel-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #000000;
  letter-spacing: -0.03em;
}

.panel-hint {
  font-size: 12px;
  color: var(--clay-text-muted, #9f9b93);
  font-weight: 600;
}

.panel-action {
  border: 1px solid rgba(67, 8, 159, 0.16);
  background: rgba(243, 238, 255, 0.92);
  color: var(--clay-ube, #43089f);
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.panel-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(67, 8, 159, 0.12);
}

.detail-card {
  border-radius: 18px;
  padding: 18px;
  background: rgba(250, 249, 247, 0.72);
  border: 1px solid rgba(218,212,200,0.45);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.42), 0 6px 18px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-current-banner {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(67, 8, 159, 0.08);
  border: 1px solid rgba(67, 8, 159, 0.12);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.32);
}

.detail-current-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(67, 8, 159, 0.08);
}

.current-dot-internal {
  background: #2fd6a3;
  box-shadow: 0 0 0 4px rgba(47, 214, 163, 0.16);
}

.current-dot-external {
  background: #f5d061;
  box-shadow: 0 0 0 4px rgba(245, 208, 97, 0.18);
}

.detail-current-text {
  font-size: 12px;
  font-weight: 800;
  color: var(--clay-ube, #43089f);
  letter-spacing: 0.01em;
}

.detail-pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.detail-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.01em;
}

.pill-internal {
  background: rgba(47, 214, 163, 0.18);
  color: #0a7a59;
  border: 1px solid rgba(47, 214, 163, 0.28);
}

.pill-external {
  background: rgba(79, 108, 255, 0.16);
  color: #3147c7;
  border: 1px solid rgba(79, 108, 255, 0.26);
}

.pill-high {
  background: rgba(252, 121, 129, 0.14);
  color: #c43d4b;
  border: 1px solid rgba(252, 121, 129, 0.24);
}

.pill-medium {
  background: rgba(245, 208, 97, 0.2);
  color: #9d6f06;
  border: 1px solid rgba(245, 208, 97, 0.3);
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--clay-text-muted, #9f9b93);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-value {
  font-size: 14px;
  line-height: 1.5;
  color: #171717;
  font-weight: 600;
}

.detail-value.mono {
  font-family: 'Space Mono', monospace;
  font-size: 13px;
}

.detail-ip-link {
  width: fit-content;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--clay-ube, #43089f);
  font-weight: 700;
  cursor: pointer;
  text-align: left;
  transition: color 0.2s ease, transform 0.2s ease;
}

.detail-ip-link:hover {
  color: #2f0a70;
  transform: translateY(-1px);
}

.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.detail-action-btn {
  border: 1px solid rgba(218,212,200,0.6);
  background: rgba(255,255,255,0.88);
  color: #55534e;
  border-radius: 999px;
  padding: 9px 14px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.detail-action-btn.primary {
  background: rgba(243, 238, 255, 0.92);
  color: var(--clay-ube, #43089f);
  border-color: rgba(67, 8, 159, 0.14);
}

.detail-action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(0,0,0,0.08);
}

.detail-empty {
  flex: 1;
  border-radius: 18px;
  border: 1px dashed rgba(218,212,200,0.6);
  background: rgba(250, 249, 247, 0.54);
  color: var(--clay-text-muted, #9f9b93);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 22px;
  line-height: 1.7;
}

.detail-empty__icon {
  font-size: 26px;
  color: var(--clay-ube, #43089f);
  margin-bottom: 12px;
  opacity: 0.75;
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
  width: min(100%, 540px);
  aspect-ratio: 1290 / 2132;
  flex: 0 0 auto;
  transition: transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.is-active-dot .dot-core {
  transform: scale(1.18);
  box-shadow:
    inherit,
    0 0 0 8px rgba(67, 8, 159, 0.08);
}

.is-active-dot .dot-ripple {
  animation-duration: 1.15s;
}

.modal-map-img {
  width: 100%;
  height: 100%;
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
  .map-trace-container {
    padding: 20px;
    gap: 16px;
  }

  .map-surface {
    min-height: 0;
  }

  .map-partial {
    min-height: 0;
  }

  .zoom-hint {
    left: 12px;
    right: 12px;
    justify-content: center;
  }

  .modal-body {
    flex-direction: column;
  }

  .modal-side-panel {
    width: 100%;
    flex-basis: auto;
    border-left: none;
    border-top: 1px solid var(--clay-border-light, #eee9df);
  }

  .dot-label {
    display: none;
  }
}
</style>
