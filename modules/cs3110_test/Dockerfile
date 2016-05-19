FROM ocaml/opam:ubuntu-15.10_ocaml-4.02.3
MAINTAINER Remy Jette <remy@remyjette.com>

RUN opam update

RUN opam install oasis
RUN opam pin add type_conv 112.01.02

#Install custom pa_ounit
COPY pa_ounit /pa_ounit
RUN eval `opam config env` && opam pin add pa_ounit /pa_ounit

#Get async, which will get core and other important libraries
RUN opam pin add async 112.35.00

#Get qcheck, necessary for 3110 tools
RUN opam pin add qcheck 0.4

RUN opam pin add yojson 1.3.2

#Install 3110 tools
RUN [ -d 3110-tools ] || git clone https://github.com/cs3110/tools.git 3110-tools \
  && eval `opam config env` \
  && make -C 3110-tools/cs3110-cli/ \
  && make -C 3110-tools/cs3110-cli/ install

USER root

#Install python3.5 for the server, as well as nginx
RUN apt-get update \
  && apt-get install -y python3.5 python3.5-venv nginx

#Configure nginx to accept web requests
#ADD certs/server.key /etc/ssl/
#ADD certs/server.crt /etc/ssl/
RUN rm -v /etc/nginx/nginx.conf
ADD nginx.conf /etc/nginx/
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

#Copy the autograder code and set it up to run
COPY tester tester

RUN chown -R opam:opam tester

USER opam

WORKDIR tester

RUN python3.5 -m venv env

ADD requirements.txt requirements.txt
RUN . env/bin/activate; pip install -r requirements.txt

EXPOSE 443

CMD . env/bin/activate; eval `opam config env`; ( gunicorn -w 8 -k gthread -b unix:/tmp/gunicorn.sock tester:app & sudo service nginx start)
