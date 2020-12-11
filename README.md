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
  hook those rules up to Lambdas to act on the identified resources.

* cloud-custodian policies are defined in [custodian/policy.yml]. That policy
  file is read by [c7n-terraform.py], which generates a set of AWS resources
  that can be deployed by Terraform. (See `make package`.)

  [custodian/policy.yml]: custodian/policy.yml
  [c7n-terraform.py]: c7n-terraform.py

* The policy-specific resources, in addition to the other resources needed to
  make everything run, are defined in [terraform/] and can be deployed together.
  (See `make deploy`.)

  [terraform/]: terraform/

* Instead of writing Terraform HCL and cloud-custodian YAML by hand,
  configuration is written in Python and generated with a simple template
  mechanism. The helper code that makes this work is in [template.py]. This
  approach minimizes repetition and allows us to perform pre-processing.

  [template.py]: template.py

Email notifications are handled by c7n-mailer. It is deployed in a similar
fashion.

### Multi-account and multi-region

cloud-custodian can be easily deployed to multiple accounts and regions by
adding an IAM role ARN to config.json.

cloud-custodian must be deployed to every region that we wish to observe
regional reources in. So, for example:

* if we wanted to monitor EC2 resources in us-west-2, we would need to deploy
  the cloud-custodian AWS Config rules to us-west-2, but

* if we wanted to monitor IAM resources (which are regionless), we could monitor
  them from any region.

In the latter case, only one region, the account's *primary region*, has AWS
Config rules configured to monitor global resources. The primary region also has
an AWS Config configuration aggregator, which collects the results of all
configured AWS Config rules in the account and displays them in one place.

Internally, the term *deployment* is used to refer to a region in an account
where cloud-custodian is deployed. So, a config.json that specifies an account
`foo` deploying to us-east-1, us-east-2, and us-west-1 specifies three
deployments.

There is an organization-wide configuration aggregator, which is installed in
the *primary account* (`aws.primary_account` in config.json).  The
organization-wide configuration aggregator aggregates results from all deployed
regions in all deployments.

c7n-mailer is only deployed once, to the primary region in the primary account.
All deployments use this instance of c7n-mailer.

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

* supports GCP and Azure in addition to AWS (albeit not with Terraform),

* provides a number of other event streams and remediation actions that we might
  otherwise have to develop ourselves.

If it turns out that adding the complexity needed to get things to deploy with
Terraform was the wrong call, it's easy enough to simplify things:

* Remove Terraform deployment scripts (c7n-terraform.py,
  c7n-mailer-terraform.py, and module instantiations in terraform/).

* Only deploy auxiliary resources with Terraform.

* Deploy cloud-custodian using c7n-org, hardcoding ARNs of the aforementioned
  resources.

* Manually track and clean up resources left behind. It might be feasible to do
  this (incompletely) using security groups or tagging.


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

  [config.json.example]: config.json.example

* On the first time running `make deploy`, you might be sent a verification
  email to the `admin_email` specified in config.json.

* If you haven't already done so, you need to request production access to
  Amazon SES in the region and account the mailer is deployed in to send email
  to unverified addresses. (Alternatively, you can verify a domain.) Consult the
  [Amazon SES documentation].

  [Amazon SES documentation]: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/request-production-access.html

### Install

```
$ make package deploy
```

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

### Common tasks

#### Adding, removing, or adjusting a policy

Policies are defined in [custodian/policy.yml.template.py], which is rendered to
YAML during `make package`. Consult the [cloud-custodian documentation] for
details on how to configure policies.

  [custodian/policy.yml.template.py]: custodian/policy.yml.template.py
  [cloud-custodian documentation]: https://cloudcustodian.io/docs/


#### Configuring c7n-mailer templates

In [custodian/policy.yml.template.py], you can define which mail template is
used for which matched resources. Mail templates are written with Jinja2.

TODO: Implement mail templates, which shouldn't be too hard.

Consult the [c7n-mailer documentation][c7n-mailer-docs].

  [c7n-mailer-docs]: https://cloudcustodian.io/docs/tools/c7n-mailer.html#writing-an-email-template

#### Adding an account

To add an account, add the account information to `aws.accounts` in config.json.
You will likely need to ask Erich to provision a role with the necessary
permisisons that can be assumed without MFA.

## Workarounds

### c7n-mailer has no native Terraform support

Not a big problem since we can use [c7n-mailer-terraform.py] to deploy using
Terraform ourselves, but it's hacky. With native Terraform support, we might be
able to avoid the second `make package deploy`.

See also cloud-custodian/cloud-custodian#3482.

  [c7n-mailer-terraform.py]: c7n-mailer-terraform.py

### cloud-custodian has no native Terraform support

Again, I ended up writing my own support (for a subset of cloud-custodian modes)
in [c7n-terraform.py]. cloud-custodian currently has poor support for other
deployment mechanisms.

See also cloud-custodian/cloud-custodian#48.

