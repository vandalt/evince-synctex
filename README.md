# evince-synctex

This script wraps [Evince](https://wiki.gnome.org/Apps/Evince) to provide a command-line-friendly SyncTeX integration.
It is based on [Mortal/evince-synctex](https://github.com/Mortal/evince-synctex).

## Installation

A [Python 3](https://www.python.org/downloads) installation is required. To install the latest version, run the following command:

```shell
pip3 install --user https://github.com/efoerster/evince-synctex/archive/master.zip
```

## Usage

```shell
evince-synctex PDF_FILE EDITOR_COMMAND
```

This command opens the specified file in Evince and executes the given editor command on a backwards search. A forward search can be performed by using the `-f` flag:

```shell
evince-synctex -f LINE PDF_FILE EDITOR_COMMAND
```
