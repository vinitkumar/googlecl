# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Service details and instances for the Contacts service.

Some use cases:
Add contacts:
  contacts add "Bob Smith, bob@smith.com" "Jim Raynor, jimmy@noreaster.com"

List contacts:
  contacts list title,email

"""
from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import logging
import os.path
import googlecl.contacts

LOG = logging.getLogger(googlecl.contacts.LOGGER_NAME + '.base')


class ContactsBaseCL(object):
  """Class inherited by either ContactsServiceCL or ContactsClientCL. """

  def add_contacts(self, contacts):
    """Add contact(s).

    Args:
      contacts: Contact(s) to add. This is either a path to a CSV with
          contact information, or a list of comma separated contact data.
    """
    successes = []
    for contact in contacts:
      if os.path.exists(contact):
        with open(contact, 'r') as contacts_csv_file:
          for line in contacts_csv_file:
            entry = self.add_single_contact(line)
            if entry:
              successes.append(entry)
      else:
        entry = self.add_single_contact(contact)
        if entry:
          successes.append(entry)
    return successes

  AddContacts = add_contacts

  def add_single_contact(self, contact_string, delimiter=',',
                         fields=('name', 'email')):
    """Add contact.

    Args:
      contact_string: String representing fields of a contact to add.
      delimiter: Delimiter for fields in the contact string. Default ','
      fields: Fields contained in the contact string. Default ('name', 'email')

    Returns:
      ContactEntry with fields filled in, or None if the contact string did not
      contain the data described by fields.
    """
    num_fields = len(fields)
    values = contact_string.split(delimiter, num_fields)
    if num_fields != len(values):
      LOG.error('String did not have correct number of fields!')
      LOG.debug('Expected fields %s', fields)
      LOG.debug('Got string %s', contact_string)
      return None
    new_contact = self._get_contact_entry()
    for i in range(num_fields):
      if fields[i] == 'name':
        self._add_name(values[i].strip(), new_contact)
      elif fields[i] == 'email':
        self._add_email(values[i].strip(), new_contact)
    return self.CreateContact(new_contact)

  AddSingleContact = add_single_contact
