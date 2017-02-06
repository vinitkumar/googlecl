#Google CL

[![Build Status](https://travis-ci.org/vinitkumar/googlecl.svg?branch=master)](https://travis-ci.org/vinitkumar/googlecl)

GoogleCL is a command line utility to use google services like picasa, youtube, blogger etc.


## Credits

It was originally written by [Tom H. Miller](https://github.com/TomMiller) at Google and was hosted
[here](https://code.google.com/p/googlecl/).

This is a github fork of the project.

## Installation

Installation is simple, Just run this command in your shell:

```bash
git clone https://github.com/vinitkumar/googlecl.git
cd googlecl
python setup.py install
```

## Usage

The authentication has been ported to Oauth2 but due to the breaking changes gdata-python client there
are still some rough edges.

When using for the first time,it would ask to authenticate using a google account
and will save the credentials ~/.googlecl.conf file.

All further API calls are authenticated automatically using this file and if
the access token gets refreshed it is also written back to this file.

```sh
$ python src/google.py picasa list --title=vinit

# Results of the query below

Refreshing access_token
Auto Backup,https://picasaweb.google.com/1da353532827267524qeqe3419?alabel=small_instant_upload
vinit ,https://picasaweb.google.com/106645023605660581419/636437447265237483335626262
```
Porting is still a WIP but it will get completed as I manage to spend more time on it.

## Contribution:

Few things should be kept in notice before contributing:

- Follow PEP8, earlier code used 2-space indent. I changed it to 4 spaces as pretty much every other codebase has same conventions.
- Send a pull-request and clearly mention what bug or feature you are working on.

Thanks :)
