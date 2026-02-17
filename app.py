from flask import Flask, render_template_string, request
import os
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
  <style>
    :root{
      --bg:#0b1220;
      --card:#0f1b33;
      --card2:#0b162d;
      --text:#e8eefc;
      --muted:#9db0d6;
      --line:rgba(255,255,255,.08);
      --blue:#3b82f6;
      --blue2:#2563eb;
      --red:#ef4444;
      --shadow: 0 14px 50px rgba(0,0,0,.45);
      --radius: 18px;
    }
    *{ box-sizing:border-box; }
    body{
      margin:0;
      font-family: ui-sans-serif, system-ui, -apple-system, "Apple SD Gothic Neo", "Noto Sans KR", Arial, sans-serif;
      background:
        radial-gradient(1200px 500px at 20% -10%, rgba(59,130,246,.35), transparent 60%),
        radial-gradient(900px 400px at 90% 0%, rgba(16,185,129,.18), transparent 55%),
        var(--bg);
      color:var(--text);
    }
    .wrap{
      max-width: 980px;
      margin: 0 auto;
      padding: 28px 16px 60px;
    }
    .top{
      display:flex;
      gap:14px;
      align-items:flex-start;
      justify-content:space-between;
      margin-bottom: 18px;
    }
    .brand{
      display:flex;
      flex-direction:column;
      gap:6px;
    }
    .title{
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.3px;
      margin:0;
    }
    .subtitle{
      margin:0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }
    .badge{
      display:inline-flex;
      align-items:center;
      gap:8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(59,130,246,.12);
      border:1px solid rgba(59,130,246,.22);
      color:#cfe1ff;
      font-size: 12px;
      white-space:nowrap;
      margin-top: 4px;
    }

    .grid{
      display:grid;
      grid-template-columns: 1.2fr .8fr;
      gap: 14px;
    }
    @media (max-width: 860px){
      .grid{ grid-template-columns: 1fr; }
      .top{ flex-direction:column; }
    }

    .card{
      background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.03));
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow:hidden;
    }
    .card .head{
      padding: 16px 16px 12px;
      border-bottom: 1px solid var(--line);
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap: 10px;
      background: rgba(0,0,0,.10);
    }
    .card .head h2{
      margin:0;
      font-size: 14px;
      letter-spacing: .2px;
      color: #cfe1ff;
      font-weight: 800;
    }
    .card .body{
      padding: 16px;
    }

    .textarea{
      width:100%;
      min-height: 160px;
      resize: vertical;
      padding: 14px 14px;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,.10);
      background: rgba(2,6,23,.50);
      color: var(--text);
      font-size: 15px;
      line-height: 1.55;
      outline:none;
    }
    .textarea:focus{
      border-color: rgba(59,130,246,.65);
      box-shadow: 0 0 0 4px rgba(59,130,246,.15);
    }

    .row{
      display:grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 12px;
    }
    @media (max-width: 520px){
      .row{ grid-template-columns: 1fr; }
    }

    .select{
      width:100%;
      padding: 12px 12px;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,.10);
      background: rgba(2,6,23,.50);
      color: var(--text);
      font-size: 14px;
      outline:none;
    }
    .select:focus{
      border-color: rgba(59,130,246,.65);
      box-shadow: 0 0 0 4px rgba(59,130,246,.15);
    }

    .actions{
      display:flex;
      gap: 10px;
      margin-top: 12px;
      flex-wrap: wrap;
    }
    .btn{
      appearance:none;
      border:none;
      border-radius: 14px;
      padding: 12px 14px;
      font-size: 14px;
      font-weight: 800;
      cursor:pointer;
      transition: transform .05s ease, opacity .15s ease, background .15s ease;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      gap: 10px;
      user-select:none;
    }
    .btn:active{ transform: scale(.98); }

    .btn.primary{
      background: linear-gradient(180deg, rgba(59,130,246,1), rgba(37,99,235,1));
      color: white;
      flex: 1;
      min-width: 200px;
    }
    .btn.primary:hover{ opacity:.95; }

    .btn.ghost{
      background: rgba(255,255,255,.06);
      border: 1px solid rgba(255,255,255,.10);
      color: var(--text);
    }
    .btn.ghost:hover{ background: rgba(255,255,255,.09); }

    .hint{
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }

    .result{
      white-space: pre-wrap;
      background: rgba(2,6,23,.55);
      border: 1px solid rgba(255,255,255,.10);
      border-radius: 16px;
      padding: 14px;
      line-height: 1.6;
      font-size: 15px;
    }
    .meta{
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap: 10px;
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 12px;
    }
    .pill{
      display:inline-flex;
      align-items:center;
      gap: 8px;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,.06);
      border: 1px solid rgba(255,255,255,.10);
    }

    .error{
      background: rgba(239,68,68,.10);
      border: 1px solid rgba(239,68,68,.25);
      color: #ffd0d0;
      border-radius: 16px;
      padding: 14px;
      line-height: 1.6;
      font-size: 14px;
    }

    /* 로딩 오버레이 */
    .overlay{
      position: fixed;
      inset: 0;
      background: rgba(2,6,23,.62);
      display:none;
      align-items:center;
      justify-content:center;
      padding: 20px;
      z-index: 9999;
    }
    .overlay.on{ display:flex; }
    .loaderCard{
      width: min(420px, 100%);
      background: rgba(15,27,51,.85);
      border: 1px solid rgba(255,255,255,.10);
      border-radius: 18px;
      box-shadow: var(--shadow);
      padding: 18px;
      text-align:center;
    }
    .spinner{
      width: 44px;
      height: 44px;
      border-radius: 999px;
      border: 4px solid rgba(255,255,255,.18);
      border-top-color: rgba(59,130,246,1);
      margin: 10px auto 12px;
      animation: spin .9s linear infinite;
    }
    @keyframes spin{ to{ transform: rotate(360deg); } }
    .loaderTitle{ font-weight: 900; margin: 0 0 6px; }
    .loaderText{ margin:0; color: var(--muted); font-size: 13px; line-height: 1.45; }

    .footer{
      margin-top: 14px;
      color: rgba(157,176,214,.75);
      font-size: 12px;
      text-align:center;
    }
    a{ color:#cfe1ff; }
  </style>
</head>

<body>
  <div class="wrap">
    <div class="top">
      <div class="brand">
        <h1 class="title">리뷰 답변 생성기</h1>
        <p class="subtitle">리뷰를 붙여넣고 버튼 누르면 “사장님 답변”을 자동 생성해줘. (현재는 API 없이 규칙 기반)</p>
        <div class="badge">✅ 폰 최적화 · ✅ 복사 버튼 · ✅ 배포됨(Render)</div>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <div class="head">
          <h2>입력</h2>
          <div class="pill">팁: 리뷰가 길수록 더 자연스러움</div>
        </div>
        <div class="body">
          <form id="genForm" method="POST">
            <textarea class="textarea" name="review" placeholder="예) 음식은 맛있는데 배달이 너무 늦었어요. 양은 괜찮았는데 다음엔 빨랐으면 좋겠네요.">{{ review_value or "" }}</textarea>

            <div class="row">
              <select class="select" name="tone">
                <option value="정중" {{ "selected" if tone=="정중" else "" }}>정중</option>
                <option value="친근" {{ "selected" if tone=="친근" else "" }}>친근</option>
                <option value="사과" {{ "selected" if tone=="사과" else "" }}>사과</option>
                <option value="단호" {{ "selected" if tone=="단호" else "" }}>단호</option>
              </select>

              <select class="select" name="length">
                <option value="짧게" {{ "selected" if length=="짧게" else "" }}>짧게</option>
                <option value="보통" {{ "selected" if length=="보통" else "" }}>보통</option>
                <option value="길게" {{ "selected" if length=="길게" else "" }}>길게</option>
              </select>
            </div>

            <div class="actions">
              <button class="btn primary" type="submit">
                <span>답변 생성</span>
              </button>
              <button class="btn ghost" type="button" onclick="clearForm()">
                초기화
              </button>
            </div>

            <div class="hint">
              무료 배포(Render)는 처음 접속 시 20~50초 느릴 수 있어. 정상임.
            </div>
          </form>
        </div>
      </div>

      <div class="card">
        <div class="head">
          <h2>결과</h2>
          <div class="pill">복사 가능</div>
        </div>
        <div class="body">
          {% if error %}
            <div class="error"><b>에러:</b><br/>{{ error }}</div>
          {% elif result %}
            <div class="meta">
              <span>말투: <b>{{ tone }}</b> · 길이: <b>{{ length }}</b></span>
              <button class="btn ghost" type="button" onclick="copyResult()">복사</button>
            </div>
            <div id="resultBox" class="result">{{ result }}</div>
          {% else %}
            <div class="result" style="color:rgba(157,176,214,.9);">
              아직 결과 없음.<br/>
              왼쪽에 리뷰 넣고 “답변 생성” 눌러봐.
            </div>
          {% endif %}
        </div>
      </div>
    </div>

    <div class="footer">
      Made by logankeem · 배포 링크로 친구한테 보내도 됨 😎
    </div>
  </div>

  <div id="overlay" class="overlay">
    <div class="loaderCard">
      <div class="spinner"></div>
      <p class="loaderTitle">생성 중…</p>
      <p class="loaderText">잠깐만. 답변 만들고 있어.</p>
    </div>
  </div>

  <script>
    const overlay = document.getElementById("overlay");
    const form = document.getElementById("genForm");

    form?.addEventListener("submit", () => {
      overlay.classList.add("on");
    });

    function clearForm(){
      const ta = form.querySelector('textarea[name="review"]');
      if(ta) ta.value = "";
      const result = document.getElementById("resultBox");
      overlay.classList.remove("on");
    }

    function copyResult(){
      const el = document.getElementById("resultBox");
      if(!el) return alert("복사할 결과가 없어");
      const text = el.innerText;
      navigator.clipboard.writeText(text);
      alert("복사 완료!");
    }
  </script>
</body>
</html>
"""

def detect_topics(review: str):
    r = review.lower()
    topics = []
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
    opening = {
        "정중": ["소중한 리뷰 남겨주셔서 감사합니다.", "이용해주셔서 진심으로 감사드립니다."],
        "친근": ["리뷰 남겨주셔서 감사합니다! 😊", "와주셔서 고마워요!"],
        "사과": ["불편을 드려 정말 죄송합니다.", "기대에 못 미쳐 죄송한 마음입니다."],
        "단호": ["의견 남겨주셔서 감사합니다.", "말씀 주신 내용 확인했습니다."]
    }

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

    target = {"짧게": 3, "보통": 5, "길게": 8}.get(length, 5)

    sentences = [random.choice(opening.get(tone, opening["정중"]))]
    random.shuffle(body)
    sentences.extend(body[: max(1, min(len(body), target - 2))])
    sentences.append(random.choice(closing.get(tone, closing["정중"])))

    fillers = [
        "소중한 의견 감사드립니다.",
        "더 좋은 서비스로 보답하겠습니다.",
        "다음에는 더 만족하실 수 있도록 하겠습니다."
    ]
    while len(sentences) < target:
        sentences.insert(-1, random.choice(fillers))

    return sentences[:target]

def fake_ai_reply(review: str, tone: str, length: str) -> str:
    cleaned = re.sub(r"\s+", " ", review).strip()
    topics = detect_topics(cleaned)
    sentences = make_sentences(tone, topics, length)
    if cleaned and random.random() < 0.5:
        sentences.insert(1, "말씀 주신 부분 잘 확인했습니다.")
    return "\n".join(sentences)

@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    error = ""

    # 기본 선택값 유지
    tone = "정중"
    length = "보통"
    review_value = ""

    if request.method == "POST":
        review_value = (request.form.get("review") or "").strip()
        tone = request.form.get("tone") or "정중"
        length = request.form.get("length") or "보통"

        if not review_value:
            error = "리뷰 내용을 입력해라."
        else:
            result = fake_ai_reply(review_value, tone, length)

    return render_template_string(
        HTML_PAGE,
        result=result,
        error=error,
        tone=tone,
        length=length,
        review_value=review_value
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    app.run(debug=False, host="0.0.0.0", port=port)
