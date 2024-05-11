## Build
docker build -t zettibot-llmservice .
docker run -d -p 5000:5000 --name zettibot-llmservice zettibot-llmservice