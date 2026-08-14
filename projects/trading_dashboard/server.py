#!/usr/bin/env python3
"""交易监控大屏 - SOL网格 + 行情 + RSI + 成交量 + MA"""
import json, os, time, http.server, socketserver, math, threading, urllib.request

PORT = 8888
CACHE = {"sol": {}, "btc": {}, "eth": {}, "balance": {}, "history": []}
LOCK = threading.Lock()

def fetch_ticker(symbol):
    url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}-USDT"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    req.set_proxy("127.0.0.1:7897", "http")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())["data"][0]
            return {
                "symbol": symbol, "last": float(d["last"]),
                "high": float(d.get("high24h", 0)), "low": float(d.get("low24h", 0)),
                "open": float(d.get("open24h", 0)), "vol": float(d.get("vol24h", 0)),
                "change": round((float(d["last"]) / float(d.get("open24h", d["last"])) - 1) * 100, 2)
            }
    except: return None

def fetch_kline(symbol, bar="15m", limit=50):
    url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}-USDT&bar={bar}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    req.set_proxy("127.0.0.1:7897", "http")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())["data"]
            closes = [float(d[4]) for d in reversed(data)]
            highs = [float(d[2]) for d in reversed(data)]
            lows = [float(d[3]) for d in reversed(data)]
            vols = [float(d[6]) for d in reversed(data)]
            return {"close": closes, "high": highs, "low": lows, "vol": vols}
    except: return None

