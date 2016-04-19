docker build -t cs3110_test .
docker run -p 8000:443 --restart=always -dti cs3110_test
