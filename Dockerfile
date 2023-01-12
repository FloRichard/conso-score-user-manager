FROM python:3-alpine

WORKDIR /app

COPY requirements.txt ./

RUN apk add python3 postgresql-libs && \
    apk add --virtual .build-deps gcc python3-dev musl-dev postgresql-dev
RUN pip install -r requirements.txt

ENV FLASK_APP=app_auth \
    FLASK_ENV=production \
    FLASK_DEBUG=on

EXPOSE 5000

COPY . .

#CMD [ "waitress-serve", "--port=5000", "--expose-tracebacks", "--call", "conso_score_back:create_app"]
ENTRYPOINT flask run --host=0.0.0.0