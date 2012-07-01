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


"""Service details and instances for the Finance service.

Some use cases:
Create portfolio:
  finance create --title "Some Portfolio" --currency USD

Delete portfolio:
  finance delete --title "Some Portfolio"

List portfolios:
  finance list

Create position:
  finance create-pos --title "Some Portfolio" --ticker NYSE:PCLN

Delete position:
  finance delete-pos --title "Some Portfolio" --ticker NYSE:PCLN

List positions:
  finance list-pos --title "Some Portfolio"

Create transaction:
  finance create-txn --title "Some Portfolio" --ticker NASDAQ:PCLN
          --currency USD --ttype Sell --price 346.60 --commission 7.7
          --shares 60 --date 2010-09-24 --notes "Stop loss on 347.01"

Delete transaction:
  finance delete-txn --title "Some Portfolio"
                             --ticker NASDAQ:PCLN --txnid 4

List transactions:
  finance list-txn --title "Some Portfolio" --ticker NASDAQ:PCLN

"""

__author__ = 'bartosh@gmail.com (Ed Bartosh)'

import logging
import datetime

import googlecl
import googlecl.calendar.date
from googlecl.base import BaseCL
from googlecl.service import BaseServiceCL
from googlecl.finance import SECTION_HEADER

from gdata.service import RequestError
from gdata.finance.service import FinanceService, PortfolioQuery, PositionQuery
from gdata.finance import PortfolioData, PortfolioEntry, TransactionEntry, \
                          TransactionData, Money, Price, Commission, \
                          PortfolioFeedFromString

LOG = logging.getLogger(googlecl.finance.LOGGER_NAME)

class FinanceServiceCL(FinanceService, BaseServiceCL):

  """Extends gdata.photos.service.FinanceService for the command line.

  This class adds some features focused on using Finance via an installed app
  with a command line interface.

  """

  def __init__(self, config):
    """Constructor."""
    FinanceService.__init__(self)
    BaseServiceCL.__init__(self, SECTION_HEADER, config)
    self.max_results = None

  def create_portfolio(self, title, currency):
    """Creates a portfolio.

    Args:
      title: Title to give the portfolio.
      currency: Currency associated with the portfolio (e.g. USD)
    """
    pfl = PortfolioEntry(
      portfolio_data=PortfolioData(currency_code=currency))
    pfl.portfolio_title = title
    try:
      return self.AddPortfolio(pfl)
    except RequestError, err:
      LOG.error('Failed to create portfolio: %s' % err[0]['body'])

  CreatePortfolio = create_portfolio

  def is_token_valid(self, test_uri='/data/feed/api/user/default'):
    """Check that the token being used is valid."""
    return BaseCL.IsTokenValid(self, test_uri)

  IsTokenValid = is_token_valid

  def get_portfolio_entries(self, title=None, returns=False, positions=False,
                            multiple=True):
    """Get portfolio entries or one entry.
    Args:
      title: string, portfolio title, could be regexp.
      returns: [optional] boolean, include returns into the result.
      positions: [optional] boolean, include positions into the result.
      multiple: boolean, return multiple entries if True
    Returns: list of portfolio entries
    """

    query = PortfolioQuery()
    query.returns = returns
    query.positions = positions

    uri = "/finance/feeds/default/portfolios/" + query.ToUri()

    if multiple:
      return self.GetEntries(uri, titles=title,
                             converter=PortfolioFeedFromString)
    else:
      entry = self.GetSingleEntry(uri, title=title,
                                  converter=PortfolioFeedFromString)
      if entry:
        return [entry]
      else:
        return []

  def get_portfolio(self, title, returns=False, positions=False):
    """Get portfolio by title.
    Args:
      title: string, portfolio title.
      returns: [optional] boolean, include returns into the result.
      positions: [optional] boolean, include positions into the result.

    Returns: portfolio feed object or None if not found.
    """

    entries = self.get_portfolio_entries(title=title, returns=returns,
                                         positions=positions, multiple=False)
    if entries:
      return entries[0]
    else:
      LOG.info('Portfolio "%s" not found' % title)
      return None

  def get_positions(self, portfolio_title, ticker_id=None,
                    include_returns=False):
    """Get positions in a portfolio.

    Args:
      portfolio_title: Title of the portfolio.
      ticker_id: Ticker, e.g. "NYSE:GLD"
      include_returns: Include returns in the portfolio data. Default False.

    Returns:
      List of positions in the portfolio, or empty list if no positions found
      matching the criteria.
    """
    # XXX:Would be nice to differentiate between positions.  Right now, just get
    # all of them.
    pfl = self.get_portfolio(portfolio_title, returns=include_returns,
                               positions=True)
    if not pfl:
      LOG.debug('No portfolio to get positions from!')
      return []
    if not pfl.positions:
      LOG.debug('No positions found in this portfolio.')
      return []

    if ticker_id is not None:
      positions = [self.GetPosition(portfolio_id=pfl.portfolio_id,
                                      ticker_id=ticker_id)]
    else:
      positions = self.GetPositionFeed(portfolio_entry=pfl).entry
    return positions

  def get_transactions(self, portfolio_title, ticker_id, transaction_id=None):
    pfl = self.get_portfolio(portfolio_title)
    if not pfl:
      LOG.debug('No portfolio to get transactions from!')
      return []
    if transaction_id:
      transactions = [self.GetTransaction(portfolio_id=pfl.portfolio_id,
                                            ticker_id=ticker_id,
                                            transaction_id=transaction_id)]
    else:
      transactions = self.GetTransactionFeed(portfolio_id=pfl.portfolio_id,
                                             ticker_id=ticker_id).entry
    return transactions

  def create_transaction(self, pfl, ttype, ticker, shares=None, price=None,
                         currency=None, commission=None, date='', notes=None):
    """Create transaction.

    Args:
      pfl: portfolio object.
      ttype: string, transaction type, on of the 'Buy', 'Sell',
             'Short Sell', 'Buy to Cover'.
      shares: [optional] decimal, amount of shares.
      price: [optional] decimal, price of the share.
      currency: [optional] string, portfolio currency by default.
      commission: [optional] decimal, brocker commission.
      date: [optional] string, transaction date,
            datetime.now() by default.
      notes: [optional] string, notes.

    Returns:
      None if transaction created successfully, otherwise error string.
    """
    if not currency:
      currency = pfl.portfolio_data.currency_code
    if date is None:
      # if date is not provided from the command line current date is set
      date = datetime.datetime.now().isoformat()
    elif date is '':
      # special case for create position task. date should be set to None
      # to create empty transaction. See detailed explanations in
      # the _run_create_position function below
      date = None
    else:
      parser = googlecl.calendar.date.DateParser()
      date = parser.parse(date).local.isoformat()

    if price is not None:
      price = Price(money=[Money(amount=price, currency_code=currency)])
    if commission is not None:
      commission = Commission(money=[Money(amount=commission,
                                             currency_code=currency)])
    txn = TransactionEntry(transaction_data=TransactionData(
        type=ttype, price=price, shares=shares, commission=commission,
        date=date, notes=notes))

    try:
      return self.AddTransaction(txn, portfolio_id=pfl.portfolio_id,
                                 ticker_id=ticker)
    except RequestError, err:
      LOG.error('Failed to create transaction: %s' % err[0]['body'])


SERVICE_CLASS = FinanceServiceCL

# Local Variables:
# mode: python
# py-indent-offset: 2
# indent-tabs-mode: nil
# tab-width: 2
# End:
