FROM python:3.12-slim

WORKDIR /home

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ../services/api .

CMD ["python", "app.py"]
