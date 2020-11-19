export PYTHONPATH := ${PYTHONPATH}:$(shell dirname $(shell pwd))

.PHONY: all
all: apply

include ../common.mk

.PHONY: config
config: $(patsubst %.template.py,%,$(wildcard *.tf.json.template.py))
config: $(patsubst %.template.py,%,$(wildcard */*.tf.json.template.py))

.PHONY: init
init: check_terraform config
	terraform init

.PHONY: validate
validate: init
	terraform validate

.PHONY: plan
plan: validate
	terraform plan

.PHONY: apply
apply: validate
	terraform apply

.PHONY: auto_apply
auto_apply: validate
	terraform apply -auto-approve

.PHONY: destroy
destroy: validate
	terraform destroy

.PHONY: auto_destroy
auto_destroy: validate
	@echo '!!! All resources will be deleted in 10s, hit Ctrl-C to cancel !!!'; sleep 10
	terraform destroy -auto-approve

.PHONY: clean
clean:
	rm -f *.tf.json
	rm -f config/*.tf.json
	rm -f *.zip
	rm -rf custodian

