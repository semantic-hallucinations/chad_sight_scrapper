FROM python:3.10-slim

WORKDIR /chad_sight_scrapper

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Устанавливаем дополнительные библиотеки для поддержки Chrome
RUN apt-get update && apt-get install -y \
    libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgdk-pixbuf2.0-0 libatspi2.0-0 libdbus-1-3
# Установка Google Chrome
RUN apt-get update && apt-get install -y wget gnupg
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
RUN apt-get update && apt-get install -y google-chrome-stable

RUN apt-get update && apt-get install -y unzip wget gnupg
RUN wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip && mv chromedriver /usr/local/bin/chromedriver
RUN chmod +x /usr/local/bin/chromedriver



ENV DISPLAY=:99

CMD ["python", "scrapper.py"]

