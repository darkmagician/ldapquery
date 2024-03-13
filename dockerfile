# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app


COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY . .
CMD ["python3", "-u", "ldapquery.py"]