def compute_rsi(closes, period=14):
    if len(closes) < period + 1: return []
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    rsi = [None] * period
    gains = [d if d > 0 else 0 for d in deltas[:period]]
    losses = [-d if d < 0 else 0 for d in deltas[:period]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi.append(100 - 100 / (1 + rs))
    for i in range(period, len(deltas)):
        gain = deltas[i] if deltas[i] > 0 else 0
        loss = -deltas[i] if deltas[i] < 0 else 0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi.append(round(100 - 100 / (1 + rs), 2))
    return rsi

def compute_ma(closes):
    ma5, ma10, ma20 = [], [], []
    for i in range(len(closes)):
        ma5.append(round(sum(closes[max(0,i-4):i+1]) / min(5, i+1), 2) if i >= 0 else None)
        ma10.append(round(sum(closes[max(0,i-9):i+1]) / min(10, i+1), 2) if i >= 6 else None)
        ma20.append(round(sum(closes[max(0,i-19):i+1]) / min(20, i+1), 2) if i >= 15 else None)
    return {"ma5": ma5, "ma10": ma10, "ma20": ma20}

def updater():
    while True:
        try:
            for sym in ["SOL", "BTC", "ETH"]:
                tick = fetch_ticker(sym)
                if tick:
                    kline = fetch_kline(sym)
                    rsi = compute_rsi(kline["close"]) if kline else []
                    ma = compute_ma(kline["close"]) if kline else {}
                    with LOCK:
                        CACHE[sym.lower()] = {
                            "ticker": tick, "kline": kline,
                            "rsi": rsi, "ma": ma
                        }
            # 记录历史
            with LOCK:
                CACHE["history"].append({
                    "time": time.strftime("%H:%M:%S"),
                    "sol": CACHE.get("sol", {}).get("ticker", {}).get("last")
                })
                if len(CACHE["history"]) > 100:
                    CACHE["history"] = CACHE["history"][-100:]
        except: pass
        time.sleep(15)

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_html(HTML)
        elif self.path == "/api/data":
            with LOCK:
                self.send_json(CACHE)
        elif self.path == "/api/status":
            self.send_json({"status": "ok", "uptime": "running"})
        else:
            self.send_error(404)

    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>📊 Leo AI 交易大屏</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0f;color:#e0e0e0;font-family:system-ui,sans-serif;padding:20px}
.header{text-align:center;padding:20px;border-bottom:1px solid #2a2a3a;margin-bottom:20px}
.header h1{font-size:28px;background:linear-gradient(135deg,#00ff88,#00d4ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header .time{color:#666;margin-top:4px;font-size:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;max-width:1400px;margin:0 auto}
.card{background:#12121a;border:1px solid #2a2a3a;border-radius:12px;padding:20px}
.card h2{color:#888;font-size:14px;margin-bottom:10px}
.price{font-size:36px;font-weight:800;margin:8px 0}
.price.up{color:#00ff88}
.price.down{color:#ff4444}
.change{font-size:16px;margin-left:8px}
.indicators{display:flex;gap:12px;flex-wrap:wrap;margin-top:10px}
.ind{padding:6px 12px;border-radius:6px;font-size:12px;font-weight:600}
.ind.green{background:rgba(0,255,136,.1);color:#00ff88}
.ind.red{background:rgba(255,68,68,.1);color:#ff4444}
.ind.blue{background:rgba(0,212,255,.1);color:#00d4ff}
.ind.yellow{background:rgba(255,200,0,.1);color:#ffc800}
.chart-container{position:relative;height:200px;margin-top:12px}
canvas{width:100%;height:100%}
.signal{font-size:13px;padding:8px 12px;border-radius:8px;margin-top:10px}
.signal.buy{background:rgba(0,255,136,.1);border:1px solid #00ff88;color:#00ff88}
.signal.sell{background:rgba(255,68,68,.1);border:1px solid #ff4444;color:#ff4444}
.signal.wait{background:rgba(0,212,255,.1);border:1px solid #00d4ff;color:#00d4ff}
.footer{text-align:center;margin-top:30px;color:#444;font-size:12px}
.blink{animation:blink 1s infinite}
@keyframes blink{50%{opacity:.3}}
</style>
</head>
<body>
<div class="header">
  <h1>📊 Leo AI 交易监控大屏</h1>
  <div class="time" id="clock">--</div>
</div>
<div class="grid">
  <div class="card" id="solCard"><h2>💎 SOL/USDT</h2><div class="price">--</div></div>
  <div class="card" id="btcCard"><h2>₿ BTC/USDT</h2><div class="price">--</div></div>
  <div class="card" id="ethCard"><h2>⟠ ETH/USDT</h2><div class="price">--</div></div>
</div>
<div class="footer">Leo AI Trading Dashboard · 15s刷新 · 实时OKX数据</div>
<script>
let charts = {};
function initChart(id) {
  const canvas = document.createElement('canvas');
  document.getElementById(id).querySelector('.chart-container')?.remove();
  const div = document.createElement('div'); div.className='chart-container';
  div.appendChild(canvas);
  document.getElementById(id).appendChild(div);
  const ctx = canvas.getContext('2d');
  canvas.width = canvas.parentElement.clientWidth;
  canvas.height = 200;
  return {ctx, canvas};
}
function drawChart(ctx, data, w, h) {
  const {close, rsi, vol, high, low} = data.kline || {};
  if (!close || !close.length) return;
  ctx.clearRect(0,0,w,h);
  const last = close[close.length-1];
  const min = Math.min(...high.slice(-50).filter(Boolean)) * 0.995;
  const max = Math.max(...high.slice(-50).filter(Boolean)) * 1.005;
  const range = max - min || 1;
  const xStep = w / close.length;
  // 价格线
  ctx.strokeStyle = '#00d4ff'; ctx.lineWidth=1.5; ctx.beginPath();
  close.forEach((p,i) => {const x=i*xStep, y=h-(p-min)/range*h; i===0?ctx.moveTo(x,y):ctx.lineTo(x,y)});
  ctx.stroke();
  // MA5
  const ma = data.ma || {};
  if (ma.ma5) {ctx.strokeStyle='#ffc80040'; ctx.lineWidth=1; ctx.beginPath();
    ma.ma5.forEach((p,i)=>{if(p===null)return; const x=i*xStep, y=h-(p-min)/range*h; ctx.moveTo(x,y); ctx.lineTo(x,y)}); ctx.stroke();}
  // RSI overlay
  if (rsi && rsi.length) {
    rsi.forEach((v,i)=>{if(v===null)return; const x=i*xStep;
      ctx.fillStyle=v>70?'#ff444420':v<30?'#00ff8820':'transparent';
      ctx.fillRect(x,0,xStep,4);});
  }
  // 当前价线
  const cy = h - (last - min) / range * h;
  ctx.strokeStyle = '#ffffff30'; ctx.setLineDash([4,4]); ctx.beginPath();
  ctx.moveTo(0,cy); ctx.lineTo(w,cy); ctx.stroke(); ctx.setLineDash([]);
  ctx.fillStyle = '#fff'; ctx.font='10px monospace'; ctx.fillText('$'+last, w-60, cy-4);
}
function updateCard(id, sym, data) {
  const card = document.getElementById(id);
  const t = data.ticker;
  if (!t) return;
  let color = t.change >= 0 ? 'up' : 'down';
  card.innerHTML = `<h2>${sym==='sol'?'💎':sym==='btc'?'₿':'⟠'} ${t.symbol}/USDT</h2>
    <div class="price ${color}">$${t.last.toFixed(2)}<span class="change">${t.change>=0?'+':''}${t.change}%</span></div>
    <div class="indicators">
      <span class="ind blue">H: $${t.high.toFixed(2)}</span>
      <span class="ind yellow">L: $${t.low.toFixed(2)}</span>
      <span class="ind ${t.change>=0?'green':'red'}">24h量: ${(t.vol/1000).toFixed(0)}K</span>
    </div>
    ${data.rsi && data.rsi.length ? `<div class="indicators"><span class="ind ${data.rsi[data.rsi.length-1]>70?'red':data.rsi[data.rsi.length-1]<30?'green':'blue'}">RSI(14): ${data.rsi[data.rsi.length-1]}</span></div>` : ''}
    ${signalText(t.change, data)}
  `;
  if (!charts[id]) charts[id] = initChart(id);
  drawChart(charts[id].ctx, data, charts[id].canvas.width, charts[id].canvas.height);
}
function signalText(change, data) {
  const rsi = data.rsi?.[data.rsi.length-1];
  if (rsi && rsi < 30) return '<div class="signal buy">🔔 RSI超卖信号 — 考虑买入</div>';
  if (rsi && rsi > 70) return '<div class="signal sell">🔔 RSI超买信号 — 考虑卖出</div>';
  if (change < -5) return '<div class="signal buy">📉 急跌 — 关注反弹买入</div>';
  if (change > 5) return '<div class="signal wait">📈 急涨 — 关注回调风险</div>';
  return '<div class="signal wait">⚪ 观望 — 等待信号</div>';
}
async function refresh() {
  try {
    const r = await fetch('/api/data'); const d = await r.json();
    if (d.sol) updateCard('solCard', 'sol', d.sol);
    if (d.btc) updateCard('btcCard', 'btc', d.btc);
    if (d.eth) updateCard('ethCard', 'eth', d.eth);
  } catch(e) {}
  document.getElementById('clock').textContent = new Date().toLocaleTimeString('zh-CN');
}
setInterval(refresh, 5000);
refresh();
</script>
</body>
</html>"""

if __name__ == "__main__":
    threading.Thread(target=updater, daemon=True).start()
    print(f"📊 交易大屏: http://127.0.0.1:{PORT}")
    socketserver.TCPServer(("0.0.0.0", PORT), Handler).serve_forever()
