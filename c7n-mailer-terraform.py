"""
Given a c7n-mailer YAML configuration file, writes the generated Lambda archive
to the specified location without deploying it.
"""
import argparse
from pathlib import (
    Path,
)

import c7n_mailer.cli
import c7n_mailer.deploy


def write_c7n_mailer_archive(config: Path, destination: Path) -> None:
    args = argparse.Namespace(config=config.as_posix(), update_lambda=True)
    config = c7n_mailer.cli.get_and_validate_mailer_config(args)
    templates_path = Path(c7n_mailer.__file__).parent.joinpath('msg-templates')
    config['templates_folders'] = [templates_path.resolve().as_posix()]
    lambda_archive = c7n_mailer.deploy.get_archive(config)
    with destination.open('wb') as archive:
        archive.write(lambda_archive.get_bytes())


if __name__ == '__main__':
    # https://youtrack.jetbrains.com/issue/PY-41806
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--config-file',
                        required=True,
                        help='c7n-mailer configuration file')
    parser.add_argument('-o', '--output-path',
                        required=True,
                        help='Output directory for Lambda archive')
    arguments = parser.parse_args()
    write_c7n_mailer_archive(config=Path(arguments.config_file),
                             destination=Path(arguments.output_path))
