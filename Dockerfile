FROM python:3.9
COPY . .
RUN pip3 install -r requirements.txt
CMD gunicorn -b 0.0.0.0:5000 -k eventlet app:app