FROM python:3.12-alpine

WORKDIR /home

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./source .

CMD ["python", "app.py"]
