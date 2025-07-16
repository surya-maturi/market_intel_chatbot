# app.py

import streamlit as st
import nltk
import openai
import plotly.graph_objs as go

from db.db import init_db, save_message, get_history
from utils.config import PERPLEXITY_API_KEY, OPENAI_API_KEY
from agents.intent_detector import detect_intent
from agents.reddit_agent import fetch_reddit_posts
from agents.sentiment_agent import analyze_sentiment
from agents.synthesizer_agent import synthesize_insight
from agents.pdl_agent import fetch_company_info

# Choose which key to use
openai.api_key = PERPLEXITY_API_KEY or OPENAI_API_KEY

nltk.download('vader_lexicon')

# Init DB
conn = init_db()

st.set_page_config(page_title="Market Intelligence Chatbot", layout="wide")
st.title("🧠 Market Intelligence Chatbot for Startups")

# Load session history
if "history" not in st.session_state:
    st.session_state.history = []
if not st.session_state.history:
    for row in get_history(conn):
        st.session_state.history.append((row['sender'], row['message']))

# User input
user_query = st.text_input("Ask your question:", "")
if st.button("Send") and user_query:
    save_message(conn, 'user', user_query)
    st.session_state.history.append(('user', user_query))

    intent, entities = detect_intent(user_query)

    if intent in ['trend', 'sentiment']:
        posts      = fetch_reddit_posts(entities)
        sentiments = analyze_sentiment(posts)
        summary    = synthesize_insight(user_query, posts, sentiments)

        st.markdown(f"**Bot:** {summary}")
        st.subheader("Reddit Sentiment Analysis")
        fig = go.Figure([go.Histogram(x=sentiments, nbinsx=20)])
        fig.update_layout(
            title="Sentiment Distribution",
            xaxis_title="Sentiment Score",
            yaxis_title="Frequency"
        )
        st.plotly_chart(fig)
        st.subheader("Example Reddit Posts")
        for p in posts[:5]:
            st.markdown(f"- **{p['title']}**")

    elif intent == 'competitor':
        info    = fetch_company_info(entities)
        summary = (
            f"**{info['name']}**\n\n"
            f"Description: {info.get('description','N/A')}\n\n"
            f"Employees: {info.get('employees','N/A')}\n\n"
            f"Estimated Revenue: {info.get('estimatedRevenue','N/A')}\n\n"
            f"Total Funding: {info.get('totalFunding','N/A')}"
        )
        st.markdown(f"**Bot:** {summary}")

    else:
        summary = "Sorry, I couldn't understand your request."
        st.markdown(f"**Bot:** {summary}")

    save_message(conn, 'bot', summary)
    st.session_state.history.append(('bot', summary))

# Show history
st.divider()
for who, msg in st.session_state.history:
    prefix = "You" if who == 'user' else "Bot"
    st.markdown(f"**{prefix}:** {msg}")
