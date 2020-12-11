import dataclasses
import functools
import json
from pathlib import (
    Path,
)
import subprocess
import sys
import tempfile
from typing import (
    Any,
    Mapping,
    Optional,
    Sequence,
)

import yaml


project_root = Path(__file__).parent.resolve()


def emit_yaml(yml: Mapping) -> None:
    emit(yaml.dump(yml))


def emit_tf(tf: Mapping) -> None:
    emit(json.dumps(tf, indent=4))


def emit(doc: Optional[str]) -> None:
    rendered_template = Path(sys.argv[1])
    if doc is None:
        print(f'Removing {rendered_template.as_posix()}')
        rendered_template.unlink()
    else:
        with tempfile.NamedTemporaryFile(mode='w+',
                                         dir=rendered_template.parent.as_posix(),
                                         encoding='utf-8',
                                         delete=False) as tmpfile:
            try:
                tmpfile.write(doc)
            except BaseException:
                Path(tmpfile.name).unlink()
                raise
            else:
                print(f"Creating {rendered_template.as_posix()}")
                Path(tmpfile.name).rename(rendered_template)


class Terraform:

    def __init__(self, terraform_dir: Path):
        self.dir = terraform_dir

    def cmd(self, *args: str) -> str:
        cmd = subprocess.run(['terraform', *args],
                             cwd=self.dir,
                             check=True,
                             stdout=subprocess.PIPE,
                             text=True,
                             shell=False)
        return cmd.stdout.decode()

    @functools.cached_property
    def state(self) -> Mapping[str, Any]:
        state = json.loads(self.cmd('show', '-json'))
        assert state['format_version'] == '0.1'
        return state

    def attribute(self, address: str, attr: str) -> str:
        resources = []
        try:
            resources = [res for res in self.state['values']['root_module']['resources']
                         if res['address'] == address]
        except KeyError:
            pass
        finally:
            if len(resources) == 1:
                return resources[0]['values'][attr]
            else:
                raise ValueError(f'Expected 1 resource {address}, found {len(resources)}')

    def get_attribute(self, address: str, attr: str, default: str = None) -> str:
        try:
            return self.attribute(address, attr)
        except ValueError:
            if default:
                return default
            else:
                return f'${{{address}.{attr}}}'


terraform = Terraform(project_root.joinpath('terraform'))


@dataclasses.dataclass
class Account:
    role_arn: str
    name: str
    regions: Sequence[str]
    primary_region: str
    primary: bool = False

    def module_name(self, module: str) -> str:
        return config.module_name(module, self.name)


@dataclasses.dataclass
class Deployment:
    region: str
    account: Account

    @property
    def name(self) -> str:
        return f'{self.account.name}_{self.region}'

    @property
    def primary(self) -> bool:
        return self.region == self.account.primary_region

    def module_name(self, module: str) -> str:
        return config.module_name(module, self.name)


class Config:

    def __init__(self, config_file: Path):
        with config_file.open('r') as cfg:
            self._config = json.load(cfg)

    @property
    def admin_email(self) -> str:
        return self._config['admin_email']

    @property
    def aws_accounts(self) -> Sequence[Account]:
        return [
            Account(**{  # as dict to prevent passing same arg multiple times
                'name': account_name,
                **self._config['aws']['defaults'],
                **account
            })
            for account_name, account in self._config['aws']['accounts'].items()
        ]

    @property
    def aws_deployments(self) -> Sequence[Deployment]:
        return [
            Deployment(region=region, account=account)
            for account in self.aws_accounts
            for region in account.regions
        ]

    @property
    def aws_primary_deployments(self) -> Sequence[Deployment]:
        return [
            deployment
            for deployment in self.aws_deployments
            if deployment.region == deployment.account.primary_region
        ]

    @property
    def aws_primary_deployment(self) -> Deployment:
        primary_deployments = [
            primary_deployment
            for primary_deployment in self.aws_primary_deployments
            if primary_deployment.account.primary
        ]
        assert len(primary_deployments) == 1, 'Exactly one primary account required'
        return primary_deployments[0]

    @property
    def aws_provider_access_key(self) -> str:
        return self._config['aws']['provider']['access_key']

    @property
    def aws_provider_secret_key(self) -> str:
        return self._config['aws']['provider']['secret_key']

    def module_name(self, module: str, deployment: str) -> str:
        return f'{module}_{deployment}'


config = Config(project_root.joinpath('config.json'))
