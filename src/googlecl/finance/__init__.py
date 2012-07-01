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
import googlecl
import inspect
import logging
import os
import sys
from googlecl.base import Task


safe_encode = googlecl.safe_encode
service_name = __name__.split('.')[-1]
LOGGER_NAME = __name__
SECTION_HEADER = service_name.upper()
LOG = logging.getLogger(LOGGER_NAME)


class BaseFormatter(object):
  """Base class for formatters."""

  def __init__(self, avail_fields, fields, sep=','):
    """Init formatter
    Args:
      avail_fields: list of tuples [(field_name, format_spec), ...] for all
                    possible fields
      fields: string, list of <sep>-separated requested fields names.
      sep: string, separator, comma by default
    """
    if fields:
      self.fields = fields.split(sep)
    else:
      self.fields = [item[0] for item in avail_fields]

    self.avail_fields = avail_fields
    avail_dict = dict(avail_fields)
    self.format = ' '.join(avail_dict[name] for name in self.fields)

  @property
  def header(self):
    """Make output header.
    Uses names of available fields as column headers. replaces
    '_' with ' ' and capitalizes them. Utilizes the same format as
    used for body lines: self.format

    Returns: string, header.
    """
    return self.format % \
        dict([(item[0], item[0].replace('_', ' ').capitalize()) \
                for item in self.avail_fields])

  def get_line(self, entry):
    """Get formatted entry. Abstract method.
    Args:
      entry: entry object
    Returns:
      string, formatted entry.
    """
    raise NotImplementedError("Abstract method %s.%s called" % \
                                (self.__class__.__name__,
                                 inspect.stack()[0][3] ))

  def output(self, entries, stream=sys.stdout):
    """Output list of entries to the output stream.

    Args:
      entries: list of entries.
      stream: output stream.
    """

    if self.header:
      stream.write(self.header + os.linesep)
    for entry in entries:
      stream.write(self.get_line(entry) + os.linesep)

class PortfolioFormatter(BaseFormatter):
  avail_fields = [('id', '%(id)3s'), ('title', '%(title)-15s'),
                  ('curr', '%(curr)-4s'),
                  ('gain', '%(gain)-10s'),
                  ('gain_persent', '%(gain_persent)-14s'),
                  ('cost_basis', '%(cost_basis)-10s'),
                  ('days_gain', '%(days_gain)-10s'),
                  ('market_value', '%(market_value)-10s')]

  def __init__(self, fields):
    super(self.__class__, self).__init__(self.avail_fields, fields)

  def get_line(self, entry):
    data =  entry.portfolio_data
    return self.format % \
      {'id': entry.portfolio_id, 'title': entry.portfolio_title,
       'curr': data.currency_code,
       'gain': data.gain and data.gain.money[0].amount,
       'gain_persent': '%-14.2f' % (float(data.gain_percentage) * 100,),
       'cost_basis': data.cost_basis and data.cost_basis.money[0].amount,
       'days_gain': data.days_gain and data.days_gain.money[0].amount,
       'market_value': data.market_value and data.market_value.money[0].amount
      }

class PositionFormatter(BaseFormatter):
  avail_fields = [('ticker', '%(ticker)-14s'), ('shares', '%(shares)-10s'),
                  ('gain', '%(gain)-10s'),
                  ('gain_persent', '%(gain_persent)-14s'),
                  ('cost_basis', '%(cost_basis)-10s'),
                  ('days_gain', '%(days_gain)-10s'),
                  ('market_value', '%(market_value)-10s')]

  def __init__(self, fields):
    super(self.__class__, self).__init__(self.avail_fields, fields)

  def get_line(self, entry):
    data =  entry.position_data
    return self.format % \
      {'ticker': entry.ticker_id, 'shares': data.shares,
       'gain': data.gain and data.gain.money[0].amount,
       'gain_persent': '%-14.2f' % (float(data.gain_percentage) * 100,),
       'cost_basis': data.cost_basis and data.cost_basis.money[0].amount,
       'days_gain': data.days_gain and data.days_gain.money[0].amount,
       'market_value': data.market_value and data.market_value.money[0].amount
      }

