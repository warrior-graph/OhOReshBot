FROM python:3.11.2
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install pytz && pip install --upgrade pip && pip install -r requirements.txt
COPY . /bot
RUN apt-get update && \
    apt-get install -y locales tzdata && \
    sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && apt-get clean
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && dpkg-reconfigure -f noninteractive tzdata
ENV LANG pt_BR.UTF-8
ENV LC_ALL pt_BR.UTF-8
CMD python main.py