# FROM ubuntu:22.04
FROM python:3.10-slim-bullseye

# Might be necessary.
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /app

# Install all the dependencies as it's own layer.
COPY ./requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Add requirements file and install.
COPY . .

# Allow files to be pulled off the container easily.
RUN python -m pip install -U magic-wormhole
RUN python -m pip install -e .

# Expose the port and then launch the app.
EXPOSE 80

ENV DB_PATH_DIR=/var/data
# RUN rm -rf /var/data

# For now keep in testing mode
ENV MODE=PRODUCTION
# ENV MODE=DEVELOPMENT

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "80", "--workers", "10", "vids_db_server.app:app"]
