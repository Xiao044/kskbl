<script setup>
import { ref, watch, computed } from 'vue'
import AnimatedCharacters from './AnimatedCharacters.vue'
import zhCN from '../i18n/zh-CN'
import enUS from '../i18n/en-US'
import i18n from '../i18n'

const lang = ref('zh-CN')
const dict = computed(() => (lang.value === 'zh-CN' ? zhCN : enUS))

function t(key) {
  const row = dict.value
  return row[key] ?? key
}

const langLabel = computed(() => (lang.value === 'zh-CN' ? 'English' : '中文'))

function toggleLocale() {
  lang.value = lang.value === 'zh-CN' ? 'en-US' : 'zh-CN'
  i18n.global.locale.value = lang.value
}

const emit = defineEmits(['login-success'])

const email = ref('')
const password = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)
const focusedField = ref('none')
const isLoginError = ref(false)
const isTyping = ref(false)

const formBanner = ref('')
const emailFormatInvalid = ref(false)
let errorTimer = null

const characterConfig = {
  scale: 0.88,
  mouseSensitivityX: 20,
  mouseSensitivityY: 30,
  pupilFollowFactor: 0.35,
}

function onEmailFocus() { focusedField.value = 'email'; isTyping.value = true }
function onEmailBlur() { focusedField.value = 'none'; isTyping.value = false }
function onPasswordFocus() { focusedField.value = 'password'; isTyping.value = true }
function onPasswordBlur() { focusedField.value = 'none'; isTyping.value = false }

function togglePassword() { showPassword.value = !showPassword.value }

function isValidEmail(v) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)
}

function clearFormErrors() {
  formBanner.value = ''
  emailFormatInvalid.value = false
}

function handleLogin() {
  clearFormErrors()

  if (!email.value.trim() || !password.value) {
    formBanner.value = t('loginFailEmpty')
    triggerError()
    return
  }
  if (!isValidEmail(email.value)) {
    emailFormatInvalid.value = true
    triggerError()
    return
  }

  // TODO: 对接后端鉴权 API，成功后 emit('login-success')
  formBanner.value = t('loginFailCheck')
  triggerError()
}

function triggerError() {
  isLoginError.value = true
  if (errorTimer) window.clearTimeout(errorTimer)
  errorTimer = window.setTimeout(() => { isLoginError.value = false }, 2200)
}

watch([email, password], () => {
  clearFormErrors()
  if (isLoginError.value) {
    isLoginError.value = false
    if (errorTimer) { window.clearTimeout(errorTimer); errorTimer = null }
  }
})
</script>

<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="left-panel">
        <AnimatedCharacters
          :config="characterConfig"
          :focused-field="focusedField"
          :is-password-visible="showPassword"
          :password-length="password.length"
          :is-login-error="isLoginError"
          :is-typing="isTyping"
        />
      </section>

      <section class="right-panel">
        <div class="form-card">
          <button class="lang-btn" type="button" @click.stop.prevent="toggleLocale">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            {{ langLabel }}
          </button>

          <div class="form-center" :key="lang">
            <div v-if="formBanner" class="form-banner" role="alert">
              {{ formBanner }}
            </div>

            <h1>{{ t('welcomeBack') }}</h1>
            <p class="subtitle">{{ t('enterDetails') }}</p>

            <label class="field-label">{{ t('email') }}</label>
            <div
              class="input-wrap"
              :class="{
                focused: focusedField === 'email',
                'input-error': emailFormatInvalid,
              }"
            >
              <input
                v-model="email"
                type="email"
                :placeholder="t('emailPlaceholder')"
                autocomplete="email"
                @focus="onEmailFocus"
                @blur="onEmailBlur"
              />
            </div>
            <p v-if="emailFormatInvalid" class="field-error">{{ t('emailFormatError') }}</p>

            <label class="field-label">{{ t('password') }}</label>
            <div class="input-wrap" :class="{ focused: focusedField === 'password' }">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                :placeholder="t('passwordPlaceholder')"
                autocomplete="current-password"
                maxlength="30"
                @focus="onPasswordFocus"
                @blur="onPasswordBlur"
              />
              <button class="eye-btn" type="button" tabindex="-1" @click="togglePassword">
                <svg v-if="!showPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>

            <div class="action-row">
              <label class="checkbox-wrap">
                <input v-model="rememberMe" type="checkbox" />
                <span class="checkmark" :class="{ checked: rememberMe }">
                  <svg v-if="rememberMe" width="10" height="10" viewBox="0 0 10 10"><path d="M2 5l2.5 2.5L8 3" stroke="#fff" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </span>
                <span>{{ t('rememberMe') }}</span>
              </label>
              <a href="javascript:void(0)" class="forgot-link">{{ t('forgotPassword') }}</a>
            </div>

            <button class="login-btn" type="button" @click="handleLogin">{{ t('loginAccount') }}</button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  background: #0B0B0D;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 24px 16px;
}

