SHELL=/bin/bash

.PHONY: check_terraform
check_terraform:
	@if ! hash terraform; then \
		echo -e "\nLooks like Terraform is not installed.\n"; \
		false; \
	fi

%.json: %.json.template.py .FORCE
	python $< $@
.FORCE:

%.yml: %.yml.template.py .FORCE
	python $< $@
.FORCE:

# The template output file depends on the template file, of course, as well as the environment. To be safe we force the
# template creation. This is what the fake .FORCE target does. It still is necessary to declare a target's dependency on
# a template to ensure correct ordering.
