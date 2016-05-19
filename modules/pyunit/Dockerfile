FROM ubuntu:xenial
MAINTAINER Remy Jette <remy@remyjette.com>

#Install python3.5 for the server, as well as nginx
RUN apt-get update \
  && apt-get install -y python3.5 python3.5-venv nginx

#ADD certs/server.key /etc/ssl/
#ADD certs/server.crt /etc/ssl/
RUN rm -v /etc/nginx/nginx.conf
ADD nginx.conf /etc/nginx/
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

#Copy the autograder code and set it up to run
ADD tester.py tester.py

RUN python3.5 -m venv env

ADD requirements.txt requirements.txt
RUN . env/bin/activate; pip install --upgrade pip; pip install -r requirements.txt

EXPOSE 80
#EXPOSE 443

CMD . env/bin/activate; ( ./tester.py & service nginx start )
