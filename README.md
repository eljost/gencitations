# gencitations
Painless bibtex generator for ORCA logfiles.

## Building & Installation
Requires poetry.

```bash
# Create wheel
poetry build
# Install wheel
pip install pip install dist/[whl]
# E.g.
pip install dist/gencitations-0.1.0-py3-none-any.whl
```

## Usage
```bash
gencitations [orca_log]
# E.g.
gencitations tests/03_rimp2_jk_orca5.out
```

Currently DOIs are read from `dois.yaml` in the `gencitations/` subdirectory. A different
file, e.g., modified by the user can be specified to `gencitations` via the `--dois` argument
on the command line. See `gencitations --help` for all possible commands.
