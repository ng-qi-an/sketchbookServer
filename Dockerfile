FROM python:3.12.9-alpine

COPY . /

RUN pip3 install -r requirements.txt

# final configuration
EXPOSE 5671
CMD python3 main.py