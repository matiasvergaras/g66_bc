.PHONY: venv install run

venv:
	## Crea el virtualenv
	@rm -rf .venv
	@python3 -m venv .venv
	@./.venv/bin/pip install -U pip
	@echo "Done. Activate with: source .venv/bin/activate"

install:
	## Instala dependencias
	pip install -r requirements.txt

run:
	## Levanta la API en modo desarrollo
	uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload
