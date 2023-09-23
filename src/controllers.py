import json
import asyncio
import datetime
from tda import auth
from src import config, db
from tda.client import Client
from tda.auth import easy_client
from tda.streaming import StreamClient


flag = False
resp = None


def getOptions(symbol, strike='all'):
    resp = _getOptions(symbol, strike)
    if resp:
        return resp
    else:
        print(resp)
        return {
            'message': 'Something went wrong'
        }, 500


def getAllStrikes(symbol):
    strikes = _getAllStrikes(symbol)
    if strikes:
        return {
            'strikes': strikes
        }, 200
    else:
        return {
            'message': 'Something went wrong'
        }, 500


def getAllExpirations(symbol):
    expirations = _getAllExpirations(symbol)
    if expirations:
        return {
            'expirations': expirations
        }, 200
    else:
        return {
            'message': 'Something went wrong'
        }, 500


def getInfo(symbol):
    data = _info(symbol)
    if data:
        return data, 200
    else:
        return {
            'message': 'Something went wrong'
        }, 500


def getAllSymbols(symbol, _range, save, minDate, maxDate):
    try:
        optionsData = _getOptions(symbol)
        symbols = _parseOptionData(optionsData[0], _range, minDate, maxDate)
        if save:
            db.insert_contracts(symbols, symbol)
            db.set_intruption(True)
        return symbols, 200
    except Exception as e:
        print(str(e))
        return {
            'message': 'Something went wrong',
            'error': str(e)
        }, 500


def getOrders(ts, symbol, page, limit):
    try:
        return {
            "orders": db.get_books(ts, symbol, page, limit)
        }, 200
    except Exception as e:
        print(str(e))
        return {
            'message': 'Something went wrong'
        }, 500


def filter_contracts_by_date(contracts, minDate=None, maxDate=None):
    filtered_contracts = []
    for contract in contracts:
        expiration_date = datetime.datetime.fromtimestamp(
            contract['expirationDate']/1000)
        if minDate is not None and expiration_date < minDate:
            continue
        if maxDate is not None and expiration_date > maxDate:
            continue
        filtered_contracts.append(contract)
    return filtered_contracts


def _parseOptionData(data, _range, minDate=None, maxDate=None):
    reqkeys = ["putExpDateMap", "callExpDateMap"]
    symbols = []
    toReturn = []
    for reqKey in reqkeys:
        try:
            price = data['underlyingPrice']
            putExpDateMap = data[reqKey]
            putExpDateMapKeys = list(putExpDateMap.keys())
            for putExpDateMapKey in putExpDateMapKeys:
                _keys = list(data[reqKey][putExpDateMapKey].keys())
                for _key in _keys:
                    strikes = data[reqKey][putExpDateMapKey][_key]
                    for strike in strikes:
                        _strik = {}
                        contractPrice = strike['strikePrice']
                        if price - _range <= contractPrice <= price + _range:
                            _strik["symbol"] = strike['symbol']
                            _strik["openInterest"] = strike['openInterest']
                            expiration_date = strike['expirationDate']/1000
                            if minDate is not None and expiration_date < minDate:
                                continue
                            if maxDate is not None and expiration_date > maxDate:
                                continue
                            symbols.append(_strik)
        except Exception as e:
            # raise e
            pass
    quota = 25
    puts = list(filter(lambda x: "P" in x['symbol'].split("_")[-1], symbols))
    calls = list(filter(lambda x: "C" in x['symbol'].split("_")[-1], symbols))
    sortedPuts = sorted(puts, key=lambda x: x['openInterest'], reverse=True)
    sortedCalls = sorted(calls, key=lambda x: x['openInterest'], reverse=True)
    if len(puts) >= quota and len(calls) >= quota:
        toReturn.extend([s['symbol'] for s in sortedPuts[:quota]])
        toReturn.extend([s['symbol'] for s in sortedCalls[:quota]])
    elif len(calls) >= quota and len(puts) < quota:
        extendedQuota = quota + (quota - len(puts))
        toReturn.extend([s['symbol'] for s in sortedPuts])
        if len(sortedCalls) <= extendedQuota:
            toReturn.extend([s['symbol'] for s in sortedCalls])
        else:
            toReturn.extend([s['symbol'] for s in sortedCalls[:extendedQuota]])
    elif len(puts) >= quota and len(calls) < quota:
        extendedQuota = quota + (quota - len(calls))
        toReturn.extend([s['symbol'] for s in sortedCalls])
        if len(sortedPuts) <= extendedQuota:
            toReturn.extend([s['symbol'] for s in sortedPuts])
        else:
            toReturn.extend([s['symbol'] for s in sortedPuts[:extendedQuota]])
    else:
        toReturn.extend([s['symbol'] for s in sortedPuts])
        toReturn.extend([s['symbol'] for s in sortedCalls])
    return toReturn


