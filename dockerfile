# ベースイメージを指定
FROM python:3.10-slim-bullseye

ENV TZ="Asia/Tokyo"

RUN apt update
RUN apt install -y cron

# ワークディレクトリを設定
WORKDIR /app

# ソースコードをコピー
COPY ./app /app

# crontabファイルをコピー
COPY crontab /etc/cron.d/crontab

# クロンジョブを設定
RUN chmod 0644 /etc/cron.d/crontab && crontab /etc/cron.d/crontab

RUN pip install -r requirements.txt

# シェルを起動してcronを開始
CMD cron && tail -f /dev/null