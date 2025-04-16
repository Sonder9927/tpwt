# Installing tpwt

## Prerequisites

TPWT is built on top of standard [Python](https://www.python.org) and uses
some popular third party modules (e.g. [`NumPy`][numpy], [`Pandas`][pandas]).
In order to benefit from modern Python features and up to date modules, pysmo is
developed on the latest stable Python versions. Automatic tests are done on
version 3.12 and newer.

=== "pip"

    ```bash
    $ pip install git+https://github.com/sonder9927/tpwt
    ```

=== "uv"

    ```bash
    $ uv add git+https://github.com/sonder9927/tpwt
    ```

## Uninstalling

To remove pysmo from the system run:

```bash
uv remove tpwt
```

!!! warning
    Unfortunately `pip` currently does not remove dependencies that were automatically
    installed. We suggest running `pip list` to see the installed packages, which
    can then also be removed using `pip uninstall`.
