import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.urandom(24)

# You should set NEWSAPI_KEY as an environment variable for security
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

TRUSTED_DOMAINS = [
    "bbc.co.uk", "bbc.com", "cnn.com", "reuters.com", "apnews.com", "nytimes.com", "theguardian.com"
]

def get_articles(query):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "relevancy",
        "apiKey": NEWSAPI_KEY,
        "pageSize": 10,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        if data.get("status") != "ok":
            return [], "NewsAPI returned an error."
        articles = data.get("articles", [])
        return articles, None
    except Exception as e:
        return [], f"Error contacting NewsAPI: {str(e)}"

def trust_score(articles):
    if not articles:
        return 0, 0
    trusted_count = 0
    for article in articles:
        source_url = article.get("url", "")
        if any(domain in source_url for domain in TRUSTED_DOMAINS):
            trusted_count += 1
    return trusted_count, len(articles)

def verdict(trusted, total):
    if total == 0:
        return "Unknown", "No relevant news found.", 0
    percent = int((trusted / total) * 100)
    if trusted >= 3 or percent >= 60:
        return "Likely True", f"Many reputable sources report on this story. ({trusted} trusted out of {total})", percent
    elif trusted == 0:
        return "Possibly Fake", "No trusted sources reported this story.", percent
    else:
        return "Possibly Fake", f"Only {trusted} out of {total} sources are reputable.", percent

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        headline = request.form.get("headline", "").strip()
        if not headline:
            flash("Please enter a news headline to check.", "danger")
            return redirect(url_for("index"))
        return redirect(url_for("result", headline=headline))
    return render_template("index.html")

@app.route("/result")
def result():
    headline = request.args.get("headline", "")
    if not headline:
        flash("Missing headline.", "danger")
        return redirect(url_for("index"))
    articles, error = get_articles(headline)
    if error:
        verdict_text, reasoning, percent = "Unknown", error, 0
    else:
        trusted, total = trust_score(articles)
        verdict_text, reasoning, percent = verdict(trusted, total)
    return render_template(
        "result.html",
        headline=headline,
        articles=articles,
        verdict=verdict_text,
        reasoning=reasoning,
        percent=percent,
        trusted_domains=TRUSTED_DOMAINS
    )

if __name__ == "__main__":
    app.run(debug=True)