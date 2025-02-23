FROM python:3.9-slim

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

WORKDIR /app
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py"]