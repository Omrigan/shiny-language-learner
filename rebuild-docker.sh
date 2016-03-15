docker build -t english-bot .
docker stop english-bot
docker rm english-bot
docker run --restart=always -d --name english-bot english-bot