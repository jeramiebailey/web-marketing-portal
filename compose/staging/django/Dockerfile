FROM python:3.6-alpine

ENV PYTHONUNBUFFERED 1

RUN apk update \
  # psycopg2 dependencies
  # && apk add --virtual build-deps .pynacl_deps gcc python3-dev musl-dev build-base libffi-dev \
  && apk add --virtual build-deps gcc python3-dev musl-dev \
  && apk add postgresql-dev \
  # Pillow dependencies
  && apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev \
  # CFFI dependencies
  && apk add libffi-dev py-cffi \
  && apk add curl \
  && apk add make \ 
  && apk add chromium \
  && apk add chromium-chromedriver \
  && apk add cargo \
  && apk add rust \
  && apk add g++

RUN addgroup -S django \
    && adduser -S -G django django

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
# RUN pip install --upgrade pip
# RUN pip install --no-cache-dir --use-deprecated=legacy-resolver -r /requirements/staging.txt \
#     && rm -rf /requirements

RUN pip install --upgrade pip
RUN python -m pip install setuptools
RUN pip install --no-cache-dir -r /requirements/production.txt

# RUN pip3 install --upgrade pip
# RUN python3 -m pip install --upgrade setuptools
# RUN pip3 install --no-cache-dir -r /requirements/production.txt

COPY ./compose/staging/django/entrypoint /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint
RUN chown django /entrypoint

COPY ./compose/staging/django/start /start
RUN sed -i 's/\r//' /start
RUN chmod +x /start
RUN chown django /start

COPY ./compose/staging/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r//' /start-celeryworker
RUN chmod +x /start-celeryworker
RUN chown django /start-celeryworker

COPY ./compose/staging/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r//' /start-celerybeat
RUN chmod +x /start-celerybeat
RUN chown django /start-celerybeat

COPY ./compose/staging/django/celery/flower/start /start-flower
RUN sed -i 's/\r//' /start-flower
RUN chmod +x /start-flower

COPY . /app

RUN chown -R django /app
RUN chown -R django /root
# RUN chown -R django /root/*
# RUN chown -R django /root/.ssh

USER django

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
