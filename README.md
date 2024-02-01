# Unofficial exports of the Serlo metadata API

## Development

* Install the Python version in [.tool-versions](.tool-versions)
    * You may use [asdf](https://asdf-vm.com/) for the installation.

### Using Pipenv

* Install [pipenv](https://pipenv.pypa.io/en/latest/installation/#installing-pipenv)
* Run `pipenv shell` to activate the project's [virtual environment](https://docs.python.org/3/library/venv.html). 
* Run `pipenv install --dev` to install the dev dependencies.
* Run `pipenv run lint` to run the linting.
* Run `pipenv run format` to format the code.
* Run `exit` to exit the shell

### Export Metadata

* Run `pipenv run python download_metadata.py [output_file]` to download all metadata from serlo.org
* Run `pipenv run python convert2rss.py [input_file] [output_file]` to convert the downloaded .json into .rss
