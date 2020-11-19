include ./common.mk

package:
	$(MAKE) -C custodian policy.yml
	mkdir -p terraform/custodian/
	python c7n-terraform.py -c custodian/policy.yml -o terraform/custodian
	$(MAKE) -C custodian mailer.yml
	python c7n-mailer-terraform.py -c custodian/mailer.yml -o terraform/mailer.zip

deploy:
	$(MAKE) -C terraform apply

report:
	REPORT_ONLY=1 $(MAKE) -C custodian policy.yml
	mkdir -p out/
	custodian run --output-dir out/ custodian/policy.yml -d --region all

mailer:
	$(MAKE) -C custodian mailer.yml
	c7n-mailer --config custodian/mailer.yml --update-lambda

clean:
	$(MAKE) -C terraform clean
	$(MAKE) -C custodian clean

