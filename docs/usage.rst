This document is a quick-guide on getting up to speed with the new version of GoogleCL.

version 0.9.13
  * Bugfixes only. Booooooring.

version 0.9.12
  * --access will take a variety of text to set access levels on the following items during creation:
      Blogger posts
      Picasa albums
      YouTube videos
    Some example text that should work: public, private, draft, unlisted, link only. --draft will still be honored for Blogger.
  * --date takes way, way more that just YYYY-MM-DD format. See the README and example scripts for a detailed list.
  * --photo will act like a "--title for photos" for Picasa, allowing you to list, get, delete, or tag only certain photos.
  * --summary can be given to picasa tag and post, to change the captions of photos being modified by those commands.
  * Got rid of the following config file options: tags_prompt, delete_by_default, delete_prompt. Essentially, tags_prompt is now always False, and delete_by_default is always False (the default values for these options). delete_prompt was obsoleted by the command line argument --yes, which will answer "yes" to all "are you sure" deletion prompts.
  * url-download is now a list field for picasa photos.
  * You can disable automatic launching of the browser during authentication be setting auth_browser to "disabled" in the config file.
	* Input can be piped into GoogleCL by inserting a "_" or "__" as a command line argument. "_" will take characters sitting on stdin and treat them as a single argument, not expanding or splitting the string. "__" will split the data. For example:
		$ echo "These are my files" > list.txt

	Entering
		$ cat list.txt | google docs upload __
	is equivalent to 
		$ google docs upload These are my files
	while
		$ cat list.txt | google docs upload _
	is equivalent to
		$ google docs upload "These are my files"
	(Note that the echo command will actually produce a newline that will be at the end of 'files' -- this is just a quick example)

	You can pipe data directly to options as well, but only as single arguments. For example,
	$ cat file | google docs upload --title __
	Will set the title to "__" and ignore the value from "cat file"

version 0.9.11
  * --force-auth and --skip-auth will let you specify if GoogleCL should verify the oauth access token it has on file for the service being used. After the first valid access token retrieved, --skip-auth is set in your config file as True. You can set this value to False to force a validation step on every run. The validation step is an authenticated request to Google to retrieve a small amount of data -- removing this step can yield a significant decrease in execution time for slow connections.
  * 'list_fields' has been shortened to 'fields' in the config file, and the --fields option is introduced. Thanks to the "read required options from the argument list" ability also introduced in this version, your old scripts should be alright without specifying --fields. You can also change the XXX_fields entries in the config file to just fields.
  * --src and --dest options were added. Conceptually, --src indicates data being transmitted to Google and --dest is where you want to put data received from Google. They mostly replaced command line arguments that were flapping in the wind (i.e. not associated with a command line option, and had an "arguments description" in the --help output).This seems like a pain in the neck, but read the next point where we introduce...
  * Positional autofill for command line arguments! Read the --help output or man page, but in a nutshell, GoogleCL will figure out what argument corresponds to which option based on the order of the arguments and what the configuration file has specified. You should notice significantly less wear and tear on your hyphen key.
  * Multiple arguments can be given to options.src and options.title by just sticking them on the command line. This should flow naturally with the "positional autofill" mentioned above. For example:
    $ google contacts list huey dewy louie
  will list all of your obnoxious nephews.
  * Picasa got a whole mess of new list fields: distance, ev, exposure (aka shutter, speed), flash, focallength, fstop, imageUniqueID (aka ia), iso, make, model, time (aka when).

version 0.9.10
  * List "styles" have been renamed to list "fields". If you have a custom list_style entry in your config file, rename it to list_fields to make it work again.
  * v2 and v3 support for gdata for the average user means that you can now see and download non-converted files that you've uploaded through the web interface, and list more details about your contacts. See the README section on the list task.
  * Config file option force_gdata_v1 lets you use the older versions in the library written for Docs and Contacts. The primary purpose of this option is to avoid copying and pasting a verification code from the browser into GoogleCL. It means that you won't benefit from any v2 / v3 upgrades to GoogleCL like the ones mentioned before.
  * Started following the XDG Base Directory Specification (http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html). GoogleCL will still look for config files and access tokens in the old directory (~/.googlecl), but may not in the future.
