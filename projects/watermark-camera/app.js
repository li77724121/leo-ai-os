/**
 * 今日水印相机 - 核心逻辑
 * 功能：相机拍照、相册选择、水印叠加、模板切换、保存图片
 */

// ============ 状态管理 ============
const state = {
  stream: null,
  facingMode: 'environment', // 'environment' 后置 | 'user' 前置
  template: 'work',
  position: 'bl', // bl, br, tl, tr
  theme: 'dark',
  options: {
    date: true,
    time: true,
    location: true,
    weather: true,
    temp: true,
    coord: false,
    step: false,
    logo: true
  },
  customTitle: '',
  brandText: '今日水印相机',
  locationData: null,
  weatherData: null,
  stepCount: 0,
  capturedImage: null
};

// ============ DOM 元素 ============
const els = {
  video: document.getElementById('video'),
  snapshot: document.getElementById('snapshot'),
  liveWatermark: document.getElementById('liveWatermark'),
  cameraWrap: document.getElementById('cameraWrap'),
  cameraHint: document.getElementById('cameraHint'),
  fileInput: document.getElementById('fileInput'),
  btnCapture: document.getElementById('btn-capture'),
  btnRetake: document.getElementById('btn-retake'),
  btnDownload: document.getElementById('btn-download'),
  btnUpload: document.getElementById('btn-upload'),
  btnFlip: document.getElementById('btn-flip'),
  templateRow: document.getElementById('templateRow'),
  posRow: document.getElementById('posRow'),
  themeRow: document.getElementById('themeRow'),
  customTitle: document.getElementById('customTitle'),
  brandText: document.getElementById('brandText'),
  optDate: document.getElementById('opt-date'),
  optTime: document.getElementById('opt-time'),
  optLocation: document.getElementById('opt-location'),
  optWeather: document.getElementById('opt-weather'),
  optTemp: document.getElementById('opt-temp'),
  optCoord: document.getElementById('opt-coord'),
  optStep: document.getElementById('opt-step'),
  optLogo: document.getElementById('opt-logo')
};

// ============ 模板配置 ============
const TEMPLATES = {
  work: {
    name: '工程打卡',
    defaults: { date: true, time: true, location: true, weather: true, temp: true, coord: true, step: false, logo: true },
    title: '工程打卡',
    showTitle: true
  },
  attend: {
    name: '考勤打卡',
    defaults: { date: true, time: true, location: true, weather: true, temp: true, coord: false, step: false, logo: true },
    title: '考勤打卡',
    showTitle: true
  },
  travel: {
    name: '旅游记录',
    defaults: { date: true, time: true, location: true, weather: true, temp: true, coord: false, step: false, logo: true },
    title: '',
    showTitle: false
  },
  time: {
    name: '时间地点',
    defaults: { date: true, time: true, location: true, weather: false, temp: false, coord: false, step: false, logo: true },
    title: '',
    showTitle: false
  },
  custom: {
    name: '自定义',
    defaults: { date: true, time: true, location: true, weather: true, temp: true, coord: false, step: false, logo: true },
    title: '',
    showTitle: true
  }
};

// ============ 主题配置 ============
const THEMES = {
  dark: { bg: 'rgba(0,0,0,0.7)', text: '#fff', accent: '#4caf50', border: 'rgba(255,255,255,0.3)' },
  blue: { bg: 'rgba(21,101,192,0.9)', text: '#fff', accent: '#64b5f6', border: 'rgba(255,255,255,0.3)' },
  red: { bg: 'rgba(198,40,40,0.9)', text: '#fff', accent: '#ef9a9a', border: 'rgba(255,255,255,0.3)' },
  green: { bg: 'rgba(46,125,50,0.9)', text: '#fff', accent: '#81c784', border: 'rgba(255,255,255,0.3)' },
  orange: { bg: 'rgba(239,108,0,0.9)', text: '#fff', accent: '#ffb74d', border: 'rgba(255,255,255,0.3)' }
};

// ============ 工具函数 ============
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

function formatDate(date = new Date()) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function formatTime(date = new Date()) {
  const h = String(date.getHours()).padStart(2, '0');
  const m = String(date.getMinutes()).padStart(2, '0');
  const s = String(date.getSeconds()).padStart(2, '0');
  return `${h}:${m}:${s}`;
}

