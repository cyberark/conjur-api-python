# Contributing

For general contribution and community guidelines, please see the [community repo](https://github.com/cyberark/community).
In particular, before contributing please review our [contributor licensing guide](https://github.com/cyberark/community/blob/main/CONTRIBUTING.md#when-the-repo-does-not-include-the-cla)
to ensure your contribution is compliant with our contributor license agreements.


## Table of Contents

- [Development](#development)
- [Testing](#testing)
- [Releases](#releases)
- [Contributing](#contributing-workflow)

## Development

To set up a development environment follow the instructions in this section.

1. Create a directory that will hold all the `virtualenv` packages and files. 
   Note: You need to run this command once only.

macOS:

```
python3 -m venv venv
```

Windows:

```
py -m venv venv
```

2. Enable your terminal to use the files in this directory using this command. Note: This command needs to run each
time you return to your virtual environment.

macOS:

```
source venv/bin/activate
```

Windows:

```
venv\Scripts\activate.bat
```

3. Install the requirements

```
pip3 install -r requirements.txt
```

You can now run tests and the SDK with modifiable files.

To test the SDK against a locally running Conjur Server, see [Manual testing](#manual-testing)

### Consuming the SDK locally

If you want to install the SDK using `pip` without uploading it to `pypi` you can run the following command from the
repo source dir:

`pip3 install .`

Note that the SDK requires Python version >= than the one specified in the `setup.cfg` file under the `python_requires`
field.

## Testing

### Linting

In the project, a linter is used to help enforce coding standards and provides refactoring suggestions.

```
./ci/test/test_linting.sh
```

### Unit tests

To run the unit test isolated inside a container, run:

```
./ci/test/test_unit.sh
```

### Integration tests

To run integration tests run:

```
./ci/test/test_integration -e ubuntu
```
This creates a Conjur environment with an Ubuntu container running the SDK's integration tests.

### Manual testing

To perform manual tests, run:
```
./ci/test/test_integration -e ubuntu -d
```
This creates a Conjur environment with an Ubuntu container running in interactive mode.
You can now run Python and manually test the SDK.

The connection parameters to Conjur are:
- conjur_url = `https://conjur-https`
- username = `admin`
- account = `dev`
- api_key = stored inside the `CONJUR_AUTHN_API_KEY` environment variable. You can fetch the value by running 
  `echo $CONJUR_AUTHN_API_KEY`

## Releases

This section describes the requirements for releasing a Conjur python SDK.

### Checklist

1. Create a release branch from main
2. Verify that all changes related to the version are applied to `README`,`CHANGELOG` and `NOTICES` files
3. Verify that Jenkins Pipeline is green
4. Bump the version in `conjur_api.__init__.py` file
5. Merge the branch into main
6. Create and push a tag using the following naming convention: v<version_number>, for example `v8.1.0`
7. Follow the Jenkins Pipeline and verify that it's green and that `Publish to PyPI` step ended successfully
8. Log into https://pypi.org and verify that the package uploaded successfully
9. Import the package locally by running `pip install conjur-api==<version_number>`, for example 
   `pip install conjur-api==8.1.0`
10. Create a release page from the tag.
    [Click here for assistance](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
11. On the releases page, write all the changes affecting this version (This can be taken from the changelog)
12. Update all stakeholders that the release was completed successfully

## Contributing workflow

1. [Fork the project](https://help.github.com/en/github/getting-started-with-github/fork-a-repo)
2. [Clone your fork](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository)
3. Make local changes to your fork by editing files
3. [Commit your changes](https://help.github.com/en/github/managing-files-in-a-repository/adding-a-file-to-a-repository-using-the-command-line)
4. [Push your local changes to the remote server](https://help.github.com/en/github/using-git/pushing-commits-to-a-remote-repository)
5. [Create new Pull Request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork)

From here your pull request will be reviewed and once you've responded to all feedback it will be merged into the
project. Congratulations, you're a contributor!
