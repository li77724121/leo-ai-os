import os, time, json, hmac, base64, logging, signal, sys, ssl, requests
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime
from dotenv import load_dotenv
import config

# ── 配置 ──────────────────────────────────────────
SOL_GRID_LOW = config.SOL_GRID_LOW
SOL_GRID_HIGH = config.SOL_GRID_HIGH
GRID_LEVELS = config.GRID_LEVELS
TRADE_USDT_PER_GRID = config.TRADE_USDT_PER_GRID
CHECK_INTERVAL = config.CHECK_INTERVAL
LOG_FILE = config.LOG_FILE
GRID_PRICES = config.GRID_PRICES
STOP_LOSS = config.STOP_LOSS
MAX_POSITION_USDT = config.MAX_POSITION_USDT
TAKE_PROFIT = config.TAKE_PROFIT
# 安全开关（真正生效！）
DRY_RUN = config.DRY_RUN
LIVE_TRADING_ENABLED = config.LIVE_TRADING_ENABLED

# ── 初始化 ──────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv('OKX_API_KEY')
SECRET = os.getenv('OKX_SECRET_KEY')
PASSPHRASE = os.getenv('OKX_PASSPHRASE')

# 代理配置 (urllib自动读取小写env var)
PROXY = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy') or ''
if PROXY:
    os.environ['https_proxy'] = PROXY
    os.environ['http_proxy'] = PROXY.replace('https://', 'http://') if 'https://' in PROXY else PROXY

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger("GridBot")

# Telegram 通知
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_alert(msg):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
                timeout=5
            )
        except:
            pass  # 静默失败

# 风控：止损/止盈检查
def check_risk_control(price):
    """检查是否触发止损或止盈"""
    try:
        orders = get_open_orders()
        for o in orders:
            px = float(o.get("px", 0))
            side = o.get("side", "")
            if not px or not side:
                continue
            if side == "buy":
                loss_pct = (px - price) / px
                if loss_pct >= STOP_LOSS:
                    logger.warning(f"🛑 触发止损: {side}单 @ ${px:.2f}, 当前价 ${price:.2f}, 跌幅 {loss_pct:.2%}")
                    send_alert(f"🛑 止损触发: SOL ${price:.2f}, 买单 ${px:.2f} 跌幅 {loss_pct:.2%}")
                    cancel_order_with_retry(o["ordId"])
            elif side == "sell":
                profit_pct = (price - px) / px
                if profit_pct >= TAKE_PROFIT:
                    logger.info(f"✅ 触发止盈: {side}单 @ ${px:.2f}, 当前价 ${price:.2f}, 涨幅 {profit_pct:.2%}")
                    send_alert(f"✅ 止盈触发: SOL ${price:.2f}, 卖单 ${px:.2f} 涨幅 {profit_pct:.2%}")
                    cancel_order_with_retry(o["ordId"])
    except Exception as e:
        logger.error(f"风控检查异常: {e}")

# 网格价格
ORDER_AMOUNT = TRADE_USDT_PER_GRID / GRID_PRICES[0]  # SOL数量 (基于最低价计算)

def sign_request(method, path, query=None, body=None):
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
    qs = urlencode(query) if query else ''
    request_path = f"{path}?{qs}" if qs else path
    body_str = json.dumps(body) if body else ''
    msg = timestamp + method + request_path + body_str
    sig = base64.b64encode(hmac.new(SECRET.encode(), msg.encode(), 'sha256').digest()).decode()
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": sig,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json",
    }

def okx_get(path, query=None):
    headers = sign_request("GET", path, query)
    headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    url = "https://www.okx.com" + path
    if query:
        url += "?" + urlencode(query)
    ctx = ssl._create_unverified_context()
    req = Request(url, headers=headers, method="GET")
    with urlopen(req, timeout=10, context=ctx) as r:
        return json.loads(r.read())

