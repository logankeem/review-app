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
  h1{font-size:26px;margin:0 0 20px;text-align:center}
  textarea,select{width:100%;padding:12px;border-radius:12px;border:1px solid rgba(255,255,255,.10);margin-top:8px;background:#111a33;color:#fff}
  button{padding:12px;border-radius:12px;border:none;font-weight:900;margin-top:12px;cursor:pointer}
  .primary{background:#3b82f6;color:#fff;width:100%}
  .grid{display:grid;grid-template-columns:1fr;gap:14px;margin-top:20px}
  .card{background:#111a33;border:1px solid rgba(255,255,255,.10);padding:16px;border-radius:14px;line-height:1.8}
  .head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
  .tag{font-size:12px;color:#cfe1ff;background:rgba(59,130,246,.14);padding:6px 12px;border-radius:999px}
  .copyBtn{background:#1f2937;color:#fff;padding:8px 12px;font-size:13px;border-radius:999px}
  .meta{margin-top:14px;color:#a8b3d6;font-size:12px;text-align:center}
</style>
</head>
<body>
<div class="wrap">
  <h1>리뷰 답변 생성기</h1>

  <form method="POST">
    <textarea name="review" placeholder="리뷰 내용을 입력하세요" required>{{ review or "" }}</textarea>

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
  </div>
  <div class="meta">{{ stamp }}</div>
  {% endif %}
</div>
</body>
</html>
"""

# --- 감정 판정 ---
STRONG_POS = ["최고", "대박", "강추", "추천", "미쳤", "존맛", "맛있", "완전좋", "너무좋", "만족", "재주문", "또시킬", "단골"]
POS_WORDS = ["좋", "괜찮", "만족", "감사", "친절", "빠르", "깔끔", "재주문", "또", "추천", "맛있"]
STRONG_NEG = ["최악", "실망", "환불", "불친절", "머리카락", "곰팡", "상했"]
NEG_WORDS = ["별로", "불만", "늦", "지연", "차갑", "식었", "누락", "오배송", "잘못", "더럽", "비싸", "엉망"]

def score(text, words):
    t = text.lower()
    return sum(1 for w in words if w in t)

def classify(text):
    pos = score(text, POS_WORDS) + 2*score(text, STRONG_POS)
    neg = score(text, NEG_WORDS) + 2*score(text, STRONG_NEG)
    if pos >= neg + 2:
        return "긍정"
    if neg >= pos + 1:
        return "부정"
    return "중립"

def build(review, tone, length):
    sentiment = classify(review)
    count = {"짧게":3,"보통":5,"길게":7}.get(length,5)

    base = {
        "긍정":["소중한 리뷰 감사합니다.","만족하셨다니 정말 기쁩니다."],
        "중립":["리뷰 남겨주셔서 감사합니다.","말씀 참고하겠습니다."],
        "부정":["불편을 드려 죄송합니다.","말씀 주신 부분 확인하겠습니다."]
    }

    close = {
        "긍정":["다음에도 만족 드리겠습니다.","또 찾아주세요."],
        "중립":["더 나은 모습으로 보답하겠습니다.","감사합니다."],
        "부정":["재발 방지에 신경 쓰겠습니다.","다음엔 더 나은 경험 드리겠습니다."]
    }

    def make_variant(extra):
        lines = []
        lines.append(random.choice(base[sentiment]))
        lines += extra
        lines.append(random.choice(close[sentiment]))
        return " ".join(lines[:count])

    v1 = make_variant(["정성껏 준비하겠습니다."])
    v2 = make_variant(["항상 최선을 다하겠습니다."])
    v3 = make_variant(["더 꼼꼼히 챙기겠습니다."])

    return [
        {"title":"기본형","text":v1},
        {"title":"친근형","text":v2},
        {"title":"해결형","text":v3}
    ]

@app.route("/", methods=["GET","POST"])
def home():
    review=""
    tone="정중"
    length="보통"
    results=[]
    stamp=""

    if request.method=="POST":
        review=request.form.get("review")
        tone=request.form.get("tone")
        length=request.form.get("length")
        results=build(review,tone,length)
        stamp=datetime.now().strftime("%Y-%m-%d %H:%M")

    return render_template_string(HTML,review=review,tone=tone,length=length,results=results,stamp=stamp)

if __name__=="__main__":
    port=int(os.environ.get("PORT",5001))
    app.run(host="0.0.0.0",port=port)
