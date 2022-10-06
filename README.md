# The Ethereum Standard Library

[![GitHub](https://img.shields.io/github/license/skellet0r/eth-stdlib)](https://github.com/skellet0r/eth-stdlib/blob/master/COPYING)
[![Codecov](https://img.shields.io/codecov/c/github/skellet0r/eth-stdlib)](https://app.codecov.io/gh/skellet0r/eth-stdlib)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/skellet0r/eth-stdlib/test?label=test%20suite)](https://github.com/skellet0r/eth-stdlib/actions/workflows/test.yaml)
[![Read the Docs](https://img.shields.io/readthedocs/eth-stdlib)](https://eth-stdlib.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/eth-stdlib)](https://pypi.org/project/eth-stdlib/)

The Ethereum Standard Library is a collection of libraries for developers building on the EVM.

## Installation

### Using pip

```bash
$ pip install eth-stdlib
```

### Using poetry

```bash
$ poetry add eth-stdlib
```

## Development

### Initializing an Environment

To start developing/contributing to the eth-stdlib code base follow these steps:

1. Install [poetry](https://python-poetry.org/)

   ```bash
   $ pipx install poetry
   ```

2. Clone the eth-stdlib repository

   ```bash
   $ git clone https://github.com/skellet0r/eth-stdlib.git
   ```

3. Initialize virtual environment

   ```bash
   $ poetry install --sync
   ```

Afterwards the development environment will be complete.

### Testing

To run the test suite, execute the following command:available in the `html

```bash
$ poetry run pytest
```

After running the test suite, code coverage results will be displayed in the terminal, as well as exported in html format (in the `htmlcov` directory).