function formatDateTime(date = new Date()) {
  return `${formatDate(date)} ${formatTime(date)}`;
}

function debounce(fn, ms = 300) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

// ============ 相机控制 ============
async function startCamera() {
  try {
    if (state.stream) {
      state.stream.getTracks().forEach(t => t.stop());
    }
    
    const constraints = {
      video: {
        facingMode: state.facingMode,
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      },
      audio: false
    };
    
    state.stream = await navigator.mediaDevices.getUserMedia(constraints);
    els.video.srcObject = state.stream;
    els.video.play();
    els.cameraHint.style.display = 'block';
    updateLiveWatermark();
  } catch (err) {
    console.error('相机启动失败:', err);
    alert('无法访问相机，请检查权限设置。将使用相册模式。');
    els.cameraWrap.style.display = 'none';
  }
}

function flipCamera() {
  state.facingMode = state.facingMode === 'environment' ? 'user' : 'environment';
  startCamera();
}

// ============ 定位与天气 ============
async function getLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }
    
    navigator.geolocation.getCurrentPosition(
      pos => resolve({
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        accuracy: pos.coords.accuracy
      }),
      err => {
        console.warn('定位失败:', err.message);
        resolve(null);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
    );
  });
}

async function reverseGeocode(lat, lng) {
  try {
    // 使用免费的 Nominatim API (OpenStreetMap)
    const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&accept-language=zh-CN`);
    const data = await res.json();
    return data.display_name || `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
  } catch (e) {
    return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
  }
}

