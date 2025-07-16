from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(posts):
    sentiments = []
    for p in posts:
        text = f"{p['title']} {p['selftext']}"
        score = analyzer.polarity_scores(text)["compound"]
        sentiments.append(score)
    return sentiments
