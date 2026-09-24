import json
import random
import time
from datetime import datetime
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Referer": "https://hgnice.biz",
}

RED = "\033[31m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
RESET = "\033[0m"


def print_line(text: str, color: str = GREEN) -> None:
    print(f"{color}{text}{RESET}")


def print_banner() -> None:
    print_line("", color=CYAN)
    print_line("🎯  ALPHA PREDICTOR v1.0", color=CYAN)
    print_line("", color=CYAN)


def print_status(label: str, value: str, color: str = CYAN) -> None:
    print_line(f"{label:<8} ➜ {value}", color=color)

def get_result_type(num: int) -> str:
    return "BIG" if num >= 5 else "SMALL"


def get_number_color(num: int) -> str:
    if num in (0, 5):
        return "VIOLET"
    if num in (1, 3, 7, 9):
        return "GREEN"
    return "RED"


def get_number_predictions(history: List[Dict[str, Any]], trend: str) -> tuple[int, int]:
    """Return two recent-frequency numbers matching the descriptive trend."""
    nums = []
    for item in history[:10]:
        try:
            n = int(item.get("number"))
        except (TypeError, ValueError):
            continue
        if 0 <= n <= 9:
            nums.append(n)

    if not nums:
        picks = random.sample(range(10), 2)
        return picks[0], picks[1]

    candidates = [n for n in nums if get_result_type(n) == trend]
    if len(set(candidates)) < 2:
        candidates = nums

    counts = {n: candidates.count(n) for n in set(candidates)}
    ranked = sorted(counts, key=lambda n: (-counts[n], nums.index(n)))
    unique = []
    for n in ranked:
        if n not in unique:
            unique.append(n)
        if len(unique) == 2:
            break

    if len(unique) < 2:
        for n in range(10):
            if n not in unique and (get_result_type(n) == trend or len(unique) == 0):
                unique.append(n)
            if len(unique) == 2:
                break

    return unique[0], unique[1]


def get_trend_signal(history: List[Dict[str, Any]], window: int = 10) -> tuple[str, int]:
    """Calculate a simple descriptive BIG/SMALL trend from recent completed results."""
    types = []
    for item in history[:window]:
        value = item.get("number")
        try:
            num = int(value)
        except (TypeError, ValueError):
            continue
        if 0 <= num <= 9:
            types.append(get_result_type(num))

    if not types:
        return "NEUTRAL", 0

    big_count = types.count("BIG")
    small_count = types.count("SMALL")
    strength = round(max(big_count, small_count) / len(types) * 100)

    if big_count > small_count:
        return "BIG", strength
    if small_count > big_count:
        return "SMALL", strength
    return "NEUTRAL", 50


def fetch_latest() -> List[Dict[str, Any]]:
    url = f"{API_URL}?ts={int(time.time() * 1000)}"
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = response.read().decode("utf-8")
        data = json.loads(payload)
        return data.get("data", {}).get("list", []) or []
    except (urllib.error.URLError, ValueError, TimeoutError, json.JSONDecodeError) as exc:
        print_line(f"[ERROR] Failed to fetch history: {exc}")
        return []


def stable_random_prediction(prev_prediction: Optional[str], trend_bias: str) -> tuple[str, str]:
    choice = "BIG" if random.random() > 0.5 else "SMALL"
    if random.random() < 0.65:
        choice = trend_bias
    if prev_prediction and choice == prev_prediction and random.random() < 0.5:
        choice = "SMALL" if choice == "BIG" else "BIG"
    if random.random() < 0.2:
        trend_bias = "SMALL" if trend_bias == "BIG" else "BIG"
    return choice, trend_bias


def wait_for_result(target_period: str, poll_interval: float = 2.0, max_attempts: int = 90) -> Dict[str, Any]:
    for _ in range(max_attempts):
        time.sleep(poll_interval)
        history = fetch_latest()
        if not history:
            continue

        latest = history[0]
        issue = str(latest.get("issueNumber") or latest.get("issue") or "")
        number = latest.get("number")
        if issue == str(target_period) and number not in (None, "", "-"):
            return {"found": True, "number": int(number), "raw": latest}

    return {"found": False}


