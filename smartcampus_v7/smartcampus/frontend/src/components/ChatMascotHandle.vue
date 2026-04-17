<script setup>
import { computed, onBeforeUnmount, onMounted, ref, nextTick } from 'vue'

const props = defineProps({
  isCollapsed: { type: Boolean, default: false },
  isChatFocused: { type: Boolean, default: false },
})
const emit = defineEmits(['open-chat'])

/* Scale: original orange character is 240×204
   0.58 → visual ≈ 139×118 — bigger, more impactful */
const SCALE = 0.58

/* ---- Refs ---- */
const wrapRef = ref(null)
const mouseX = ref(0)
const mouseY = ref(0)
const isHovering = ref(false)
const isBlinking = ref(false)
let rafId = null
let blinkTimer = null

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v))
}

/* ---- rAF-throttled mouse tracking ---- */
let pendingMX = 0
let pendingMY = 0
let dirty = false

function onMouseMove(e) {
  pendingMX = e.clientX
  pendingMY = e.clientY
  if (!dirty) {
    dirty = true
    rafId = requestAnimationFrame(flushMouse)
  }
}
function flushMouse() {
  dirty = false
  mouseX.value = pendingMX
  mouseY.value = pendingMY
}

/* ---- Blinking ---- */
function scheduleBlink() {
  const delay = 2500 + Math.random() * 3500
  blinkTimer = window.setTimeout(() => {
    isBlinking.value = true
    window.setTimeout(() => {
      isBlinking.value = false
      scheduleBlink()
    }, 140)
  }, delay)
}

/* ---- Mouse offset — overrides to "staring down" when chat is focused ---- */
const mouseOffset = computed(() => {
  if (props.isChatFocused) {
    return { faceX: 0, faceY: 10 }
  }
  if (!wrapRef.value) return { faceX: 0, faceY: 0 }
  const r = wrapRef.value.getBoundingClientRect()
  const cx = r.left + r.width / 2
  const cy = r.top + r.height * 0.4
  const dx = mouseX.value - cx
  const dy = mouseY.value - cy
  return {
    faceX: clamp(dx / 10, -15, 15),
    faceY: clamp(dy / 14, -10, 10),
  }
})

/* ---- Body style ---- */
const orangeStyle = computed(() => {
  const { faceX, faceY } = mouseOffset.value
  const squash = faceY * 0.011
  const pull = Math.abs(faceX) * 0.004
  const sx = 1 + squash + pull
  const sy = 1 - squash - pull * 0.45
  const skew = -faceX * 0.56
  const lr = clamp(138 + faceX * 3.5 + faceY * 1.1, 100, 200)
  const rr = clamp(138 - faceX * 3.5 + faceY * 1.1, 100, 200)
  const hoverScale = isHovering.value ? 1.06 : 1
  return {
    transform: `scale(${hoverScale}) skewX(${skew.toFixed(2)}deg) scaleX(${sx.toFixed(3)}) scaleY(${sy.toFixed(3)})`,
    transformOrigin: 'bottom center',
    borderRadius: `${lr}px ${rr}px 0 0`,
  }
})

/* ---- Eyes position ---- */
const orangeEyesStyle = computed(() => {
  const { faceX, faceY } = mouseOffset.value
  return {
    left: `${85 + faceX * 2.4}px`,
    top: `${90 + faceY * 1.45 - faceX * 0.24}px`,
    transform: `rotate(${(faceX * 0.42).toFixed(2)}deg)`,
  }
})

/* ---- Pupils ---- */
const pupilDarkStyle = computed(() => {
  const { faceX, faceY } = mouseOffset.value
  return {
    transform: `translate3d(${faceX * 0.35}px, ${faceY * 0.35}px, 0)`,
  }
})

/* ---- Mouth ---- */
const orangeMouthStyle = computed(() => {
  const { faceX, faceY } = mouseOffset.value
  if (isHovering.value) {
    return {
      width: '28px', height: '14px',
      borderRadius: '0 0 28px 28px',
      background: '#2D2D2D',
      left: `${113 + faceX * 2.2}px`,
      top: `${117 + faceY * 1.6 - faceX * 0.16}px`,
      transform: 'translateX(-50%)',
    }
  }
  if (props.isChatFocused) {
    return {
      width: '14px', height: '14px',
      borderRadius: '50%',
      background: '#2D2D2D',
      left: `${113 + faceX * 2.2}px`,
      top: `${118 + faceY * 1.6 - faceX * 0.16}px`,
      transform: 'translateX(-50%)',
    }
  }
  return {
    width: '24px', height: '12px',
    borderRadius: '0 0 24px 24px',
    background: '#2D2D2D',
    left: `${113 + faceX * 2.2}px`,
    top: `${117 + faceY * 1.6 - faceX * 0.16}px`,
    transform: `translateX(-50%) rotate(${(faceX * 0.34).toFixed(2)}deg)`,
  }
})

