.PHONY: all test-all test-go test-python test-ts

all: test-all

test-all: test-go test-python test-ts

test-go:
	@echo "Running Go tests..."
	go test -v ./...

test-python:
	@echo "Running Python tests..."
	cd code/python && python -m unittest discover -v

test-ts:
	@echo "Running TypeScript tests..."
	cd code/typescript && npm install && npm test
