FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OPENAI_API_KEY=your_api_key
ENV REDDIT_CLIENT_ID=your_reddit_client_id
ENV REDDIT_CLIENT_SECRET=your_reddit_client_secret
ENV PDL_API_KEY=your_peopledatalabs_api_key_here
ENV DB_PATH=chat_history.db

CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]
 