async function getWeather(lat, lng) {
  try {
    // 使用免费的 Open-Meteo API
    const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&current_weather=true&timezone=auto`);
    const data = await res.json();
    if (data.current_weather) {
      const code = data.current_weather.weathercode;
      const temp = Math.round(data.current_weather.temperature);
      const wind = data.current_weather.windspeed;
      return { code, temp, wind, description: weatherCodeToText(code) };
    }
    return null;
  } catch (e) {
    console.warn('天气获取失败:', e);
    return null;
  }
}

function weatherCodeToText(code) {
  const map = {
    0: '晴天', 1: '多云', 2: '局部多云', 3: '阴天',
    45: '雾', 48: '雾凇',
    51: '毛毛雨', 53: '小雨', 55: '中雨', 56: '冻雨', 57: '冻雨',
    61: '小雨', 63: '中雨', 65: '大雨', 66: '冻雨', 67: '冻雨',
    71: '小雪', 73: '中雪', 75: '大雪', 77: '雪粒',
    80: '阵雨', 81: '中阵雨', 82: '大阵雨',
    85: '阵雪', 86: '大阵雪',
    95: '雷暴', 96: '雷暴伴冰雹', 99: '雷暴伴大冰雹'
  };
  return map[code] || '未知';
}

// ============ 步数模拟 ============
function getStepCount() {
  // 模拟步数（实际应用可接入健康数据API）
  const base = 5000;
  const hour = new Date().getHours();
  const factor = hour < 6 ? 0.1 : hour < 12 ? 0.5 : hour < 18 ? 0.8 : 0.3;
  return Math.floor(base * factor + Math.random() * 2000);
}

// ============ 实时水印更新 ============
function updateLiveWatermark() {
  const now = new Date();
  let text = '';
  
  if (state.options.date) text += formatDate(now) + ' ';
  if (state.options.time) text += formatTime(now) + '\n';
  if (state.locationData) {
    if (state.options.location) text += state.locationData.address + '\n';
    if (state.options.coord) text += `经度:${state.locationData.lng.toFixed(4)} 纬度:${state.locationData.lat.toFixed(4)}\n`;
  }
  if (state.weatherData) {
    if (state.options.weather) text += `${state.weatherData.description} `;
    if (state.options.temp) text += `${state.weatherData.temp}°C `;
    if (state.options.wind) text += `${state.weatherData.wind}km/h\n`;
  }
  if (state.options.step) text += `步数:${state.stepCount}\n`;
  if (state.options.logo) text += state.brandText;
  
  els.liveWatermark.textContent = text || '水印预览';
}

// ============ 模板切换 ============
function applyTemplate(tplKey) {
  const tpl = TEMPLATES[tplKey];
  if (!tpl) return;
  
  state.template = tplKey;
  
  // 更新选中状态
  $$('.tpl', els.templateRow).forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tpl === tplKey);
  });
  
  // 应用默认选项
  Object.keys(state.options).forEach(key => {
    state.options[key] = tpl.defaults[key];
    const el = els[`opt${key.charAt(0).toUpperCase() + key.slice(1)}`];
    if (el) el.checked = tpl.defaults[key];
  });
  
  // 设置标题
  if (tpl.showTitle) {
    els.customTitle.value = tpl.title;
    state.customTitle = tpl.title;
  } else {
    els.customTitle.value = '';
    state.customTitle = '';
  }
  
  updateLiveWatermark();
}

// ============ 位置切换 ============
function setPosition(pos) {
  state.position = pos;
  $$('.pos', els.posRow).forEach(btn => {
    btn.classList.toggle('active', btn.dataset.pos === pos);
  });
  updateLiveWatermark();
}

// ============ 主题切换 ============
function setTheme(theme) {
  state.theme = theme;
  $$('.theme', els.themeRow).forEach(btn => {
    btn.classList.toggle('active', btn.dataset.theme === theme);
  });
  updateLiveWatermark();
}

// ============ 选项切换 ============
function toggleOption(key, checked) {
  state.options[key] = checked;
  updateLiveWatermark();
}

// ============ 拍照核心 ============
function capturePhoto() {
  const video = els.video;
  const canvas = els.snapshot;
  const ctx = canvas.getContext('2d');
  
  // 设置画布尺寸为视频原始尺寸
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  
  // 绘制视频帧
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  
  // 绘制水印
  drawWatermark(ctx, canvas.width, canvas.height);
  
  // 隐藏视频，显示画布
  video.style.display = 'none';
  canvas.classList.remove('hidden');
  els.cameraHint.style.display = 'none';
  els.liveWatermark.style.display = 'none';
  
  // 切换按钮状态
  els.btnCapture.classList.add('hidden');
  els.btnRetake.classList.remove('hidden');
  els.btnDownload.classList.remove('hidden');
  
  // 保存图片数据
  state.capturedImage = canvas.toDataURL('image/jpeg', 0.95);
}

function retakePhoto() {
  els.video.style.display = 'block';
  els.snapshot.classList.add('hidden');
  els.cameraHint.style.display = 'block';
  els.liveWatermark.style.display = 'block';
  
  els.btnCapture.classList.remove('hidden');
  els.btnRetake.classList.add('hidden');
  els.btnDownload.classList.add('hidden');
  
  state.capturedImage = null;
}

function downloadPhoto() {
  if (!state.capturedImage) return;
  
  const link = document.createElement('a');
  link.href = state.capturedImage;
  link.download = `watermark_${formatDate(new Date()).replace(/-/g, '')}_${formatTime(new Date()).replace(/:/g, '')}.jpg`;
  link.click();
  
  // 可选：保存后自动重拍
  // setTimeout(retakePhoto, 500);
}

// ============ 从相册选择 ============
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  
  const reader = new FileReader();
  reader.onload = (evt) => {
    const img = new Image();
    img.onload = () => {
      const canvas = els.snapshot;
      const ctx = canvas.getContext('2d');
      
      // 计算缩放比例，保持宽高比
      const maxW = window.innerWidth;
      const maxH = window.innerHeight * 0.7;
      let w = img.width;
      let h = img.height;
      
      if (w > maxW || h > maxH) {
        const scale = Math.min(maxW / w, maxH / h);
        w *= scale;
        h *= scale;
      }
      
      canvas.width = w;
      canvas.height = h;
      ctx.drawImage(img, 0, 0, w, h);
      drawWatermark(ctx, w, h);
      
      // 显示结果
      els.video.style.display = 'none';
      canvas.classList.remove('hidden');
      els.cameraHint.style.display = 'none';
      els.liveWatermark.style.display = 'none';
      
      els.btnCapture.classList.add('hidden');
      els.btnRetake.classList.remove('hidden');
      els.btnDownload.classList.remove('hidden');
      
      state.capturedImage = canvas.toDataURL('image/jpeg', 0.95);
    };
    img.src = evt.target.result;
  };
  reader.readAsDataURL(file);
  
  // 重置input以便再次选择同一文件
  e.target.value = '';
}

// ============ 水印绘制核心 ============
function drawWatermark(ctx, width, height) {
  const theme = THEMES[state.theme];
  const padding = Math.max(16, width * 0.03);
  const lineHeight = Math.max(20, width * 0.025);
  const fontSize = Math.max(14, width * 0.018);
  const titleFontSize = Math.max(18, width * 0.022);
  
  // 收集水印行
  const lines = [];
  const now = new Date();
  
  // 标题
  if (state.customTitle && TEMPLATES[state.template].showTitle) {
    lines.push({ text: state.customTitle, size: titleFontSize, weight: 'bold', color: theme.accent });
    lines.push({ text: '', size: lineHeight * 0.5 }); // 间距
  }
  
  // 日期时间
  if (state.options.date || state.options.time) {
    let dt = '';
    if (state.options.date) dt += formatDate(now);
    if (state.options.date && state.options.time) dt += ' ';
    if (state.options.time) dt += formatTime(now);
    lines.push({ text: dt, size: fontSize, weight: 'normal', color: theme.text });
  }
  
  // 地点
  if (state.locationData && state.options.location) {
    lines.push({ text: state.locationData.address, size: fontSize, weight: 'normal', color: theme.text });
  }
  
  // 经纬度
  if (state.locationData && state.options.coord) {
    lines.push({ text: `经度:${state.locationData.lng.toFixed(4)} 纬度:${state.locationData.lat.toFixed(4)}`, size: fontSize * 0.85, weight: 'normal', color: theme.text });
  }
  
  // 天气
  if (state.weatherData) {
    let weatherText = '';
    if (state.options.weather) weatherText += state.weatherData.description;
    if (state.options.weather && state.options.temp) weatherText += '  ';
    if (state.options.temp) weatherText += `${state.weatherData.temp}°C`;
    if (state.options.wind) weatherText += `  ${state.weatherData.wind}km/h`;
    if (weatherText) lines.push({ text: weatherText, size: fontSize, weight: 'normal', color: theme.text });
  }
  
  // 步数
  if (state.options.step) {
    lines.push({ text: `步数:${state.stepCount}`, size: fontSize, weight: 'normal', color: theme.text });
  }
  
  // 品牌
  if (state.options.logo && state.brandText) {
    lines.push({ text: '', size: lineHeight * 0.5 });
    lines.push({ text: state.brandText, size: fontSize * 0.85, weight: 'normal', color: theme.accent });
  }
  
  if (lines.length === 0) return;
  
  // 计算水印块尺寸
  const maxTextWidth = Math.max(...lines.map(l => {
    ctx.font = `${l.weight} ${l.size}px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`;
    return ctx.measureText(l.text).width;
  }));
  
  const blockWidth = maxTextWidth + padding * 2;
  const blockHeight = lines.reduce((sum, l) => sum + l.size * 1.3, 0) + padding * 2;
  
  // 计算位置
  let x, y;
  switch (state.position) {
    case 'bl': x = padding; y = height - blockHeight - padding; break;
    case 'br': x = width - blockWidth - padding; y = height - blockHeight - padding; break;
    case 'tl': x = padding; y = padding; break;
    case 'tr': x = width - blockWidth - padding; y = padding; break;
    default: x = padding; y = height - blockHeight - padding;
  }
  
  // 绘制背景
  ctx.fillStyle = theme.bg;
  ctx.strokeStyle = theme.border;
  ctx.lineWidth = 1;
  const radius = 12;
  roundRect(ctx, x, y, blockWidth, blockHeight, radius, true, true);
  
  // 绘制左侧竖线装饰
  ctx.fillStyle = theme.accent;
  ctx.fillRect(x + 4, y + padding, 3, blockHeight - padding * 2);
  
  // 绘制文字
  let curY = y + padding;
  lines.forEach(line => {
    if (!line.text) {
      curY += line.size;
      return;
    }
    ctx.font = `${line.weight} ${line.size}px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`;
    ctx.fillStyle = line.color || theme.text;
    ctx.textBaseline = 'top';
    ctx.fillText(line.text, x + padding + 8, curY);
    curY += line.size * 1.3;
  });
}

// 圆角矩形辅助
function roundRect(ctx, x, y, w, h, r, fill, stroke) {
  if (w < 2 * r) r = w / 2;
  if (h < 2 * r) r = h / 2;
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
  if (fill) ctx.fill();
  if (stroke) ctx.stroke();
}

// ============ 事件绑定 ============
function bindEvents() {
  // 模板切换
  els.templateRow.addEventListener('click', e => {
    const btn = e.target.closest('.tpl');
    if (btn) applyTemplate(btn.dataset.tpl);
  });
  
  // 位置切换
  els.posRow.addEventListener('click', e => {
    const btn = e.target.closest('.pos');
    if (btn) setPosition(btn.dataset.pos);
  });
  
  // 主题切换
  els.themeRow.addEventListener('click', e => {
    const btn = e.target.closest('.theme');
    if (btn) setTheme(btn.dataset.theme);
  });
  
  // 选项切换
  ['Date', 'Time', 'Location', 'Weather', 'Temp', 'Coord', 'Step', 'Logo'].forEach(key => {
    const el = els[`opt${key}`];
    if (el) {
      el.addEventListener('change', () => toggleOption(key.toLowerCase(), el.checked));
    }
  });
  
  // 自定义标题
  els.customTitle.addEventListener('input', debounce(() => {
    state.customTitle = els.customTitle.value;
    updateLiveWatermark();
  }));
  
  // 品牌文字
  els.brandText.addEventListener('input', debounce(() => {
    state.brandText = els.brandText.value;
    updateLiveWatermark();
  }));
  
  // 拍照按钮
  els.btnCapture.addEventListener('click', capturePhoto);
  els.btnRetake.addEventListener('click', retakePhoto);
  els.btnDownload.addEventListener('click', downloadPhoto);
  
  // 相册选择
  els.btnUpload.addEventListener('click', () => els.fileInput.click());
  els.fileInput.addEventListener('change', handleFileSelect);
  
  // 翻转摄像头
  els.btnFlip.addEventListener('click', flipCamera);
  
  // 键盘快捷键
  document.addEventListener('keydown', e => {
    if (e.code === 'Space' && !els.btnCapture.classList.contains('hidden')) {
      e.preventDefault();
      capturePhoto();
    } else if (e.code === 'Escape' && !els.btnRetake.classList.contains('hidden')) {
      retakePhoto();
    } else if (e.code === 'KeyF') {
      flipCamera();
    }
  });
  
  // 可见性变化处理
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      updateLiveWatermark();
    }
  });
}

// ============ 初始化 ============
async function init() {
  console.log('🚀 今日水印相机 初始化中...');
  
  // 绑定事件
  bindEvents();
  
  // 获取定位
  console.log('📍 获取定位中...');
  const loc = await getLocation();
  if (loc) {
    state.locationData = {
      ...loc,
      address: await reverseGeocode(loc.lat, loc.lng)
    };
    console.log('✅ 定位成功:', state.locationData.address);
    
    // 获取天气
    console.log('🌤️ 获取天气中...');
    state.weatherData = await getWeather(loc.lat, loc.lng);
    if (state.weatherData) {
      console.log('✅ 天气获取成功:', state.weatherData);
    }
  } else {
    console.warn('⚠️ 定位失败，将使用模拟数据');
    // 模拟数据（北京）
    state.locationData = {
      lat: 39.9042,
      lng: 116.4074,
      address: '北京市朝阳区'
    };
    state.weatherData = { code: 0, temp: 22, wind: 10, description: '晴天' };
  }
  
  // 步数
  state.stepCount = getStepCount();
  
  // 启动相机
  await startCamera();
  
  // 定时更新实时水印
  setInterval(updateLiveWatermark, 1000);
  
  console.log('✅ 初始化完成');
}

// 启动
init();

// 导出供调试
window.WatermarkCamera = { state, capturePhoto, retakePhoto, downloadPhoto };