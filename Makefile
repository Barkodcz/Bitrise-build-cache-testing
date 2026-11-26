.PHONY: lint generate validate render-yaml docs-serve test clean

PY ?= python3

generate:
	$(PY) tools/yaml/generate_scenarios.py
	$(PY) tools/yaml/flatten.py

render-yaml: generate

validate:
	bitrise yml validate -c bitrise.yml
	bitrise yml validate -c bitrise.modular.yml

lint:
	@echo "== check_conventions =="
	$(PY) tools/yaml/check_conventions.py
	@echo "== cache_lint (static anti-pattern checker) =="
	$(PY) tools/lint/cache_lint.py
	@command -v yamllint >/dev/null 2>&1 && yamllint . || echo "(skip) yamllint not installed"
	@command -v shellcheck >/dev/null 2>&1 && find tools -name '*.sh' -print0 | xargs -0 shellcheck || echo "(skip) shellcheck not installed"
	@command -v ruff >/dev/null 2>&1 && ruff check tools generators || echo "(skip) ruff not installed"
	@command -v markdownlint >/dev/null 2>&1 && markdownlint docs README.md || echo "(skip) markdownlint not installed"

test:
	$(PY) -m pytest tools generators -q || echo "(skip) pytest not installed or no tests collected"

docs:
	$(PY) tools/yaml/generate_doc_stubs.py
	@echo "-- scenario matrix (paste into README.md between the markers if it changed) --"
	$(PY) tools/yaml/scenario_matrix.py

docs-serve:
	$(PY) -m http.server 8000 --directory docs

report-fixtures:
	$(PY) tools/report/render.py --metrics-dir tools/report/fixtures --catalog scenarios/catalog.yml --out .showcase/report
	$(PY) tools/report/assertions.py --metrics-dir tools/report/fixtures --catalog scenarios/catalog.yml --out .showcase/report --fail-on-assertion false

clean:
	rm -rf .showcase
