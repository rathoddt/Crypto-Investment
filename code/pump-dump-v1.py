import requests
import time
from datetime import datetime
import winsound
from concurrent.futures import ThreadPoolExecutor

BINANCE_FAPI = "https://fapi.binance.com"


def play_alert_sound():
    frequency = 900     # soft beep
    duration = 3000     # 3 seconds

    for _ in range(5):  # beep 5 times
        winsound.Beep(frequency, duration)
        time.sleep(5)   # 5 sec gap


def get_futures_symbols():
    url = f"{BINANCE_FAPI}/fapi/v1/exchangeInfo"
    data = requests.get(url).json()
    return [
        s["symbol"]
        for s in data["symbols"]
        if s["contractType"] == "PERPETUAL" and s["quoteAsset"] == "USDT"
    ]


def get_klines(symbol):
    url = f"{BINANCE_FAPI}/fapi/v1/klines"
    params = {"symbol": symbol, "interval": "1m", "limit": 40}

    try:
        return requests.get(url, params=params, timeout=3).json()
    except:
        return []


def detect(symbol):
    kl = get_klines(symbol)

    if not kl or isinstance(kl, dict):
        return None

    closes = [float(k[4]) for k in kl[-30:]]
    vols = [float(k[5]) for k in kl[-30:]]

    openp = closes[0]
    lastp = closes[-1]

    change = ((lastp - openp) / openp) * 100

    avg_prev = sum(vols[:-5]) / max(1, len(vols[:-5]))
    avg_last = sum(vols[-5:]) / 5
    vol_spike = avg_last > avg_prev * 1.5

    if change >= 10 and vol_spike:
        return f"🚀 PUMP: {symbol} ({change:.2f}%)"

    if change <= -10 and vol_spike:
        return f"🔻 DUMP: {symbol} ({change:.2f}%)"

    return None


def monitor():
    print("Starting fast Binance pump/dump scanner...\n")

    symbols = get_futures_symbols()
    print(f"Loaded {len(symbols)} USDT futures pairs")

    while True:
        start = time.time()
        print(f"\nScanning at {datetime.utcnow()}...\n")

        with ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(detect, symbols))

        signals_found = False

        for res in results:
            if res:
                signals_found = True
                print(res)
                play_alert_sound()

        if not signals_found:
            print("None")   # <-- PRINT NONE EVERY MINUTE

        elapsed = time.time() - start
        wait = max(0, 60 - elapsed)  # maintain 1-minute cycle
        time.sleep(wait)


if __name__ == "__main__":
    monitor()
