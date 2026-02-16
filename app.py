from flask import Flask, render_template_string, request
import random
import re

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>리뷰 답변 생성기</title>
</head>
<body style="background:#0f172a;color:white;font-family:Arial;padding:32px;max-width:900px;margin:0 auto;">
  <h1 style="margin:0 0 12px 0;">⭐ 리뷰 답변 생성기 (API 없이)</h1>
  <p style="opacity:.8;margin:0 0 18px 0;">지금은 규칙 기반으로 “AI처럼” 답변을 만들어줌. (나중에 진짜 AI로 교체 가능)</p>

  <form method="POST" style="display:flex;flex-direction:column;gap:12px;">
    <textarea name="review" placeholder="예: 음식은 맛있는데 배달이 늦었어요"
      style="width:100%;height:120px;padding:12px;border-radius:10px;border:none;font-size:16px;"></textarea>

    <div style="display:flex;gap:12px;flex-wrap:wrap;">
      <select name="tone" style="flex:1;min-width:180px;padding:12px;border-radius:10px;border:none;font-size:16px;">
        <option value="정중">정중</option>
        <option value="친근">친근</option>
        <option value="사과">사과</option>
        <option value="단호">단호</option>
      </select>

      <select name="length" style="flex:1;min-width:180px;padding:12px;border-radius:10px;border:none;font-size:16px;">
        <option value="짧게">짧게</option>
        <option value="보통" selected>보통</option>
        <option value="길게">길게</option>
      </select>
    </div>

    <button type="submit"
      style="padding:12px;border-radius:10px;border:none;font-size:16px;font-weight:700;background:#3b82f6;color:white;cursor:pointer;">
      답변 생성
    </button>
  </form>

  {% if result %}
    <div style="margin-top:18px;padding:14px;background:#111827;border-radius:10px;white-space:pre-wrap;">
      <h3 style="margin:0 0 8px 0;">✅ 결과</h3>
      {{ result }}
      <div style="margin-top:10px;">
        <button onclick="copyText()" style="padding:10px;border-radius:10px;border:none;font-weight:700;cursor:pointer;">
          복사
        </button>
      </div>
    </div>
    <script>
      function copyText(){
        const text = `{{ result|replace("`","\\`") }}`;
        navigator.clipboard.writeText(text);
        alert("복사 완료!");
      }
    </script>
  {% endif %}

  {% if error %}
    <div style="margin-top:18px;padding:14px;background:#7f1d1d;border-radius:10px;white-space:pre-wrap;">
      <b>에러:</b> {{ error }}
    </div>
  {% endif %}
