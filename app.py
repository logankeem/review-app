from flask import Flask, render_template_string, request
import os
import random
import re

app = Flask(__name__)

HTML_PAGE = """
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>리뷰 답변 생성기</title>
<style>
  body{background:#0b1020;color:#fff;font-family:system-ui;margin:0}
  .wrap{max-width:860px;margin:0 auto;padding:20px}
  h1{font-size:22px;margin:0 0 10px}
  .sub{color:#a8b3d6;font-size:13px;margin:0 0 14px;line-height:1.5}
  textarea,select{width:100%;padding:12px;border-radius:12px;border:1px solid rgba(255,255,255,.10);margin-top:8px;background:#111a33;color:#fff}
  button{padding:12px;border-radius:12px;border:none;font-weight:900;margin-top:10px;cursor:pointer}
  .primary{background:#3b82f6;color:#fff;width:100%}
  .grid{display:grid;grid-template-columns:1fr;gap:12px;margin-top:14px}
  .card{background:#111a33;border:1px solid rgba(255,255,255,.10);padding:14px;border-radius:14px;line-height:1.7}
  .head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}
  .tag{font-size:12px;color:#cfe1ff;background:rgba(59,130,246,.14);border:1px solid rgba(59,130,246,.22);padding:6px 10px;border-radius:999px}
  .copyBtn{background:#1f2937;color:#fff;padding:8px 10px;font-size:13px;border-radius:999px}
  .muted{color:#a8b3d6;font-size:12px}
</style>
</head>
<body>
<div class="wrap">
  <h1>리뷰 답변 생성기</h1>
  <p class="sub">리뷰 넣고 “답변 3개” 받기 (기본형 / 공감+사과형 / 해결+재방문형)</p>

  <form method="POST">
    <textarea name="review" placeholder="예) 음식은 맛있는데 배달이 늦었어요. 다음엔 빨랐으면 좋겠네요.">{{ review_value or "" }}</textarea>

    <select name="tone">
      <option value="정중" {{ "selected" if tone=="정중" else "" }}>정중</option>
      <option value="친근" {{ "selected" if tone=="친근" else "" }}>친근</option>
      <option value="사과" {{ "selected" if tone=="사과" else "" }}>사과</option>
      <option value="단호" {{ "selected" if tone=="단호" else "" }}>단호</option>
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
    <div class="muted">팁: 1점/클레임 리뷰면 ‘공감+사과형’이나 ‘해결+재방문형’이 제일 무난함.</div>
  </div>
  {% endif %}
</div>
</body>
</html>
"""

def detect_topics(review: str):
    r = review.lower()
    topics = set()
    if any(k in r for k in ["맛", "맛있", "싱겁", "짜", "음식", "간"]):
        topics.add("taste")
    if any(k in r for k in ["배달", "늦", "시간", "오래", "도착"]):
        topics.add("delivery")
    if any(k in r for k in ["불친절", "친절", "응대", "서비스", "직원", "사장"]):
        topics.add("service")
    if any(k in r for k in ["양", "적", "많", "푸짐", "가성비", "가격", "비싸", "싸"]):
        topics.add("value")
    if any(k in r for k in ["위생", "더럽", "청결", "머리카락", "냄새"]):
        topics.add("clean")
    if any(k in r for k in ["최고", "만족", "또", "재주문", "단골"]):
        topics.add("praise")
    return list(topics)

def tone_open_close(tone: str):
    # 톤별 시작/마무리 문장 (과장 줄이고 자연스럽게)
    openings = {
        "정중": ["리뷰 남겨주셔서 감사합니다.", "소중한 후기 감사합니다."],
        "친근": ["리뷰 고마워요! 😊", "후기 남겨주셔서 감사해요!"],
        "사과": ["불편을 드려 죄송합니다.", "기대에 못 미쳐 죄송합니다."],
        "단호": ["의견 남겨주셔서 감사합니다.", "말씀 주신 내용 확인했습니다."]
    }
    closings = {
        "정중": ["다음에는 더 만족드릴 수 있도록 준비하겠습니다.", "앞으로도 더 신경 써서 운영하겠습니다."],
        "친근": ["다음엔 더 만족하게 해드릴게요! 🙏", "다음 주문도 잘 챙길게요!"],
        "사과": ["같은 불편이 없도록 바로 개선하겠습니다.", "다음에는 꼭 더 나은 경험 드리겠습니다."],
        "단호": ["말씀 주신 부분은 기준에 맞게 점검하겠습니다.", "재발 방지를 위해 내부적으로 확인하겠습니다."]
    }
    return random.choice(openings.get(tone, openings["정중"])), random.choice(closings.get(tone, closings["정중"]))

