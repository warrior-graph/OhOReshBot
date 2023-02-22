FROM python:3.10
WORKDIR /bot
copy requirements.txt /bot/
RUN pip install -r requirements.txt
copy . /bot
CMD python main.py