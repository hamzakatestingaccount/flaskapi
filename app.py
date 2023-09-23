import flask
import datetime
from src import controllers
from flask_cors import CORS
from flask import request

app = flask.Flask(__name__)
PREFIX = '/api/v1'

CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route('/', methods=['GET'])
def home():
    return "<h1>API DEVELOPMENT</h1><p>This site is a prototype API for option chain data</p>", 200


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


@app.route(PREFIX + '/options', methods=['GET'])
def options():
    query_parameters = request.args
    if not query_parameters:
        return {
            "error": "No query parameters"
        }, 400
    symbol = query_parameters.get('symbol')
    strike = query_parameters.get('strike') or 'all'
    return controllers.getOptions(symbol, strike)


@app.route(PREFIX + '/info', methods=['GET'])
def info():
    query_parameters = request.args
    if not query_parameters:
        return {
            "error": "No query parameters"
        }, 400
    symbol = query_parameters.get('symbol')
    return controllers.getInfo(symbol)


@app.route(PREFIX + '/symbols', methods=['GET'])
def symbols():
    query_parameters = request.args
    if not query_parameters:
        return {
            "error": "No query parameters"
        }, 400
    symbol = query_parameters.get('symbol')
    _range = query_parameters.get('range')
    save = query_parameters.get("save")
    minDate = query_parameters.get("minDate")
    maxDate = query_parameters.get("maxDate")
    try:
        minDate = datetime.datetime.strptime(
            minDate, '%Y-%m-%d').timestamp() if minDate is not None else None
    except:
        minDate = None
    try:
        maxDate = datetime.datetime.strptime(
            maxDate, '%Y-%m-%d').timestamp() if maxDate is not None else None
    except:
        maxDate = None
    if not symbol:
        return {
            "error": "No symbol parameter"
        }, 400
    if not _range:
        _range = 10
    try:
        _range = int(_range)
    except:
        _range = 10
    if not save or save != "1":
        save = False
    else:
        save = True
    return controllers.getAllSymbols(symbol, _range, save, minDate, maxDate)


@app.route(PREFIX + '/orders', methods=['GET'])
def orders():
    query_parameters = request.args
    if not query_parameters:
        return {
            "error": "No query parameters"
        }, 400
    symbol = query_parameters.get('symbol') or ""
    ts = query_parameters.get('ts') or ""
    if not symbol or not ts:
        return {
            "error": "symbol and timestamp is required"
        }, 400
    limit = query_parameters.get('limit') or 200
    try:
        limit = int(limit)
        if limit > 200:
            limit = 200
    except:
        limit = 200
    page = query_parameters.get('page') or 1
    try:
        page = int(page)
    except:
        page = 1
    return controllers.getOrders(ts, symbol.upper(), page, limit)


if __name__ == '__main__':
    app.run()
