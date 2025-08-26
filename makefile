docker-build-chrome:
	docker build -t playwright-py:v1.54.0-noble -f Dockerfile.playwright .

start-inspector:
	npx @modelcontextprotocol/inspector \
	uv \
	--directory . \
	run \
	playwright-service \
	--host 0.0.0.0 --port 8000