#!/bin/bash

TOUCH_PREFIX="tested_"
GOOGLE_SH=./google.py

# List of commands to set by each function
declare -a commands

# Commands to run for cleaning up test account
#declare -a cleanup_commands

function blogger {
  echo 'This is my post from a file\nIt contains a few line breaks, but not much else.' > test_post.txt
  commands[0]='blogger post --tags delete test_post.txt'
  commands[1]='blogger list --fields title,author'
  commands[2]='blogger post -n CL_post_test "This is my post from a command line"'
  commands[3]='blogger tag CL_post_ delete'
  commands[4]='blogger delete CL_post_test test_post ^New post$ --yes'
}

function calendar {
  commands[0]='calendar add "test event at 5pm on 10/10/10"'
  commands[1]='calendar add "test event at midnight on 10/10/10"'
  commands[2]='calendar add "test event today at 3" --reminder 1h'
  commands[3]='calendar today'
  commands[4]='calendar list --date 2010-10-10'
  commands[5]='calendar delete --date 10/10/10 test --yes'
  commands[6]='calendar delete --date today@3 test'
}

function contacts {
  echo -e 'contacts csv1, test_csv1@eh.com\ncontacts csv2, test_csv2@eh.com' > contacts.csv
#  commands[0]='contacts add "contacts test1,test_email1@nowhere.com" "contacts test2,test_email2@nowhere.com"'
  commands[1]='contacts add contacts.csv'
  commands[2]='contacts add "contacts test1,test_email1@nowhere.com"'
  commands[3]='contacts list contacts'      # Assumes that "fields" is specified in config file
  commands[4]='contacts add-groups test_group'
  commands[5]='contacts list-groups'
  commands[6]='contacts delete-groups test_group --yes'
  commands[7]='contacts delete test[0-9]?_?'
}

function docs {
  echo -e 'This is a document that I am about to upload.' > test_doc.txt
  commands[0]='docs upload test_doc.txt'
  commands[1]='docs get test_doc test_download.txt'
  commands[2]='docs list --fields title,url-direct --delimiter ": "'
  commands[3]='docs edit test_doc --editor vim'
  commands[4]='docs delete test_doc'
}

function finance {
  commands[0]='finance create my_empty_pfl USD'
  commands[1]='finance create-pos my_empty_pfl NASDAQ:MSFT'
  commands[2]='finance create-txn my_empty_pfl NASDAQ:MSFT Sell'
  commands[3]='finance list'
  commands[4]='finance list-pos --title=.*'
  commands[5]='finance list-txn --title=.* --ticker=NASDAQ:MSFT'
  commands[6]='finance delete-txn'
  commands[7]='finance delete-pos'
  commands[8]='finance delete my_empty'
}

function picasa {
  commands[0]='picasa create test_album --tags "test, Disney World, florida, vacation" ~/testphotos/IMG_9882.JPG'
  commands[1]='picasa create test_album2'
  commands[2]='picasa list --fields title,url-site -q test'
  commands[3]='picasa list-albums'
  commands[4]='picasa delete "nosuchalbumexists"'
  commands[5]='picasa get "test_album" .'
  commands[6]='picasa post -n "test_album" --tags "Disney World, florida, vacation" ~/testphotos/IMG_9883.JPG'
  commands[7]='picasa tag "nosuchalbumexists" -t tag1,tag2'
  commands[8]='picasa tag "test_album" -t --,tag1,tag2'
  commands[9]='picasa delete test_album'
}

function youtube {
  commands[0]='youtube post ~/testclips/fighting_cats4.mp4 -n "New test cat movie" -s "More cats on youtube" Education --tags test,cats'
  commands[1]='youtube list'
  commands[2]='youtube tag cat optionless_tag'
  commands[3]='youtube tag -n "D_N_E" -t wontgothrough'
  commands[4]='youtube post ~/D_N_E -n failure -c Education'
  commands[5]='youtube delete New'
}

function goog_help {
  commands[0]="help"
}

prompt_quit() {
  echo Hit Ctrl-C again to exit, enter to skip current command
  read junk
}

trap prompt_quit INT

if [ ${#@} -eq 1 ] && [ $@ == all ]; then
  TASKS=( blogger calendar contacts docs picasa youtube )
else
  TASKS=$@
fi

for task in ${TASKS[*]}
do
  unset commands
  echo -e "\n"
  echo ===$task===
  if [ $task == blogger ]; then
    blogger
  fi
  if [ $task == calendar ]; then
    calendar
  fi
  if [ $task == contacts ]; then
    contacts
  fi
  if [ $task == docs ]; then
    docs
  fi
  if [ $task == finance ]; then
    finance
  fi
  if [ $task == picasa ]; then
    picasa
  fi
  if [ $task == youtube ]; then
    youtube
  fi
  if [ $task == help ]; then
    goog_help
  fi
  # Make note of which tasks have been run, for cleanup later
  eval touch "$TOUCH_PREFIX$task"
  for index in ${!commands[*]}; do
    echo -e "\n===${commands[$index]}"
    eval $GOOGLE_SH ${commands[$index]}
  done
done
