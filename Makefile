.PHONY: run install clean

# Run the FastAPI application with uvicorn
run:
	uvicorn main:app --reload

# Install dependencies
install:
	pip install -r requirements.txt

# Install dependencies in development mode
install-dev:
	pip install -r requirements.txt --upgrade

# Clean up Python cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