spin_count = 0


def run_cycle(prev_prediction: Optional[str], trend_bias: str) -> tuple[Optional[str], str, bool]:
    global spin_count
    spin_count += 1
    print_banner()
    print_status("🕒 TIME", datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"), color=CYAN)
    print_status("🌐 STATUS", "🟢 CONNECTED", color=GREEN)

    history = fetch_latest()
    if not history:
        print_status("⚠️ ALERT", "❌ Failed to fetch data. Retrying...", color=RED)
        return prev_prediction, trend_bias, False

    last_finished = str(history[0].get("issueNumber") or history[0].get("issue") or "0")
    current_period = str(int(last_finished) + 1)

    prediction, trend_bias = stable_random_prediction(prev_prediction, trend_bias)
    trend, trend_strength = get_trend_signal(history)
    predicted_number_1, predicted_number_2 = get_number_predictions(history, trend)

    print_status("🎰 SPIN", f"#{spin_count:03d}", color=CYAN)
    print_status("🔢 PERIOD", current_period, color=CYAN)
    print_status("🕒 TIME", datetime.now().strftime("%I:%M:%S %p"), color=CYAN)

    if trend == "BIG":
        trend_emoji = "📈"
    elif trend == "SMALL":
        trend_emoji = "📉"
    else:
        trend_emoji = "➖"

    print_status("📊 TREND", f"{trend_emoji} {trend}", color=MAGENTA)
    print_status("📈 STRENGTH", f"{trend_strength}%", color=MAGENTA)

    signal_emoji = "🔴" if prediction == "SMALL" else "🟢"
    print_status("🎯 SIGNAL", f"{signal_emoji} {prediction}", color=YELLOW)
    colour_1 = get_number_color(predicted_number_1)
    colour_2 = get_number_color(predicted_number_2)
    print_status(
        "🔢 NUMBERS",
        f"🎯 {predicted_number_1} ({colour_1}) / {predicted_number_2} ({colour_2})",
        color=CYAN,
    )
    print_status("🎲 RESULT", "🟡 WAITING", color=YELLOW)

    result = wait_for_result(current_period)
    if result["found"]:
        actual_num = result["number"]
        actual_type = get_result_type(actual_num)
        win = actual_type == prediction
        number_hit = actual_num in (predicted_number_1, predicted_number_2)

        result_emoji = "🔴" if actual_type == "SMALL" else "🟢"
        number_colour = get_number_color(actual_num)
        print_status("🎲 RESULT", f"{result_emoji} {actual_type}", color=GREEN)
        print_status("🔢 ACTUAL", f"{actual_num} ({number_colour})", color=MAGENTA)

        if number_hit:
            print_status("🏆 NUMBER HIT", "🎉🎰💰 JACKPOT! 💰🎰🎉", color=YELLOW)
        else:
            print_status("🏆 NUMBER HIT", "❌ NO HIT", color=RED)

        print_status(
            "🏆 OUTCOME",
            "🟢 WIN ✅" if win else "🔴 LOSS ❌",
            color=GREEN if win else RED,
        )
    else:
        print_status("🎲 RESULT", "🟡 WAITING", color=YELLOW)
        print_status("📌 OUTCOME", "⏳ PENDING", color=YELLOW)

    return prediction, trend_bias, True


def main() -> None:
    prev_prediction: Optional[str] = None
    trend_bias = "BIG" if random.random() > 0.5 else "SMALL"

    try:
        while True:
            prev_prediction, trend_bias, _ = run_cycle(prev_prediction, trend_bias)
            time.sleep(3)
    except KeyboardInterrupt:
        print_line("", color=RED)
        print_status("🛑 EXIT", "👋 Stopped by user.", color=RED)


if __name__ == "__main__":
    main()
