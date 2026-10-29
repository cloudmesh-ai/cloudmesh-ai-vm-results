PYTHON ?= python3
SCRIPT := analyze-smoke-tests.py

.PHONY: install analyze clean

install:
	$(PYTHON) -m pip install -r requirements.txt

analyze:
	$(PYTHON) $(SCRIPT)

clean:
	rm -f images/*-execution-times.png
	rm -f comparison.md