.login-shell {
  width: 100%;
  max-width: 1320px;
  height: 800px;
  border-radius: 28px;
  overflow: hidden;
  display: grid;
  grid-template-columns: 1.55fr 1fr;
  background: #e9e9e9;
  box-shadow: 0 20px 80px rgba(0,0,0,0.1);
  flex-shrink: 0;
}

.left-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 12px 48px;
  overflow: hidden;
}

.right-panel {
  display: flex;
  align-items: stretch;
  padding: 8px 8px 8px 0;
  overflow: hidden;
}
.form-card {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #fff;
  border-radius: 28px;
  padding: 28px 56px 20px;
  position: relative;
  overflow-y: auto;
}
.form-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.form-banner {
  width: 100%;
  max-width: 380px;
  padding: 10px 14px;
  margin-bottom: 10px;
  border-radius: 10px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.45;
  text-align: center;
}

.lang-btn {
  position: absolute; top: 14px; left: 14px;
  padding: 4px 12px;
  border: 1px solid #e5e7eb; border-radius: 8px;
  background: #fff; font-size: 12px; color: #555;
  cursor: pointer; transition: background 0.2s;
  display: flex; align-items: center; gap: 5px; z-index: 2;
}
.lang-btn:hover { background: #f3f4f6; }

h1 { font-size: 26px; font-weight: 700; color: #1d2231; letter-spacing: -0.2px; text-align: center; margin-top: 4px; }
.subtitle { color: #737373; font-size: 13px; text-align: center; margin: 4px 0 16px; }

.field-label { display: block; width: 100%; max-width: 380px; font-size: 12px; font-weight: 600; color: #111; margin-bottom: 4px; }
.input-wrap {
  width: 100%; max-width: 380px;
  display: flex; align-items: center;
  border: 1px solid #d7d9e0; border-radius: 999px;
  background: #fff; height: 44px; padding: 0 16px;
  margin-bottom: 10px; transition: box-shadow 0.25s, border-color 0.25s;
}
.input-wrap.focused { box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-color: #bbb; }
.input-wrap.input-error { border-color: #e7616f; background: #fffafa; }
.field-error {
  width: 100%; max-width: 380px;
  font-size: 11px; color: #e7616f;
  margin: -6px 0 8px; padding-left: 16px;
}
.input-wrap input { flex: 1; border: none; outline: none; background: transparent; font-size: 13px; color: #1d2231; height: 100%; }
.input-wrap input::placeholder { color: #aaa; }
.eye-btn { background: none; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #888; padding: 4px; }
.eye-btn:hover { color: #333; }

.action-row { width: 100%; max-width: 380px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; font-size: 12px; }
.checkbox-wrap { display: flex; align-items: center; gap: 6px; cursor: pointer; color: #555; font-weight: 500; user-select: none; }
.checkbox-wrap input { display: none; }
.checkmark { width: 16px; height: 16px; border: 1.5px solid #171717; border-radius: 4px; display: flex; align-items: center; justify-content: center; transition: background 0.15s; flex-shrink: 0; }
.checkmark.checked { background: #171717; }
.forgot-link { color: #555; text-decoration: none; font-weight: 600; }
.forgot-link:hover { color: #111; }

.login-btn { width: 100%; max-width: 380px; height: 48px; border: none; border-radius: 999px; background: #171717; color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s; margin-bottom: 10px; }
.login-btn:hover { background: #333; }

@media (max-width: 980px) {
  .login-shell { grid-template-columns: 1fr; height: auto; }
  .left-panel { min-height: 320px; }
  .form-card { padding: 28px 24px 16px; }
}
@media (max-width: 640px) {
  .login-page { padding: 16px 16px 12px; }
  .login-shell { border-radius: 20px; }
  .form-card { padding: 24px 16px 12px; border-radius: 20px; }
  .left-panel { display: none; }
}
</style>
