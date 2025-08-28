docker-build-chrome:
	docker build -t playwright-py:v1.54.0-noble -f Dockerfile.playwright .

docker-build-uv-pr-image:
	docker build -t playwright-py-uv:v1.54.0-noble -f Dockerfile.playwright .

start-inspector:
	npx @modelcontextprotocol/inspector \
	uv \
	--directory . \
	run \
	playwright-service \
	--host 0.0.0.0 --port 8001

start-inspector-dev:
	npx @modelcontextprotocol/inspector \
	uv \
	--directory . \
	run \
	playwright-service \
	--host 0.0.0.0 --port 8000