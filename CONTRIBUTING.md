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

o setup a development environment follow the instructions in this section. Once you have done so, you will
        be able to see live changes made to the SDK.

1. Create a directory that will hold all the `virtualenv` packages and files. Note that you will only need to
        run this command once.

macOS:

```
python3 -m venv venv
```

Windows:

```
py -m venv venv
```

2. Enable your terminal to use those files with this command. Note that this command will need to run each
time you want to return to your virtual environment.

macOS:

```
source venv/bin/activate
```

Windows:

```
venv\Scripts\activate.bat
```

3. Install requirements

```
pip3 install -r requirements.txt
```

4. You can now run the tests and the SDK with modifiable files.

For testing the sdk against a local running conjur, see [Manual testing](#manual-testing)

### Consuming the SDK locally

If you want to install the SDK using `pip` without uploading it to `pypi` you can run the following command from the
repo source dir:

`pip3 install .`

Note that the SDK requires python version >= than the one specified in the `setup.cfg` file under the `python_requires`
field.

## Testing

### Linting

In the project a linter is used to help enforce coding standards and provides refactoring suggestions.

```
./ci/test/test_linting.sh
```

### Unit tests

To run unit tests run:

```
nose2 -v -X -A '!integration' --config ./tests/unit_test.cfg
```

Or, for running it isolate inside a container:

```
./ci/test/test_unit
```

### Integration tests

To run integration tests run:

```
./ci/test/test_integration -e ubuntu
```
This will create a Conjur environment with an ubuntu container running the SDK's integration tests

### Manual testing

If you want preform some manual tests, run:
```
./ci/test/test_integration -e ubuntu -d
```
This will create a Conjur environment with an ubuntu container running in an interactive mode.
Now you can run python and manually test the SDK.

The connection parameters to conjur server are:
- conjur_url = `https://conjur-https`
- username = `admin`
- account = `dev`
- api_key = stored inside environment variable called `CONJUR_AUTHN_API_KEY` you can fetch the value by running 
  `echo $CONJUR_AUTHN_API_KEY`

## Releases

The following section provides instructions on what is needed to perform a Conjur CLI release.

### Checklist

1. Create a release branch from main
2. Verify that all changes related to this version are applied to `README`,`CHANGELOG` and `NOTICES` files
3. Verify that jenkins pipeline is green
4. Bump the version in `conjur_api.__init__.py` file
5. Merge the branch into main
6. Create and push a tag with the name of v<version_number> for example `v8.1.0`
7. Follow the jenkins pipeline and verify it is green, and `Publish to PyPI` step ended successfully
8. Log into https://pypi.org and verify that the package uploaded successfully
9. Import the package locally by running pip install conjur-api==<version_number> for example 
   `pip install conjur-api==8.1.0`
10. Create a release page from the tag.
    [You can assist github walkthrough](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
11. Write to the release page all the changes affecting this version (This can be taken from the changelog)
12. Update all stakeholders that the release ended successfully

## Contributing workflow

1. [Fork the project](https://help.github.com/en/github/getting-started-with-github/fork-a-repo)
2. [Clone your fork](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository)
3. Make local changes to your fork by editing files
3. [Commit your changes](https://help.github.com/en/github/managing-files-in-a-repository/adding-a-file-to-a-repository-using-the-command-line)
4. [Push your local changes to the remote server](https://help.github.com/en/github/using-git/pushing-commits-to-a-remote-repository)
5. [Create new Pull Request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork)

From here your pull request will be reviewed and once you've responded to all feedback it will be merged into the
project. Congratulations, you're a contributor!
