Your configuration/preferences file is searched for in the following order:
  * Current directory
  * $XDG_CONFIG_HOME/googlecl or $HOME/.config/googlecl if $XDG_CONFIG_HOME is undefined
  * $XDG_CONFIG_DIRS or /etc/xdg if $XDG_CONFIG_DIRS is undefined (with /googlecl appended to each directory)
  * ~/.googlecl (The configuration file home from v0.9.8 and earlier)
The file is assumed to be called "config." If no file is found, one is created. On POSIX systems, in the directory specified by the second item in the above list. On other systems, in ~/.googlecl as before. You can also specify a file with the --config option.

1 Options
Each option description follows the format <name>: [<values>], <description>

1.1 All sections
Each of these values can be found in any section. The service being run will try to find the option in its own section, and failing that, in the GENERAL section.

  * <option>: [<string>], You can specify any option in the config file to use as a "general" case. When a command-line option is required (for example the username, or the title of an album created with Picasa), and nothing is passed in via the command line, this value will be used.
  * cap_results: [True, False], Cap the number of results to max_results. (That is, queries will only return one feed).
  * force_gdata_v1: [True, False] Force GoogleCL to use the code written for version 1 of the gdata API. True will disable some functionality (e.g. being able to see/manipulate arbitrary uploads to Docs), but may be required if you are unable to copy and paste the verification code in the browser. (For advanced users: This forces the import_service() function in the google script to load the "service" module even when the "client" module is available.)
  * fields: [<field>,<field>,...] Comma-separated (no spaces) list of attributes to print out when using the 'list' task and no fields are specified on the command line. For a list of valid fields, see the README / manual.
  * max_retries: [<integer>] Number of attempts to make for an operation that fails with a 302 "redirect" or 500 "internal" error. Set to 0 for infinite attempts.
  * max_results: [<integer>], Maximum number of results / entries to return. Sets the max-results query parameter of the uri. You can use this with cap_results to limit the amount of data being sent over the network.
  * regex: [True, False], Use regular expressions in matching titles.
  * retry_delay: [<decimal>] Number of seconds to wait after an error before trying another request. See max_retries.
  * skip_auth: [True, False], Don't check that the oauth access token read from file is actually valid. This is also a command line option, but will be set to True automatically once a valid access token is acquired and written to file.
  * tags_prompt: [True, False], Prompt for tags for each item being uploaded. (Not fully implemented).

1.2 Picasa
  * access: [public, private, protected], The default access level of the albums you create. Public means visible to all, private means unlisted, protected means sign-in required to view the album.

1.3 Docs
  * xxx_format: [<extension>], The extension to use for a type of document. The types of document are document, spreadsheet, presentation, and drawing. PDF files automatically use 'pdf' as the extension
  * xxx_editor: [<editor>], The editor to use for a type of document. The types of document are the same as the xxx_format option, plus pdf_editor in case you have a pdf editor.
  * decode_utf_8: [True,False], When you retrieve docs from the server, you can have GoogleCL try to remove the UTF-8 byte-order marker (BOM) from the document. Most users will not need to worry about this and want to leave this as undefined or false, but it's handy if you have an application sensitive to the BOM such as `less` or `tex`.
  * editor: [<editor>], The editor to use by default if the document type is not defined by an xxx_editor option. If this is not defined, will use the EDITOR environment variable instead.
  * format: [<extension>], The extension to use by default if the document type is not defined by an xxx_format option.
  * impatient_editors: [<editor1>,<editor2>...], Comma separated list of editors that will not wait for you to finish editing before exiting / returning from the command line. For example, setting this equal to "openoffice.org" (without the quotes) will stop GoogleCL from uploading any changes to Docs until you give it the OK.
  * invalid_filename_character_sub: [<string>] String to replace invalid filename characters with when editing or downloading documents.  For example, if this is set to !, downloading the file "unfriendly/filename" will rename the file to "unfriendly!filename".  Note that for editing, only the temporary file's name is changed -- it should remain the same online.

1.4 General
  * auth_browser: [<browser>], Browser to launch when authenticating the OAuth request token. Set this to "disabled" or "none" to prevent the launch of any browsers.
  * date_print_format: [<format string>], Format to use when printing date information. See the Python "time" documentation for formats (http://docs.python.org/library/time.html#time.strftime). For example: "%m %d at %H" for "<month> <day> at <hour>"
  * default_encoding: [<encoding>], If the terminal encoding is undefined, use this encoding. Odds are, if you are having unicode/ascii decode/encode issues, you'll need to use this setting (almost always 'utf-8' for non-windows users).
  * missing_field_value: [<string>], Placeholder string to use when listing an invalid attribute, for example, the url of a contact.
  * url_style: [site, direct], Which sub-style to use for listing urls. "Site" will typically put you at the website, while "direct" is usually a link directly to the resource.