def okx_post(path, body):
    headers = sign_request("POST", path, body=body)
    headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    body_json = json.dumps(body)
    url = "https://www.okx.com" + path
    ctx = ssl._create_unverified_context()
    req = Request(url, data=body_json.encode(), headers=headers, method="POST")
    with urlopen(req, timeout=10, context=ctx) as r:
        return json.loads(r.read())

def get_price():
    """获取SOL现货价"""
    resp = okx_get("/api/v5/market/ticker", {"instId": "SOL-USDT"})
    return float(resp["data"][0]["last"])

def get_open_orders():
    """获取当前挂单"""
    resp = okx_get("/api/v5/trade/orders-pending", {"instId": "SOL-USDT"})
    return resp.get("data", [])


# 成交监控状态
_fill_state = {"last_ids": set(), "last_count": 0, "init": False}

def check_fills():
    """检测挂单变化 → 推断成交并 Telegram 提醒
    策略: 记录上次挂单ID集合, 若当前集合变小说明有订单消失(成交/撤单)
    配合价格方向判断买卖方向
    """
    global _fill_state
    try:
        orders = get_open_orders()
        cur_ids = {o["ordId"] for o in orders}
        cur_count = len(cur_ids)

        if _fill_state["init"]:
            # 消失的订单 = 可能成交
            vanished = _fill_state["last_ids"] - cur_ids
            # 新增订单 = 重建网格 (不算成交)
            if vanished and cur_count < _fill_state["last_count"]:
                # 查最近成交历史确认方向
                try:
                    resp = okx_get("/api/v5/trade/orders-history",
                                   {"instType": "SPOT", "instId": "SOL-USDT", "limit": "3"})
                    filled = [o for o in resp.get("data", [])
                              if o.get("state") == "filled"]
                    if filled:
                        o = filled[0]
                        side = o["side"]
                        px = float(o.get("avgPx") or o.get("px") or 0)
                        sz = float(o.get("accFillSz") or 0)
                        fee = float(o.get("fee") or 0)
                        icon = "🟢 买入" if side == "buy" else "🔴 卖出"
                        msg = (f"{icon} SOL 成交! @ ${px:.2f} x {sz:.4f} SOL "
                               f"(≈${px*sz:.2f}) | 手续费 {abs(fee):.4f} {o.get('feeCcy','')}")
                        logger.info(f"💹 {msg}")
                        send_alert(f"{msg}")
                except Exception as e:
                    logger.warning(f"  ⚠️ 成交详情查询失败: {e}")

        _fill_state["last_ids"] = cur_ids
        _fill_state["last_count"] = cur_count
        _fill_state["init"] = True
    except Exception as e:
        logger.warning(f"  ⚠️ 成交监控异常: {e}")

def cancel_order(ord_id):
    """撤销订单"""
    if DRY_RUN:
        logger.info(f"🧪 [DRY RUN] 模拟撤单 {ord_id} (未真实操作)")
        return True
    if not LIVE_TRADING_ENABLED:
        logger.warning(f"⛔ 实盘未启用，拒绝撤单 {ord_id}")
        return False
    resp = okx_post("/api/v5/trade/cancel-order", {
        "instId": "SOL-USDT",
        "ordId": ord_id
    })
    return resp.get("code") == "0"

def place_limit_order(side, price):
    """挂限价单 (buy/sell) - 根据价格计算数量"""
    sz = round(TRADE_USDT_PER_GRID / price, 4)
    if sz < 0.01:
        sz = 0.01
    
    if DRY_RUN:
        logger.info(f"🧪 [DRY RUN] 模拟{side}单 @ ${price:.2f} x {sz} SOL (未真实下单)")
        return {"code": "0", "dry_run": True}
    
    if not LIVE_TRADING_ENABLED:
        logger.warning(f"⛔ 实盘未启用，拒绝真实{side}单 @ ${price:.2f}")
        return {"code": "blocked", "msg": "LIVE_TRADING_ENABLED is False"}
    
    resp = okx_post("/api/v5/trade/order", {
        "instId": "SOL-USDT",
        "tdMode": "cash",
        "side": side,
        "ordType": "limit",
        "px": str(round(price, 2)),
        "sz": str(sz)
    })
    return resp

