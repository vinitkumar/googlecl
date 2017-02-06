#Google CL

[![Build Status](https://travis-ci.org/vinitkumar/googlecl.svg?branch=master)](https://travis-ci.org/vinitkumar/googlecl)

GoogleCL is a command line utility to use google services like youtube, blogger etc.


## Credits

It was originally written by [Tom H. Miller](https://github.com/TomMiller) from Google and was hosted
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

The authentication has been ported to Oauth2 but the due to breaking changes to
the google data apis not everything works yet.

When using for the first time, it asks to authenticate using a google account
and saves the token and everything else requires in a ~/.googlecl.conf file.

Any further api calls are authenticated automatically using this file and if
the access token is refreshed it is also written back to this file.

```sh
$ python src/google.py picasa list --title=vinit

# Results of the query below

Refreshing access_token
Auto Backup,https://picasaweb.google.com/1da353532827267524qeqe3419?alabel=small_instant_upload
vinit ,https://picasaweb.google.com/106645023605660581419/636437447265237483335626262
```

The porting is still in progress but some part works now and more will be near
future as I get more time to complete the porting.

## Contribution:

Few things should be kept in notice before contributing:

- Few changes in the documentation structure and format(Markdown) has
been done.
- Pycco has been used to generate documentation. I believe in Literate
programming and felt that it would be easier for developers to
understand the existing code.
- Follow the same styleguide and naming conventions as present in the
code.
- Follow [github flow] (http://guides.github.com/overviews/flow/), It is
a dead simple way to deal with development using and I prefer it.
- Branch naming could be issue related. Say there is issue #23, create a
branch name feature/fix-issue23 or bugfix/issue23. It would really help.

Thanks!
