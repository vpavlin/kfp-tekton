# Copyright 2020 kubeflow.org
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Acknowledgements:
#  - The help target was derived from https://stackoverflow.com/a/35730328/5601796

VENV ?= .venv
export VIRTUAL_ENV := $(abspath ${VENV})
export PATH := ${VIRTUAL_ENV}/bin:${PATH}

.PHONY: help
help: ## Display the Make targets
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.PHONY: venv
venv: $(VENV)/bin/activate ## Create and activate virtual environment
$(VENV)/bin/activate: sdk/python/setup.py
	@echo "VENV=$(VENV)"
	@test -d $(VENV) || python3 -m venv $(VENV)
	pip install -e sdk/python
	@touch $(VENV)/bin/activate

.PHONY: install
install: venv ## Install the kfp_tekton compiler in a virtual environment
	@echo "Run 'source $(VENV)/bin/activate' to activate the virtual environment."

.PHONY: unit_test
unit_test: venv ## Run compiler unit tests
	@echo "=================================================================="
	@echo "Optional environment variables to configure $@, examples:"
	@sed -n -e 's/# *\(make $@ .*\)/  \1/p' sdk/python/tests/compiler/compiler_tests.py
	@echo "=================================================================="
	@sdk/python/tests/run_tests.sh
	@echo "$@: OK"

.PHONY: e2e_test
e2e_test: venv ## Run compiler end-to-end tests (requires kubectl and tkn CLI)
	@echo "=================================================================="
	@echo "Optional environment variables to configure $@, examples:"
	@sed -n -e 's/# *\(make $@ .*\)/  \1/p' sdk/python/tests/compiler/compiler_tests_e2e.py
	@echo "=================================================================="
	@which kubectl > /dev/null || (echo "Missing kubectl CLI" && exit 1)
	@test -z "${KUBECONFIG}" && echo "KUBECONFIG not set" && exit 1 || echo "KUBECONFIG: ${KUBECONFIG}"
	@kubectl version --short || (echo "Failed to access kubernetes cluster" && exit 1)
	@which tkn > /dev/null || (echo "Missing tkn CLI" && exit 1)
	@sdk/python/tests/run_e2e_tests.sh
	@echo "$@: OK"

.PHONY: test
test: unit_test e2e_test ## Run compiler unit tests and end-to-end tests
	@echo "$@: OK"

.PHONY: report
report: ## Report compilation status of KFP testdata DSL scripts
	@sdk/python/tests/test_kfp_samples.sh
	@echo "$@: OK"

.PHONY: lint
lint: venv ## Check Python code style compliance
	@which flake8 > /dev/null || pip install flake8
	@flake8 sdk/python --show-source --statistics \
		--select=E9,E2,E3,E5,F63,F7,F82,F4,F841,W291,W292 \
		--per-file-ignores sdk/python/tests/compiler/testdata/*:F841 \
 		--max-line-length=140
	@echo "$@: OK"

.PHONY: check_license
check_license: ## Check for license header in source files
	@find ./sdk/python -type f \( -name '*.py' -o -name '*.yaml' \) -exec \
		grep -H -E -o -c 'Copyright 20.* kubeflow.org' {} \; | \
		grep -E ':0$$' | sed 's/..$$//' | \
		grep . && echo "The files listed above are missing the license header" && exit 1 || \
		echo "$@: OK"

.PHONY: check_mdtoc
check_mdtoc: ## Check Markdown files for valid the Table of Contents
	@find samples sdk *.md -type f -name '*.md' -exec \
		grep -l -i 'Table of Contents' {} \; | sort | \
		while read -r md_file; do \
			grep -oE '^ *[-+*] \[[^]]+\]\(#[^)]+\)' "$${md_file}" |  sed -e 's/[-+*] /- /g' > md_file_toc; \
			./tools/mdtoc.sh "$${md_file}" > generated_toc; \
			diff -w md_file_toc generated_toc || echo "$${md_file}"; \
			rm -f md_file_toc generated_toc; \
		done | grep . && echo "Run './tools/mdtoc.sh <md-file>' to update the 'Table of Contents' in the Markdown files reported above." && exit 1 || \
		echo "$@: OK"

.PHONY: verify
verify: check_license check_mdtoc lint unit_test report ## Run all verification targets: check_license, check_mdtoc, lint, unit_test, report
	@echo "$@: OK"

.PHONY: distribution
distribution: venv ## Create a distribution and upload to test.PyPi.org
	@echo "NOTE: Using test.PyPi.org -- edit Makefile to target real PyPi index"
	@twine --version > /dev/null 2>&1 || pip install twine
	@cd sdk/python && \
		rm -rf dist/ && \
		python3 setup.py sdist && \
		twine check dist/* && \
		twine upload --repository testpypi dist/*

.PHONY: build
build: ## Create GO vendor directories with all dependencies
	go mod vendor
	# Extract go licenses into a single file. This assume licext is install globally through
	# npm install -g license-extractor
	# See https://github.com/arei/license-extractor
	licext --mode merge --source vendor/ --target third_party/license.txt --overwrite
	# Delete vendor directory
	rm -rf vendor
