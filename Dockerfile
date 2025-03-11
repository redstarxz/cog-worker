ARG COG_VERSION

FROM r8.im/redstarxz/10xi:latest

RUN pip install runpod

ADD src/handler.py /rp_handler.py

CMD ["python", "-u", "/rp_handler.py"]