</body>
</html>
"""

def detect_topics(review: str):
    r = review.lower()
    topics = []

    # 키워드 기반 아주 단순 감지
    if any(k in r for k in ["맛", "맛있", "간이", "싱겁", "짜", "음식"]):
        topics.append("taste")
    if any(k in r for k in ["배달", "늦", "시간", "오래", "도착"]):
        topics.append("delivery")
    if any(k in r for k in ["불친절", "친절", "응대", "서비스", "사장", "직원"]):
        topics.append("service")
    if any(k in r for k in ["양", "적", "많", "푸짐", "가성비", "가격", "비싸"]):
        topics.append("value")
    if any(k in r for k in ["위생", "더럽", "머리카락", "냄새", "청결"]):
        topics.append("clean")
    if any(k in r for k in ["재주문", "또", "단골", "자주", "최고"]):
        topics.append("loyal")

    return topics

def make_sentences(tone: str, topics, length: str):
    # 톤별 문장 조각
    opening = {
        "정중": ["소중한 리뷰 남겨주셔서 감사합니다.", "이용해주셔서 진심으로 감사드립니다."],
        "친근": ["리뷰 남겨주셔서 감사합니다! 😊", "와주셔서 고마워요!"],
        "사과": ["불편을 드려 정말 죄송합니다.", "기대에 못 미쳐 죄송한 마음입니다."],
        "단호": ["의견 남겨주셔서 감사합니다.", "말씀 주신 내용 확인했습니다."]
    }

    # 주제별 대응 문장
    body = []
    if "taste" in topics:
        body += [
            "음식 맛과 퀄리티는 항상 일정하게 유지하려고 노력하고 있습니다.",
            "말씀 주신 부분은 조리 과정과 간 조절을 다시 점검하겠습니다."
        ]
    if "delivery" in topics:
        body += [
            "배달 시간이 지연된 점 정말 죄송합니다.",
            "배달 동선과 준비 시간을 개선해서 더 빠르게 받아보실 수 있게 하겠습니다."
        ]
    if "service" in topics:
        body += [
            "응대 과정에서 불쾌함을 느끼셨다면 정말 죄송합니다.",
            "직원 교육을 다시 진행해서 더 친절하게 안내드리겠습니다."
        ]
    if "value" in topics:
        body += [
            "양/가격에 대한 의견도 꼼꼼히 확인하겠습니다.",
            "더 만족스러운 구성으로 제공할 수 있도록 개선해보겠습니다."
        ]
    if "clean" in topics:
        body += [
            "위생 관련 이슈는 절대 가볍게 넘기지 않겠습니다.",
            "조리/포장 전 과정을 즉시 점검하고 재발 방지하겠습니다."
        ]
    if "loyal" in topics:
        body += [
            "재주문해주셔서 정말 감사합니다! 다음에도 만족드릴게요.",
            "단골로 찾아주셔서 감사한 마음입니다."
        ]

    if not body:
        body = [
            "남겨주신 내용은 꼼꼼히 확인하겠습니다.",
            "다음 방문 때 더 만족하실 수 있도록 개선하겠습니다."
        ]

    closing = {
        "정중": ["다음에도 만족 드릴 수 있도록 최선을 다하겠습니다.", "다시 한 번 감사드립니다."],
        "친근": ["다음엔 더 만족하게 해드릴게요! 🙏", "다음에 또 뵐게요!"],
        "사과": ["다음에는 꼭 더 나은 경험 드리겠습니다.", "불편 드린 점 다시 한 번 죄송합니다."],
        "단호": ["안내드린 내용대로 개선하겠습니다.", "앞으로도 기준을 지키며 운영하겠습니다."]
    }

    # 길이에 맞게 문장 수 조절
    target = {"짧게": 3, "보통": 5, "길게": 8}.get(length, 5)

    sentences = []
    sentences.append(random.choice(opening.get(tone, opening["정중"])))

    # body에서 랜덤/중복 제거해서 넣기
    random.shuffle(body)
    sentences.extend(body[: max(1, min(len(body), target - 2))])

    sentences.append(random.choice(closing.get(tone, closing["정중"])))

    # target에 맞춰 부족하면 일반 문장 추가
    fillers = [
        "소중한 의견 감사드립니다.",
        "더 좋은 서비스로 보답하겠습니다.",
        "다음에는 더 만족하실 수 있도록 하겠습니다."
    ]
    while len(sentences) < target:
        sentences.insert(-1, random.choice(fillers))

    # 너무 길면 줄이기
    sentences = sentences[:target]
    return sentences

def fake_ai_reply(review: str, tone: str, length: str) -> str:
    # 리뷰에서 괄호/특수문자 좀 정리
    cleaned = re.sub(r"\s+", " ", review).strip()
    topics = detect_topics(cleaned)
    sentences = make_sentences(tone, topics, length)

    # 마지막에 고객 리뷰를 짧게 언급하는 느낌(너무 노골적이진 않게)
    if len(cleaned) > 0 and random.random() < 0.5:
        hint = "말씀 주신 부분"
        sentences.insert(1, f"{hint} 잘 확인했습니다.")

    return "\n".join(sentences)

@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    error = ""

    if request.method == "POST":
        review = (request.form.get("review") or "").strip()
        tone = request.form.get("tone") or "정중"
        length = request.form.get("length") or "보통"

        if not review:
            error = "리뷰 내용을 입력해라."
        else:
            result = fake_ai_reply(review, tone, length)

    return render_template_string(HTML_PAGE, result=result, error=error)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
