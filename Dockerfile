FROM python:3.10

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

WORKDIR /app
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.address=0.0.0.0", "--server.port=8501"]