def _getOptions(symbol, strike='all'):
    try:
        c = auth.client_from_token_file(config.TOKEN_PATH, config.API_KEY)
    except FileNotFoundError:
        from selenium import webdriver
        with webdriver.Chrome() as driver:
            c = auth.client_from_login_flow(
                driver, config.API_KEY, config.REDIRECT_URI, config.TOKEN_PATH)
    try:
        if strike.strip().lower() == 'all':
            response = c.get_option_chain(symbol.upper(), contract_type=c.Options.ContractType.ALL,
                                          strike_range=c.Options.StrikeRange.ALL)
        else:
            response = c.get_option_chain(symbol.upper(), contract_type=c.Options.ContractType.ALL,
                                          strike=strike)
        return response.json(), response.status_code
    except Exception as e:
        # raise e
        return None


def _getAllStrikes(symbol):
    strikes = []
    try:
        c = auth.client_from_token_file(config.TOKEN_PATH, config.API_KEY)
    except FileNotFoundError:
        from selenium import webdriver
        with webdriver.Chrome() as driver:
            c = auth.client_from_login_flow(
                driver, config.API_KEY, config.REDIRECT_URI, config.TOKEN_PATH)
    try:
        response = c.get_option_chain(symbol.upper(), contract_type=c.Options.ContractType.PUT,
                                      strike_range=c.Options.StrikeRange.ALL)
        data = response.json()
        strikes = list(data['putExpDateMap']
                       [list(data['putExpDateMap'].keys())[0]].keys())
        return strikes
    except Exception as e:
        return False


def _getAllExpirations(symbol):
    expirations = []
    try:
        c = auth.client_from_token_file(config.TOKEN_PATH, config.API_KEY)
    except FileNotFoundError:
        from selenium import webdriver
        with webdriver.Chrome() as driver:
            c = auth.client_from_login_flow(
                driver, config.API_KEY, config.REDIRECT_URI, config.TOKEN_PATH)
    try:
        response = c.get_option_chain(symbol.upper(), contract_type=c.Options.ContractType.PUT,
                                      strike_range=c.Options.StrikeRange.ALL)
        data = response.json()
        expirations = list(data['putExpDateMap'].keys())
        return expirations
    except Exception as e:
        return False


def _info(symbol):
    expirations = []
    strikes = []
    try:
        c = auth.client_from_token_file(config.TOKEN_PATH, config.API_KEY)
    except FileNotFoundError:
        from selenium import webdriver
        with webdriver.Chrome() as driver:
            c = auth.client_from_login_flow(
                driver, config.API_KEY, config.REDIRECT_URI, config.TOKEN_PATH)
    try:
        response = c.get_option_chain(symbol.upper(), contract_type=c.Options.ContractType.PUT,
                                      strike_range=c.Options.StrikeRange.ALL)
        data = response.json()
        expirations = list(data['putExpDateMap'].keys())
        strikes = list(data['putExpDateMap']
                       [list(data['putExpDateMap'].keys())[0]].keys())
        return {
            "expirations": expirations,
            "strikes": strikes
        }
    except Exception as e:
        return False
