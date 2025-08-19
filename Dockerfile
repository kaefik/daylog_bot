FROM ubuntu:20.04
LABEL maintainer="ilnursoft@gmail.com"
LABEL version="0.1"
LABEL description="Telegram BotCore"

# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive

ENV TZ=Europe/Moscow
# rm -rf /var/lib/apt/lists/* - удаление кеша apt чтобы уменьшить размер образа
RUN apt-get update && apt-get install -y python3 && apt-get install -y python3-pip && apt-get install -y  python-is-python3 && rm -rf /var/lib/apt/lists/*

WORKDIR /home/app

# установка зависимостей
COPY install_libs.sh /home/app/install_libs.sh
RUN /usr/bin/bash -c "/home/app/install_libs.sh"

# копирование файлов проекта
COPY cfg /home/app/cfg
COPY plugins_bot /home/app/plugins_bot
COPY tlgbotcore /home/app/tlgbotcore
COPY start_tlgbotcore.py /home/app/start_tlgbotcore.py

ENTRYPOINT ["python", "start_tlgbotcore.py"]