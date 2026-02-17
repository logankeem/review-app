from flask import Flask, render_template_string, request
import os
import random
import re
from datetime import datetime

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>리뷰 답변 생성기</title>
<style>
  body{background:#0b1020;color:#fff;font-family:system-ui;margin:0}
  .wrap{max-width:900px;margin:0 auto;padding:20px}
  h1{font-size:22px;margin:0 0 14px}
  textarea,select{width:100%;padding:12px;border-radius:12px;border:1px solid rgba(255,255,255,.10);margin-top:8px;background:#111a33;color:#fff}
  button{padding:12px;border-radius:12px;border:none;font-weight:900;margin-top:10px;cursor:pointer}
  .primary{background:#3b82f6;color:#fff;width:100%}
  .grid{display:grid;grid-template-columns:1fr;gap:12px;margin-top:14px}
  .card{background:#111a33;border:1px solid rgba(255,255,255,.10);padding:14px;border-radius:14px;line-height:1.75}
  .head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}
  .tag{font-size:12px;color:#cfe1ff;background:rgba(59,130,246,.14);border:1px solid rgba(59,130,246,.22);padding:6px 10px;border-radius:999px}
  .copyBtn{background:#1f2937;color:#fff;padding:8px 10px;font-size:13px;border-radius:999px}
  .meta{margin-top:10px;color:#a8b3d6;font-size:12px}
</style>
</head>
<body>
<div class="wrap">
  <h1>리뷰 답변 생성기</h1>

  <form method="POST">
    <textarea name="review" placeholder="예) 진짜 맛있어요! 포장도 깔끔하고 또 시킬게요 / 배달이 늦고 식어서 왔어요" required>{{ review or "" }}</textarea>

    <select name="tone">
      <option value="정중" {{ "selected" if tone=="정중" else "" }}>정중</option>
      <option value="친근" {{ "selected" if tone=="친근" else "" }}>친근</option>
      <option value="사과" {{ "selected" if tone=="사과" else "" }}>사과(부정 리뷰용)</option>
      <option value="단호" {{ "selected" if tone=="단호" else "" }}>단호(무리한 요구/악성 느낌)</option>
    </select>

    <select name="length">
      <option value="짧게" {{ "selected" if length=="짧게" else "" }}>짧게</option>
      <option value="보통" {{ "selected" if length=="보통" else "" }}>보통</option>
      <option value="길게" {{ "selected" if length=="길게" else "" }}>길게</option>
    </select>

    <button class="primary" type="submit">답변 3개 생성</button>
  </form>

  {% if results %}
  <div class="grid">
    {% for r in results %}
      <div class="card">
        <div class="head">
          <div class="tag">{{ r.title }}</div>
          <button class="copyBtn" onclick="navigator.clipboard.writeText(`{{ r.text }}`)">복사</button>
        </div>
        <div>{{ r.text }}</div>
      </div>
    {% endfor %}
    <div class="meta">{{ stamp }}</div>
  </div>
  {% endif %}
</div>
</body>
</html>
"""

# ----------------------------
# 감정 판정 (오판정 줄이기)
# ----------------------------
STRONG_POS = ["최고", "대박", "강추", "추천", "미쳤", "존맛", "맛있", "완전좋", "너무좋", "만족", "재주문", "또시킬", "또 시킬", "단골"]
POS_WORDS = ["좋", "괜찮", "만족", "감사", "친절", "빠르", "깔끔", "재주문", "또", "추천", "맛있", "굿", "짱"]

STRONG_NEG = ["최악", "실망", "환불", "사기", "불친절", "머리카락", "곰팡", "상했", "썩", "배탈", "신고"]
NEG_WORDS = ["별로", "불만", "클레임", "늦", "지연", "차갑", "식었", "누락", "오배송", "잘못", "더럽", "냄새", "비싸", "적", "짜증", "엉망"]

def score_keywords(text: str, words):
    t = text.lower()
    return sum(1 for w in words if w in t)

def classify_sentiment(text: str):
    t = text.lower()
    pos_score = score_keywords(t, POS_WORDS) + 2 * score_keywords(t, STRONG_POS)
    neg_score = score_keywords(t, NEG_WORDS) + 2 * score_keywords(t, STRONG_NEG)

    if score_keywords(t, STRONG_POS) >= 1 and score_keywords(t, STRONG_NEG) == 0 and neg_score <= 1:
        return "긍정"
    if score_keywords(t, STRONG_NEG) >= 1 and score_keywords(t, STRONG_POS) == 0:
        return "부정"
    if pos_score >= neg_score + 2:
        return "긍정"
    if neg_score >= pos_score + 1:
        return "부정"
    return "중립"

# ----------------------------
# 토픽 감지
# ----------------------------
TOPIC_RULES = {
    "맛": ["맛", "맛있", "싱겁", "짜", "간", "퀄", "퀄리티", "조리", "양념"],
    "배달": ["배달", "늦", "지연", "시간", "오래", "도착", "라이더"],
    "응대": ["불친절", "친절", "응대", "서비스", "직원", "사장", "전화"],
    "가격/양": ["양", "적", "많", "푸짐", "가성비", "가격", "비싸", "싸", "양이"],
    "위생": ["위생", "더럽", "청결", "머리카락", "냄새", "깨끗"],
    "주문오류": ["누락", "빠짐", "오배송", "다름", "잘못", "실수", "빼먹"],
}

def detect_topics(text: str):
    t = text.lower()
    topics = []
    for topic, keys in TOPIC_RULES.items():
        if any(k in t for k in keys):
            topics.append(topic)
    return topics[:3]

# ----------------------------
# 톤/길이
# ----------------------------
LENGTH_SENT_COUNT = {"짧게": 3, "보통": 5, "길게": 7}

OPENINGS = {
    "긍정": {
        "정중": ["소중한 리뷰 남겨주셔서 감사합니다.", "정성스러운 후기 감사합니다."],
        "친근": ["리뷰 남겨주셔서 감사해요! 😊", "후기 너무 고마워요!"],
        "사과": ["후기 남겨주셔서 감사합니다.", "좋은 말씀 감사합니다."],
        "단호": ["리뷰 감사합니다.", "후기 확인했습니다."],
    },
    "중립": {
        "정중": ["리뷰 남겨주셔서 감사합니다.", "후기 감사합니다."],
        "친근": ["리뷰 고마워요! 😊", "후기 감사합니다!"],
        "사과": ["말씀 주셔서 감사합니다.", "후기 확인했습니다."],
        "단호": ["의견 감사합니다.", "확인했습니다."],
    },
    "부정": {
        "정중": ["불편을 드려 죄송합니다.", "기대에 못 미쳐 죄송합니다."],
        "친근": ["불편 드려 정말 죄송해요.", "기분 상하셨을까봐 죄송합니다."],
        "사과": ["불편을 드려 진심으로 죄송합니다.", "정말 죄송합니다. 말씀 주신 내용 바로 확인하겠습니다."],
        "단호": ["말씀 주신 내용 확인했습니다.", "접수된 내용은 확인 중입니다."],
    }
}

CLOSINGS = {
    "긍정": {
        "정중": ["다음에도 만족 드릴 수 있게 잘 준비하겠습니다.", "또 찾아주시면 정성껏 준비하겠습니다."],
        "친근": ["다음에도 맛있게 준비해둘게요! 🙏", "다음 주문도 더 잘 챙길게요!"],
        "사과": ["다음에도 잘 부탁드립니다.", "또 찾아주시면 감사하겠습니다."],
        "단호": ["감사합니다.", "좋은 하루 되세요."],
    },
    "중립": {
        "정중": ["다음에는 더 만족드릴 수 있도록 하겠습니다.", "더 신경 써서 준비하겠습니다."],
        "친근": ["다음엔 더 만족하게 해드릴게요!", "다음에도 잘 부탁드려요!"],
        "사과": ["확인 후 반영하겠습니다.", "더 신경 쓰겠습니다."],
        "단호": ["확인하겠습니다.", "감사합니다."],
    },
    "부정": {
        "정중": ["같은 불편이 없도록 개선하겠습니다.", "다음에는 더 나은 경험 드리겠습니다."],
        "친근": ["다음엔 꼭 더 만족하게 해드릴게요.", "바로 개선해서 다음엔 더 좋게 해드릴게요."],
        "사과": ["같은 일이 없도록 바로 조치하겠습니다.", "다음에는 꼭 더 나아지겠습니다."],
        "단호": ["확인 후 조치하겠습니다.", "필요 시 안내드리겠습니다."],
    }
}

TOPIC_LINES = {
    "긍정": {
        "맛": ["맛있게 드셨다니 정말 다행입니다.", "입맛에 맞으셨다니 기쁩니다."],
        "배달": ["배달도 만족하셨다니 감사합니다.", "빠르게 받아보셨다니 다행이에요."],
        "응대": ["응대도 좋게 봐주셔서 감사합니다.", "친절하게 느끼셨다니 정말 다행입니다."],
        "가격/양": ["구성 만족하셨다니 감사합니다.", "가성비 좋게 느끼셨다니 기쁩니다."],
        "위생": ["깔끔하게 느끼셨다니 다행입니다.", "청결도 신경 쓰고 있습니다. 감사합니다."],
        "주문오류": ["문제 없이 받아보셨다니 다행입니다.", "정확히 전달되어 다행입니다."],
    },
    "중립": {
        "맛": ["맛과 품질은 더 일정하게 유지하겠습니다.", "조리 기준은 꾸준히 점검하겠습니다."],
        "배달": ["배달/준비 흐름은 계속 개선 중입니다.", "피크 시간 운영은 더 매끄럽게 다듬겠습니다."],
        "응대": ["응대 품질도 더 신경 쓰겠습니다.", "안내 방식도 더 친절하게 개선하겠습니다."],
        "가격/양": ["구성은 더 만족스럽게 보완하겠습니다.", "가격 대비 만족도를 높이도록 검토하겠습니다."],
        "위생": ["청결은 꾸준히 점검하고 있습니다.", "위생 관리는 더 꼼꼼히 하겠습니다."],
        "주문오류": ["주문 확인은 더 꼼꼼히 진행하겠습니다.", "포장 전 검수를 강화하겠습니다."],
    },
    "부정": {
        "맛": ["맛/간 부분은 조리 과정을 다시 점검하겠습니다.", "레시피와 조리 기준을 재확인해 개선하겠습니다."],
        "배달": ["지연 원인을 확인하고 동선을 개선하겠습니다.", "피크 시간대 운영을 보완해 지연을 줄이겠습니다."],
        "응대": ["응대는 다시 교육하고 개선하겠습니다.", "불편을 드린 점은 내부적으로 점검하겠습니다."],
        "가격/양": ["구성/양은 다시 검토해보겠습니다.", "가격 대비 만족도를 높이도록 보완하겠습니다."],
        "위생": ["위생은 가장 우선으로 즉시 점검하겠습니다.", "조리/포장 과정 전체를 재점검하겠습니다."],
        "주문오류": ["누락/오배송은 바로 확인하고 재발 방지하겠습니다.", "주문 확인 절차를 강화하겠습니다."],
    }
}

def uniq_pick(pool, used, k):
    candidates = [p for p in pool if p not in used]
    if len(candidates) < k:
        candidates = pool[:]
    random.shuffle(candidates)
    picked = []
    for s in candidates:
        if s not in used:
            picked.append(s)
            used.add(s)
        if len(picked) >= k:
            break
    while len(picked) < k and pool:
        picked.append(random.choice(pool))
    return picked

def build_variants(review: str, tone: str, length: str):
    sentiment = classify_sentiment(review)
    topics = detect_topics(review)
    count = LENGTH_SENT_COUNT.get(length, 5)

    used = set()

    def open_line():
        return random.choice(OPENINGS[sentiment][tone])

    def close_line():
        return random.choice(CLOSINGS[sentiment][tone])

    topic_pool = []
    for tp in topics:
        topic_pool += TOPIC_LINES[sentiment].get(tp, [])
    if not topic_pool:
        if sentiment == "긍정":
            topic_pool = ["좋게 봐주셔서 큰 힘이 됩니다.", "만족하셨다니 정말 다행입니다."]
        elif sentiment == "부정":
            topic_pool = ["말씀 주신 내용은 바로 확인하겠습니다.", "불편이 없도록 재발 방지에 신경 쓰겠습니다."]
        else:
            topic_pool = ["남겨주신 의견은 꼼꼼히 확인하겠습니다.", "다음에는 더 만족하실 수 있도록 하겠습니다."]

    vibe_pos = ["좋은 말씀 감사합니다.", "다음에도 같은 퀄리티로 준비하겠습니다.", "재주문해주시면 더 정성껏 챙기겠습니다."]
    vibe_neg = ["말씀 주신 부분 충분히 이해합니다.", "불편하셨을 상황이라 생각합니다.", "기대하신 만큼 못 챙겨드린 점 죄송합니다."]
    vibe_neu = ["말씀 주신 내용 참고하겠습니다.", "더 나은 운영을 위해 반영하겠습니다."]

    action_pos = ["포장/검수도 더 꼼꼼히 해서 만족도 유지하겠습니다.", "다음 주문도 빠르게 확인하고 정성껏 준비하겠습니다."]
    action_neg = ["해당 내용은 바로 점검하고 개선하겠습니다.", "필요하시면 상황을 확인해 빠르게 도와드리겠습니다."]
    action_neu = ["운영 기준을 더 다듬어 만족도를 높이겠습니다.", "확인 후 개선 가능한 부분은 반영하겠습니다."]

    a = [open_line()]
    a += uniq_pick(topic_pool, used, max(1, count - 2))
    a += [close_line()]
    a = a[:count]

    b = [open_line()]
    if sentiment == "긍정":
        b += uniq_pick(vibe_pos, used, 2 if count >= 5 else 1)
        b += uniq_pick(topic_pool, used, 1)
    elif sentiment == "부정":
        b += uniq_pick(vibe_neg, used, 2 if count >= 5 else 1)
        b += uniq_pick(topic_pool, used, 1)
    else:
        b += uniq_pick(vibe_neu, used, 2 if count >= 5 else 1)
        b += uniq_pick(topic_pool, used, 1)
    b += [close_line()]
    b = b[:count]

    c = [open_line()]
    if sentiment == "긍정":
        c += uniq_pick(action_pos, used, 2 if count >= 5 else 1)
        c += uniq_pick(topic_pool, used, 1)
    elif sentiment == "부정":
        c += uniq_pick(action_neg, used, 2 if count >= 5 else 1)
        c += uniq_pick(topic_pool, used, 2 if count >= 6 else 1)
    else:
        c += uniq_pick(action_neu, used, 2 if count >= 5 else 1)
        c += uniq_pick(topic_pool, used, 1)
    c += [close_line()]
    c = c[:count]

    def join(lines):
        return " ".join([re.sub(r"\s+", " ", s).strip() for s in lines if s.strip()])

    return [
        {"title": "기본형(깔끔)", "text": join(a)},
        {"title": "친근형(감정)", "text": join(b)},
        {"title": "해결형(조치)", "text": join(c)},
    ]

@app.route("/", methods=["GET", "POST"])
def home():
    review = ""
    tone = "정중"
    length = "보통"
    results = []
    stamp = ""

    if request.method == "POST":
        review = (request.form.get("review") or "").strip()
        tone = request.form.get("tone") or "정중"
        length = request.form.get("length") or "보통"

        if review:
            results = build_variants(review, tone, length)
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    return render_template_string(
        HTML,
        review=review,
        tone=tone,
        length=length,
        results=results,
        stamp=stamp
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    app.run(host="0.0.0.0", port=port)
