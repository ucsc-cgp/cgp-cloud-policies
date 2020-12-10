# cgp-cloud-policies

Policies for CGP cloud resources, managed by [cloud-custodian].
Code and structure copied liberally from [azul].

  [cloud-custodian]: https://github.com/cloud-custodian/cloud-custodian
  [azul]: https://github.com/DataBiosphere/azul

## How it works

Using cloud-custodian, we can enforce policies on cloud resources such as:

* mandatory tags,

* automatic "off hours,"

* encryption for EBS volumes,

* security policies,

etc. on AWS, GCP, and Azure.

This repository contains cloud-custodian policy code and some glue that helps
deploy those policies to AWS. At a high level:

* cloud-custodian policies are defined in YAML. Broadly, these policies consist
  of
  - *filters* that identify resources of interest (e.g., all EC2 resources
    untagged for more than two days), and
  - *actions* to take against those resources (e.g., terminate them).

* We can use AWS Config rules to identify resources that meet our criteria, and
  hook those rules up to Lambdas to act on them.

* cloud-custodian policies are defined in [custodian/policy.yml]. That policy
  file is read by [c7n-terraform.py], which generates a set of AWS resources
  that can be deployed by Terraform. (See `make package`.)

* The policy-specific resources, in addition to the other resources needed to
  make everything run, are defined in [terraform/] and can be deployed together.
  (See `make deploy`.)

* Instead of writing Terraform HCL and cloud-custodian YAML by hand,
  configuration is written in Python and generated with a simple template
  mechanism. The helper code that makes this work is in [tempate.py]. This
  approach minimizes repetition and allows us to perform pre-processing.

Email notifications are handled by c7n-mailer. It is deployed in a similar
fashion.

### Multi-account

WIP

c7n-mailer is only deployed once.

### Tradeoffs

This approach to cloud resource management is clearly not as simple as it could
be. Much of the complexity introduced over cloud-custodian could be eliminated
if we chose not to manage resources with Terraform. However, letting
cloud-custodian manage resources itself would mean that

* running garbage collection on cloud resources deployed by cloud-custodian
  would become harder, and

* we would have to manually adjust and provision resources needed for
  cloud-custodian to work (e.g., IAM roles).

While imperfect, this approach retains several benefits. cloud-custodian:

* at time of writing, appears to be the most mature tool for our use case and
  is actively supported,

* supports GCP and Azure in addition to AWS,

* provides a number of other event streams and remediation actions that we might
  otherwise have to develop ourselves.

## Usage

### Requirements

* Terraform v0.14.0
* Python 3.9.0

```console
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
```

### Manual configuration

* You'll need to create a config.json (see [config.json.example]) with some
  account details.

* On the first time running `make deploy`, you might be sent a verification
  email to the `admin_email` specified in config.json.

* If you haven't already done so, you need to request production access to
  Amazon SES in the region and account the mailer is deployed in to send email
  to unverified addresses. (Alternatively, you can verify a domain.) Consult
  the [Amazon SES documentation].

  [Amazon SES documentation]: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/request-production-access.html

### Install

```
$ make package deploy
$ # If it's your first time deploying, deploy again:
$ make package deploy
```

It's currently necessary to deploy twice to solve a bootstrapping issue. The
cloud-custodian lambdas depend on "external" resources that we also specify
and deploy with Terraform; the first deploy creates those resources such that
they are available during the second `make package`.

Policies are enforced automatically. Alternatively, you can manually run
cloud-custodian against the current AWS account to generate JSON of all
noncompliant resources:

```
$ make report
```

### Uninstall

```
$ make package
$ make -C terraform destroy
```

# Workarounds

## c7n-mailer has no native Terraform support

Not a big problem since we can use [c7n-mailer-terraform.py] to deploy using
Terraform ourselves, but it's hacky. With native Terraform support, we might
be able to avoid the second `make package deploy`.

See also cloud-custodian/cloud-custodian#3482.

## cloud-custodian has no native Terraform support

Again, I ended up writing my own support (for a subset of cloud-custodian modes)
in [c7n-terraform.py]. cloud-custodian currently has poor support for other
deployment mechanisms.

See also cloud-custodian/cloud-custodian#48.


# Common problems

## Terraform hangs without doing anything

Your AWS credentials are likely invalid. Reauthenticate using `assume-role`,
`_preauth`, etc.