def topic_sentences(topics):
    # 주제별 문장 후보 (구린 말투 제거, 실제 사장님 답변 느낌)
    pool = []

    if "praise" in topics:
        pool += [
            "만족하셨다니 정말 다행입니다.",
            "좋게 봐주셔서 큰 힘이 됩니다.",
        ]
    if "taste" in topics:
        pool += [
            "맛 관련해서는 늘 일정하게 나갈 수 있게 조리 과정을 점검하고 있습니다.",
            "말씀 주신 부분은 레시피/간 조절을 다시 확인해보겠습니다.",
        ]
    if "delivery" in topics:
        pool += [
            "배달이 지연된 점은 정말 죄송합니다.",
            "피크 시간대에는 준비/배달 동선을 더 촘촘히 관리하겠습니다.",
        ]
    if "service" in topics:
        pool += [
            "응대에서 불편을 느끼셨다면 저희 책임입니다.",
            "직원 교육을 다시 하고 같은 일이 없도록 하겠습니다.",
        ]
    if "value" in topics:
        pool += [
            "양/가격에 대한 의견도 꼼꼼히 반영하겠습니다.",
            "구성은 더 만족스럽게 보완할 수 있도록 검토하겠습니다.",
        ]
    if "clean" in topics:
        pool += [
            "위생 관련 지적은 가장 우선으로 확인하겠습니다.",
            "조리/포장 과정 전체를 다시 점검하고 재발 방지하겠습니다.",
        ]

    if not pool:
        pool = [
            "남겨주신 내용은 꼼꼼히 확인하겠습니다.",
            "다음 이용 때 더 만족하실 수 있도록 보완하겠습니다.",
        ]

    return pool

def build_reply(review: str, tone: str, length: str, style: str):
    topics = detect_topics(review)
    open_s, close_s = tone_open_close(tone)
    pool = topic_sentences(topics)

    # 길이별 문장 수
    target = {"짧게": 3, "보통": 5, "길게": 7}.get(length, 5)

    # 스타일별 구성
    mid = []

    if style == "basic":
        # 기본형: 감사 + 핵심 1~2개 + 마무리
        random.shuffle(pool)
        mid = pool[: max(1, target - 2)]

    elif style == "empathy":
        # 공감+사과형: 공감/사과 문장을 우선
        empathy = [
            "말씀 주신 부분 충분히 이해합니다.",
            "불편하셨을 상황이라 생각합니다.",
            "기대하신 만큼 못 챙겨드린 점 죄송합니다.",
        ]
        random.shuffle(empathy)
        random.shuffle(pool)
        mid = empathy[:2] + pool[: max(1, target - 4)]

        # 사과 톤이 아니어도 공감형에서는 사과 한 번은 들어가게
        if tone != "사과":
            mid.insert(1, "불편을 드린 점은 죄송하게 생각합니다.")

    else:  # solution
        # 해결+재방문형: 조치/개선/재방문 유도
        solution = [
            "바로 점검하고 개선하겠습니다.",
            "다음 주문에는 더 신경 써서 준비하겠습니다.",
            "혹시 다음에도 같은 문제가 생기면 말씀 주시면 빠르게 도와드리겠습니다.",
        ]
        random.shuffle(solution)
        random.shuffle(pool)
        mid = pool[:2] + solution[:2]
        # 너무 길면 줄이기
        mid = mid[: max(1, target - 2)]

    # 조립
    sentences = [open_s] + mid + [close_s]
    sentences = sentences[:target]
    return " ".join(sentences)

@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    review_value = ""
    tone = "정중"
    length = "보통"

    if request.method == "POST":
        review_value = (request.form.get("review") or "").strip()
        tone = request.form.get("tone") or "정중"
        length = request.form.get("length") or "보통"

        if review_value:
            r1 = build_reply(review_value, tone, length, "basic")
            r2 = build_reply(review_value, tone, length, "empathy")
            r3 = build_reply(review_value, tone, length, "solution")
            results = [
                {"title": "기본형", "text": r1},
                {"title": "공감+사과형", "text": r2},
                {"title": "해결+재방문형", "text": r3},
            ]

    return render_template_string(
        HTML_PAGE,
        results=results,
        review_value=review_value,
        tone=tone,
        length=length
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    app.run(host="0.0.0.0", port=port)
