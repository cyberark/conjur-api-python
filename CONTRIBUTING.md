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

Releases should be created by maintainers only. To create and promote a release, follow the instructions in this section.

### Update the changelog and notices

**NOTE:** If the Changelog and NOTICES.txt are already up-to-date, skip this
step and promote the desired release build from the main branch.

1. Create a new branch for the version bump.
1. Based on the changelog content, determine the new version number and update.
1. Review the git log and ensure the [changelog](CHANGELOG.md) contains all
   relevant recent changes with references to GitHub issues or PRs, if possible.
1. Review the changes since the last tag, and if the dependencies have changed
   revise the [NOTICES](NOTICES.txt) to correctly capture the included
   dependencies and their licenses / copyrights.
1. Commit these changes - `Bump version to x.y.z` is an acceptable commit
   message - and open a PR for review.

### Release and Promote

1. Merging into the main branch will automatically trigger a release build.
   If successful, this release can be promoted at a later time.
1. Jenkins build parameters can be utilized to promote a successful release
   or manually trigger aditional releases as needed.
1. Reference the [internal automated release doc](https://github.com/conjurinc/docs/blob/master/reference/infrastructure/automated_releases.md#release-and-promotion-process)
for releasing and promoting.

### Manual Verification

1. Log into [PyPI](https://pypi.org)and verify that the package uploaded successfully
1. Import the package locally by running `pip install conjur-api==<version_number>`,
for example `pip install conjur-api==0.0.5`
1. Verify git release page from the tag.
[Click here for assistance](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)


## Contributing workflow

1. [Fork the project](https://help.github.com/en/github/getting-started-with-github/fork-a-repo)
2. [Clone your fork](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository)
3. Make local changes to your fork by editing files
3. [Commit your changes](https://help.github.com/en/github/managing-files-in-a-repository/adding-a-file-to-a-repository-using-the-command-line)
4. [Push your local changes to the remote server](https://help.github.com/en/github/using-git/pushing-commits-to-a-remote-repository)
5. [Create new Pull Request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork)

From here your pull request will be reviewed and once you've responded to all feedback it will be merged into the
project. Congratulations, you're a contributor!
