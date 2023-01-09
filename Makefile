PYTHON=python3
MAX_LINE_LENGTH=120
SCRIPT=irr_rpsl_submit.py
TEST_FILE=tests/test_$(SCRIPT)

######################################################################
# https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help ## Show all the Makefile targets with descriptions
help: ## show a list of targets
	@grep -E '^[a-zA-Z][/a-zA-Z0-9_.-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: lint
lint:
	pylint --max-line-length $(MAX_LINE_LENGTH) $(SCRIPT)

.PHONY: tidy
tidy:
	black -t py37 -l $(MAX_LINE_LENGTH) --preview $(SCRIPT)

.PHONY: test
test:
	pytest $(TEST_FILE)

.PHONY: cover
cover:
	coverage erase  && coverage run --branch  --include="irr_rpsl_submit.*" --source=. -m pytest -v $(TEST_FILE) && coverage html
