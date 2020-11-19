export PYTHONPATH := ${PYTHONPATH}:$(shell dirname $(shell pwd))

.PHONY: all
all: $(patsubst %.template.py,%,$(wildcard *.yml.template.py))

include ../common.mk

.PHONY: clean
clean:
	rm -f *.yml

