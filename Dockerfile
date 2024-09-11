FROM python:3.12-alpine

WORKDIR /root/.project

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src .

CMD ["python", "main.py"]