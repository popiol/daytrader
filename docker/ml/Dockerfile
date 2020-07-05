FROM tensorflow/tensorflow:latest-py3

RUN pip install --upgrade pip && pip install \
boto3 \
sklearn

ADD app /app

WORKDIR /app

CMD ["/bin/bash"]
