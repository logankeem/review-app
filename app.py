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
.wrap{max-width:800px;margin:0 auto;padding:20px}
h1{font-size:22px;margin-bottom:10px}
textarea,select{width:100%;padding:12px;border-radius:10px;border:none;margin-top:8px;background:#111a33;color:#fff}
button{padding:12px;border-radius:10px;border:none;font-weight:800;margin-top:10px;cursor:pointer}
.primary{background:#3b82f6;color:#fff;width:100%}
.resultCard{
  background:#111a33;
  padding:14px;
  border-radius:12px;
  margin-top:12px;
  line-height:1.6;
}
.copyBtn{
  background:#1f2937;
  color:#fff;
  margin-top:8px;
  padding:8px 10px;
  font-size:13px;
}
</style>
</head>
<body>
<div class="wrap">
<h1>리뷰 답변 생성기</h1>

<form method="POST">
<textarea name="review" placeholder="리뷰 입력">{{ review_value or "" }}</textarea>

<select name="tone">
<option value="정중">정중</option>
<option value="친근">친근</option>
<option value="사과">사과</option>
<option value="단호">단호</option>
</select>

<select name="length">
<option value="짧게">짧게</option>
<option value="보통">보통</option>
<option value="길게">길게</option>
</select>

<button class="primary" type="submit">답변 3개 생성</button>
</form>

{% if results %}
  {% for r in results %}
    <div class="resultCard">
      {{ r }}
      <br>
      <button class="copyBtn" onclick="navigator.clipboard.writeText(`{{ r }}`)">복사</button>
    </div>
  {% endfor %}
{% endif %}

</div>
</body>
</html>
"""

def generate_reply(review, tone, length):
    base = [
        "소중한 리뷰 감사합니다.",
        "말씀 주신 부분 확인했습니다.",
        "더 나은 서비스로 보답하겠습니다.",
        "다시 방문해주시면 더 만족 드리겠습니다."
    ]
    random.shuffle(base)

    if length == "짧게":
        sentences = base[:2]
    elif length == "길게":
        sentences = base[:4]
    else:
        sentences = base[:3]

    return " ".join(sentences)

@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    review_value = ""

    if request.method == "POST":
        review_value = request.form.get("review")
        tone = request.form.get("tone")
        length = request.form.get("length")

        for _ in range(3):
            results.append(generate_reply(review_value, tone, length))

    return render_template_string(HTML_PAGE, results=results, review_value=review_value)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    app.run(host="0.0.0.0", port=port)
# redeploy
