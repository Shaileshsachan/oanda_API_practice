import argparse
import re
import threading
import json
import logging
from oandapyV20 import API
from oandapyV20 import V20Error
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.orders as orders
from oandapyV20.contrib.requests import MarketOrderRequest, TakeProfitDetails, StopLossDetails
from oandapyV20.endpoints import instruments
import oandapyV20.endpoints.accounts as accounts

logging.basicConfig(
    filename="./connection.log",
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s : %(message)s',
)

logger = logging.getLogger(__name__)


def auth():
    accountID, token = None, None
    with open("account.txt") as f:
        accountID = f.read().strip()
    with open("token.txt") as f:
        token = f.read().strip()
    # print(accountID, token)
    return accountID, token


class Connection(object):

    def __init__(self):
        self.accountID, token = auth()
        self.client = API(access_token=token)


    def list_of_instruments(self):
        accountID, token = auth()
        client = API(access_token=token)
        r = accounts.AccountInstruments(accountID=accountID)
        rv = client.request(r)
        out_file = open("instrument_list.json", "w")
        json.dump(rv, out_file, indent=4)


    def order(self):

        accountId, token = auth()
        inst = []
        f = open('instrument_list.json')
        data = json.load(f)
        for i in data['instruments']:
            inst.append(i['name'])
            inst.append(i['tags'][0])
        print(inst)
        api = API(access_token=token)

        for i in inst:
            r = orders.OrderCreate(accountID=accountId, data=i)
            print("processing : {}".format(r))
            print("="*30)
            print(r.data)
            try:
                response = api.request(r)
            except V20Error as e:
                print("V20Error: {}".format(e))
            else:
                print("Resposne: {}\n{}".format(r.status_code, json.dumps(response, indent=2)))


class candle_data(object):
        price = ['M', 'B', 'A', 'BA', 'MBA']
        granularities = CandlestickGranularity().definitions.keys()
        parser = argparse.ArgumentParser(prog='candle-data')
        parser.add_argument('--nice', action='store_true', help='json indented')
        parser.add_argument('--count', default=0, type=int,
                            help='num recs, if not specified 500')
        parser.add_argument('--granularity', choices=granularities, required=True)
        parser.add_argument('--price', choices=price, default='M', help='Mid/Bid/Ask')
        parser.add_argument('--from', dest="From", type=str,
                            help="YYYY-MM-DDTHH:MM:SSZ (ex. 2016-01-01T00:00:00Z)")
        parser.add_argument('--to', type=str,
                            help="YYYY-MM-DDTHH:MM:SSZ (ex. 2016-01-01T00:00:00Z)")
        parser.add_argument('--instruments', type=str, nargs='?',
                            action='append', help='instruments')

        class Main(object):
            def __init__(self, api, accountID, clargs):
                self._accountID = accountID
                self.clargs = clargs
                self.api = api

            def main(self):
                def check_date(s):
                    dateFmt = "[\d]{4}-[\d]{2}-[\d]{2}T[\d]{2}:[\d]{2}:[\d]{2}Z"
                    if not re.match(dateFmt, s):
                        raise ValueError("Incorrect date format: ", s)

                    return True

                if self.clargs.instruments:
                    params = {}
                    if self.clargs.granularity:
                        params.update({"granularity": self.clargs.granularity})
                    if self.clargs.count:
                        params.update({"count": self.clargs.count})
                    if self.clargs.From and check_date(self.clargs.From):
                        params.update({"from": self.clargs.From})
                    if self.clargs.to and check_date(self.clargs.to):
                        params.update({"to": self.clargs.to})
                    if self.clargs.price:
                        params.update({"price": self.clargs.price})
                    for i in self.clargs.instruments:
                        r = instruments.InstrumentsCandles(instrument=i, params=params)
                        rv = self.api.request(r)
                        kw = {}
                        if self.clargs.nice:
                            kw = {"indent": self.clargs.nice}
                        print("{}".format(json.dumps(rv, **kw)))

            clargs = parser.parse_args()

            accountID, token = auth()
            api = API(access_token=token)
            try:
                m = api=api, accountID=accountID, clargs=clargs
            except V20Error as v20e:
                print("ERROR {} {}".format(v20e.code, v20e.msg))
            except ValueError as e:
                print("{}".format(e))
            except Exception as e:
                print("Unkown error: {}".format(e))

