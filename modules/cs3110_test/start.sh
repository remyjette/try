docker build -t cs3110_test .
docker run -p 8888:80 --restart=always -dti cs3110_test
