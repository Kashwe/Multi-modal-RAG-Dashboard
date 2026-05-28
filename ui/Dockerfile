FROM python:3.10-slim

WORKDIR /ui

COPY ui/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ui .

EXPOSE 8501

CMD ["streamlit", "run", "ui/app.py", "--server.address=0.0.0.0"]