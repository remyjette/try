FROM ocaml/opam:ubuntu-15.10_ocaml-4.02.3
MAINTAINER Remy Jette <remy@remyjette.com>

#Install custom pa_ounit
COPY pa_ounit /pa_ounit
RUN opam pin add pa_ounit /pa_ounit

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

#Install python3.5 for the server
RUN apt-get update \
  && apt-get install -y python3.5 python3.5-venv

COPY grader grader

RUN chown -R opam:opam grader

USER opam

WORKDIR grader

RUN python3.5 -m venv env

RUN . env/bin/activate; pip install flask

EXPOSE 8000

ENTRYPOINT . env/bin/activate; eval `opam config env`; python3.5 grade.py
