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
        return cmd.stdout

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


class Config:

    def __init__(self, config_file: Path):
        with config_file.open('r') as cfg:
            self._config = json.load(cfg)

    @property
    def admin_email(self) -> str:
        return self._config['admin_email']

    @property
    def admin_region(self) -> str:
        return self._config['admin_region']

    @property
    def aws_accounts(self) -> JSON:
        return self._config['aws']


config = Config(project_root.joinpath('config.json'))
