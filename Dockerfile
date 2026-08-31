FROM python:3
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY ./src/ /app/
COPY ./requirements.txt /app/requirements.txt
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN apt-get update
RUN apt-get install gettext -y
COPY autoSyncWorkshops.py /app/
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt
RUN pip install gunicorn

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