/* ---- Lifecycle ---- */
onMounted(() => {
  window.addEventListener('mousemove', onMouseMove, { passive: true })
  scheduleBlink()
  nextTick(() => {
    if (wrapRef.value) {
      const r = wrapRef.value.getBoundingClientRect()
      mouseX.value = r.left + r.width / 2
      mouseY.value = r.top + r.height * 0.4
    }
  })
})
onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onMouseMove)
  if (rafId) cancelAnimationFrame(rafId)
  if (blinkTimer) clearTimeout(blinkTimer)
})
</script>

<template>
  <!--
    Teleport to body: escapes sidebar's overflow:hidden AND the drawer backdrop blur.
    Visual position is still anchored to the sidebar via CSS.
  -->
  <Teleport to="body">
    <div
      class="mascot-fixed"
      :class="{ 'is-hidden': isCollapsed }"
      ref="wrapRef"
      @mouseenter="isHovering = true"
      @mouseleave="isHovering = false"
      @click="emit('open-chat')"
    >
      <!-- Scale wrapper: 240×204 at original size -->
      <div class="mascot-scale">
        <div class="m-orange" :style="orangeStyle">
          <div class="m-eyes" :style="orangeEyesStyle">
            <span class="m-eye m-eye-dark" :class="{ blink: isBlinking }">
              <span v-if="!isBlinking" class="m-pupil m-pupil-dark" :style="pupilDarkStyle" />
            </span>
            <span class="m-eye m-eye-dark" :class="{ blink: isBlinking }">
              <span v-if="!isBlinking" class="m-pupil m-pupil-dark" :style="pupilDarkStyle" />
            </span>
          </div>
          <span class="m-mouth" :style="orangeMouthStyle" />
          <div class="m-shine"></div>
        </div>
      </div>
      <!-- Clay hard-edge shadow -->
      <div class="m-clay-shadow"></div>
    </div>
  </Teleport>
</template>

<style scoped>
/* ===== Fixed-position mascot on body (teleported out of sidebar) ===== */
/* z-index: 95 — above backdrop (90), below drawer (100) */
.mascot-fixed {
  position: fixed;
  left: 48px;
  bottom: 44px;
  width: 139px;
  height: 118px;
  cursor: pointer;
  z-index: 95;
  /* Smooth show/hide with sidebar collapse */
  transition: opacity 0.35s ease, transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.mascot-fixed.is-hidden {
  opacity: 0;
  transform: translateX(-20px);
  pointer-events: none;
}

/* ===== Scale wrapper — original 240×204 ===== */
.mascot-scale {
  position: absolute;
  top: 0;
  left: 0;
  width: 240px;
  height: 204px;
  transform: scale(0.58);
  transform-origin: 0 0;
  pointer-events: none;
}

/* ===== Orange body — EXACT original 240×204 ===== */
.m-orange {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 240px;
  height: 204px;
  background: #FF8433;
  border-radius: 120px 120px 0 0;
  z-index: 1;
  overflow: hidden;
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
              border-radius 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow:
    inset 0 -6px 12px rgba(0, 0, 0, 0.1),
    inset 0 4px 8px rgba(255, 255, 255, 0.3);
}

/* ===== Eyes ===== */
.m-eyes {
  position: absolute;
  display: flex;
  gap: 36px;
  align-items: center;
  transition: left 0.5s ease-in-out, top 0.5s ease-in-out;
}
.m-eye {
  position: relative;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.12);
  transition: all 0.2s ease;
  flex: 0 0 auto;
}
.m-eye-dark {
  background: #111 !important;
  box-shadow: none !important;
  width: 12px !important;
  height: 12px !important;
}
.m-eye.blink {
  height: 2px !important;
  margin-top: 5px;
}

/* ===== Pupils ===== */
.m-pupil {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #111;
  top: 5px;
  left: 5px;
  transition: transform 0.75s cubic-bezier(0.22, 0.61, 0.36, 1);
}
.m-pupil-dark {
  top: 4px;
  left: 4px;
}

/* ===== Mouth ===== */
.m-mouth {
  position: absolute;
  width: 24px;
  height: 12px;
  border-radius: 0 0 24px 24px;
  background: #2D2D2D;
  left: 109px;
  top: 121px;
  transform: translateX(-50%);
  transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1),
    left 0.5s ease-in-out, top 0.5s ease-in-out,
    border-radius 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
    width 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
    height 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* ===== Glass shine ===== */
.m-shine {
  position: absolute;
  top: 22px;
  left: 36px;
  width: 56px;
  height: 32px;
  background: rgba(255, 255, 255, 0.22);
  border-radius: 50%;
  transform: rotate(-12deg);
  pointer-events: none;
  z-index: 2;
}

/* ===== Clay hard-edge shadow ===== */
.m-clay-shadow {
  position: absolute;
  bottom: 0;
  left: 18px;
  width: 104px;
  height: 10px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  transform: scaleY(0.5);
  box-shadow: 3px 2px 0 rgba(0, 0, 0, 0.05);
  z-index: 0;
  pointer-events: none;
}
</style>