class TransactionFormatter(BaseFormatter):
  avail_fields = [('id', '%(id)-3s'), ('type', '%(type)-12s'),
                  ('shares', '%(shares)-10s'), ('price', '%(price)-10s'),
                  ('commission', '%(commission)-10s'),
                  ('date', '%(date)-10s'), ('notes', '%(notes)-30s')]

  def __init__(self, fields):
    super(self.__class__, self).__init__(self.avail_fields, fields)

  def get_line(self, entry):
    data = entry.transaction_data
    if data.date:
      data.date = data.date[:10] # stip isoformat tail
    return self.format % \
      {'id': entry.transaction_id, 'type': data.type, 'shares': data.shares,
       'price': data.price.money[0].amount,
       'commission': data.commission.money[0].amount,
       'date': data.date or '', 'notes': data.notes or ''}


#===============================================================================
# Each of the following _run_* functions execute a particular task.
#
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================
# Portfolio-related tasks
def _run_create(client, options, args):
  client.CreatePortfolio(options.title, options.currency)


def _run_delete(client, options, args):
  entries = client.get_portfolio_entries(options.title, positions=True)
  if entries:
    client.DeleteEntryList(entries, 'portfolio', options.prompt)


def _run_list(client, options, args):
  entries = client.get_portfolio_entries(returns=True)
  if entries:
    PortfolioFormatter(options.fields).output(entries)
  else:
    LOG.info('No portfolios found')


# Position-related tasks
def _run_create_position(client, options, args):
  # Quote from Developer's Guide:
  #   You can't directly create, update, or delete position entries;
  #   positions are derived from transactions.
  #   Therefore, to create or modify a position, send appropriate
  #   transactions on that position.
  pfl = client.get_portfolio(options.title, positions=True)
  if pfl:
    # create empty transaction
    client.create_transaction(pfl, "Buy", options.ticker)


def _run_delete_positions(client, options, args):
  positions = client.get_positions(portfolio_title=options.title,
                                   ticker_id=options.ticker)
  client.DeleteEntryList(positions, 'position', options.prompt,
                 callback=lambda pos: client.DeletePosition(position_entry=pos))


def _run_list_positions(client, options, args):
  positions = client.get_positions(options.title, options.ticker,
                                   include_returns=True)
  if positions:
    PositionFormatter(options.fields).output(positions)
  else:
    LOG.info('No positions found in this portfolio')


# Transaction-related tasks
def _run_create_transaction(client, options, args):
  pfl = client.get_portfolio(options.title)
  if pfl:
    client.create_transaction(pfl, options.ttype, options.ticker,
                              options.shares, options.price,
                              options.currency, options.commission,
                              options.date, options.notes)


def _run_delete_transactions(client, options, args):
  transactions = client.get_transactions(portfolio_title=options.title,
                                         ticker_id=options.ticker,
                                         transaction_id=options.txnid)
  client.DeleteEntryList(transactions, 'transaction', options.prompt)


def _run_list_transactions(client, options, args):
  transactions = client.get_transactions(portfolio_title=options.title,
                                         ticker_id=options.ticker,
                                         transaction_id=options.txnid)
  TransactionFormatter(options.fields).output(transactions)


TASKS = {'create': Task('Create a portfolio',
                        callback=_run_create,
                        required=['title', 'currency']),
         'delete': Task('Delete portfolios',
                        callback=_run_delete,
                        required=['title']),
         'list':   Task('List portfolios',
                        callback=_run_list,
                        optional=['fields']),
         'create-pos': Task('Create position',
                            callback=_run_create_position,
                            required=['title', 'ticker']),
         'delete-pos': Task('Delete positions',
                            callback=_run_delete_positions,
                            required=['title'],
                            optional=['ticker']),
         'list-pos':  Task('List positions',
                           callback=_run_list_positions,
                           required=['title'],
                           optional=['fields']),
         'create-txn': Task('Create transaction',
                            callback=_run_create_transaction,
                            required=['title', 'ticker', 'ttype',
                                      'shares', 'price'],
                            optional=['shares', 'price', 'date',
                                      'commission', 'currency', 'notes']),
         'list-txn': Task('List transactions',
                          callback=_run_list_transactions,
                          required=['title', 'ticker']),
         'delete-txn': Task('Delete transactions',
                            callback=_run_delete_transactions,
                            required=['title', 'ticker'],
                            optional=['txnid']),
}