def get_position_size():
    """获取当前已挂单的 USDT 市值总和"""
    try:
        orders = get_open_orders()
        total_usdt = 0
        for o in orders:
            px = float(o.get("px", 0))
            sz = float(o.get("sz", 0))
            total_usdt += px * sz
        return total_usdt
    except:
        return 0

def retry_on_failure(func, retries=3, delay=1):
    """通用重试机制"""
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            logger.warning(f"⚠️ 尝试 {attempt+1}/{retries} 失败: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    logger.error(f"❌ 达到最大重试次数 ({retries}) - 操作失败")
    raise

# 带重试的包装函数
def get_price_with_retry():
    return retry_on_failure(lambda: get_price(), retries=3, delay=1)

def get_open_orders_with_retry():
    return retry_on_failure(lambda: get_open_orders(), retries=3, delay=1)

def okx_get_with_retry(path, query=None):
    return retry_on_failure(lambda: okx_get(path, query), retries=3, delay=1)

def okx_post_with_retry(path, body):
    return retry_on_failure(lambda: okx_post(path, body), retries=3, delay=1)

def cancel_order_with_retry(ord_id):
    return retry_on_failure(lambda: cancel_order(ord_id), retries=3, delay=1)

def place_limit_order_with_retry(side, price):
    return retry_on_failure(lambda: place_limit_order(side, price), retries=3, delay=1)

def should_restart_grid():
    """检查是否需要重启网格
    关键: 只有"实际挂单数 < 当前资金可支持的层数"才重建
    (SOL不足/USDT不足导致跳过的层不算缺失, 避免无限重建)
    """
    orders = get_open_orders()
    current_position = get_position_size()
    if current_position >= config.MAX_POSITION_USDT:
        logger.info(f"⚠️ 已达最大持仓限制 ({config.MAX_POSITION_USDT} USDT >= {current_position:.2f} USDT)，暂停开新网格")
        send_alert(f"⚠️ 网格暂停: 已达最大持仓限制 {config.MAX_POSITION_USDT} USDT")
        return False

    if not orders:
        return True

    # 当前价 (用于判断哪些层该挂)
    try:
        price = get_price()
    except Exception:
        return False  # 拿不到价不折腾

    # 计算当前资金能支持多少层
    try:
        bal_resp = okx_get("/api/v5/account/balance", {"ccy": "SOL"})
        sol_avail = 0.0
        for det in bal_resp.get("data", [{}])[0].get("details", []):
            if det.get("ccy") == "SOL":
                sol_avail = float(det.get("availBal", 0))
    except Exception:
        sol_avail = 99.0

    sell_possible = int(sol_avail / ORDER_AMOUNT) if ORDER_AMOUNT > 0 else 0
    buy_possible = 999  # USDT 充足, 不限制

    # 理论上该挂的层数
    expected_count = 0
    for gp in GRID_PRICES:
        if gp < price and buy_possible > 0:
            expected_count += 1
        elif gp > price and sell_possible > 0:
            expected_count += 1
            sell_possible -= 1  # 每个卖单消耗一个 SOL 份额

    # 已有挂单数 >= 可挂层数 → 网格完整, 不重建
    if len(orders) >= expected_count:
        return False

    # 有缺层才重建
    existing_prices = set(round(float(o.get("px", 0)), 2) for o in orders)
    expected = set(round(p, 2) for p in GRID_PRICES)
    missing = expected - existing_prices
    return len(missing) > 0

def build_grid():
    """重建网格：撤销旧单 → 根据当前价挂新单"""
    logger.info("🔄 重建网格...")
    
    # 0. 风控检查
    current_position = get_position_size()
    if current_position >= config.MAX_POSITION_USDT:
        logger.warning(f"⛔ 超过最大仓位限制 ({config.MAX_POSITION_USDT} USDT)，取消建网格")
        send_alert(f"⛔ 风控拦截: 超过最大仓位限制 {config.MAX_POSITION_USDT} USDT，取消建网格")
        return 0
    
    # 1. 撤销所有旧挂单
    orders = get_open_orders()
    for o in orders:
        cancel_order_with_retry(o["ordId"])
    logger.info(f"✅ 撤销 {len(orders)} 个旧单")
    
    # 2. 获取当前价
    price = get_price_with_retry()
    logger.info(f"📊 SOL当前价: ${price:.2f}")
    send_alert(f"📊 网格重建: SOL ${price:.2f} | 建 {GRID_LEVELS} 层")
    
    # 3. 挂单策略
    buy_count = sell_count = 0
    # 查询实际 SOL 可用量, 限制卖单数量 (避免超持冻结失败)
    try:
        bal_resp = okx_get("/api/v5/account/balance", {"ccy": "SOL"})
        sol_avail = 0.0
        for det in bal_resp.get("data", [{}])[0].get("details", []):
            if det.get("ccy") == "SOL":
                sol_avail = float(det.get("availBal", 0))
        logger.info(f"📦 SOL 可用: {sol_avail:.4f}")
    except Exception:
        sol_avail = 99.0  # 查不到则不限制

    sell_needed = sum(1 for gp in GRID_PRICES if gp > price)
    sell_possible = int(sol_avail / ORDER_AMOUNT)  # 可用SOL能支撑几个卖单

    for gp in GRID_PRICES:
        if gp < price:
            r = place_limit_order_with_retry("buy", gp)
            if r.get("code") == "0":
                buy_count += 1
                logger.info(f"  ✅ 挂买单 @ ${gp:.2f}")
            else:
                logger.warning(f"  ❌ 买单失败 @ ${gp:.2f}: {r.get('msg')}")
        elif gp > price:
            if sell_count >= sell_possible:
                logger.warning(f"  ⏭️ 跳过卖单 @ ${gp:.2f}: 可用SOL不足 ({sol_avail:.4f})")
                continue
            r = place_limit_order_with_retry("sell", gp)
            if r.get("code") == "0":
                sell_count += 1
                logger.info(f"  ✅ 挂卖单 @ ${gp:.2f}")
            else:
                logger.warning(f"  ❌ 卖单失败 @ ${gp:.2f}: {r.get('msg')}")
    
    logger.info(f"📈 网格完成: {buy_count}买单 + {sell_count}卖单")
    send_alert(f"📈 网格就绪: {buy_count}买单 + {sell_count}卖单 | 等待成交...")
    return buy_count + sell_count

def monitor():
    """主循环：监控并维护网格"""
    logger.info("=" * 50)
    logger.info("🚀 SOL网格交易机器人启动")
    logger.info(f"📊 网格范围: ${SOL_GRID_LOW} - ${SOL_GRID_HIGH} ({GRID_LEVELS}层)")
    logger.info(f"💵 每层: {TRADE_USDT_PER_GRID} USDT = {round(ORDER_AMOUNT, 4)} SOL")
    logger.info("=" * 50)
    
    while True:
        try:
            price = get_price_with_retry()
            
            # 风控检查
            check_risk_control(price)
            
            # 成交监控 (每笔成交 Telegram 提醒)
            check_fills()
            
            if should_restart_grid():
                count = build_grid()
                logger.info(f"⏳ 网格就绪 ({count}个挂单)，等待成交...")
            else:
                orders = get_open_orders()
                logger.info(f"📊 SOL=${price:.2f} | 挂单: {len(orders)}个 | 持仓: ${get_position_size():.2f} USDT")
            
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            logger.info("🛑 收到停止信号")
            break
        except Exception as e:
            logger.error(f"⚠️ 异常: {type(e).__name__}: {e}")
            send_alert(f"⚠️ 交易异常: {type(e).__name__}: {e}")
            time.sleep(30)

if __name__ == "__main__":
    if not all([API_KEY, SECRET, PASSPHRASE]):
        logger.error("❌ OKX API凭证不完整")
        sys.exit(1)
    monitor()