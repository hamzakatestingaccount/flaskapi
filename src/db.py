import pymongo
import datetime
from src import config
from bson.objectid import ObjectId


def get_books(timestamp, symbol, page, limit):
    # Connect to the MongoDB database
    client = pymongo.MongoClient(config.DB_STRING)
    db = client["tda"]
    orders = db["orders"]
    start_of_day_timestamp, end_of_day_timestamp = get_limits(float(timestamp))
    # Find documents where timestamp is greater than the specified value
    query = {
        "timestamp": {"$gte": start_of_day_timestamp, "$lt": end_of_day_timestamp},
        "symbol": symbol
    }
    print(query)
    projection = {"_id": 0}
    skip = (page - 1) * limit
    # Skip the specified number of pages and return the specified number of documents
    orders_cursor = orders.find(query, projection).skip(
        skip).limit(limit).sort("timestamp", pymongo.ASCENDING)
    _orders = list(orders_cursor)
    return _orders


def get_limits(timestamp):
    dt = datetime.datetime.fromtimestamp(timestamp)
    start_of_day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
    start_of_day_timestamp = int(start_of_day.timestamp())
    end_of_day_timestamp = int(end_of_day.timestamp())
    return start_of_day_timestamp, end_of_day_timestamp


def insert_contracts(contracts, symbol):
    client = pymongo.MongoClient(config.DB_STRING)
    db = client["tda"]
    _contracts = db["contracts"]
    # _contracts.create_index([("timestamp", pymongo.ASCENDING)])
    query = {"symbol": symbol}
    oldContractsCursor = _contracts.find(query)
    oldContracts = list(oldContractsCursor)
    for oldContract in oldContracts:
        document_id = ObjectId(oldContract["_id"])
        _contracts.delete_one({"_id": document_id})
    for contract in contracts:
        _contracts.insert_one({"symbol": symbol, "contract": contract})


def get_intruption():
    client = pymongo.MongoClient(config.DB_STRING)
    db = client["tda"]
    _config = db["config"]
    query = {"value": "inter", "intruption": True}
    res = _config.find_one(query)
    if res:
        return res['intruption']
    return False


def set_intruption(value):
    client = pymongo.MongoClient(config.DB_STRING)
    db = client["tda"]
    _config = db["config"]
    query = {"value": "inter"}
    res = _config.find_one(query)
    if res:
        _config.update_one(query, {"$set": {"intruption": value}})
    else:
        _config.insert_one({"value": "inter", "intruption": value})
