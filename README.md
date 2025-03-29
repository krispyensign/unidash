# Unidash

Perform signal generation and backtesting using WMA and Heiken Ashi.

## Quick Setup

* Install mongodb
* Install node
* npm install
* npm run build
* npm run -- --config ./config.json

## Config

To see all the options `npm run start -- --help`

A json file can be provided for the config using `npm run start -- --config ./config.json`

Here is the format:

```json
{
    "heartbeat": "<Your ntfy.sh topic>",  // heartbeat topic ntfy.sh
    "priority": "<Your other ntfy.sh topic>", // priority topic ntfy.sh
    "token0": "0x4200000000000000000000000000000000000006",  // token0 contract address
    "token1": "0x570b1533F6dAa82814B25B62B5c7c4c55eB83947",  // token1 contract address
    "strategyWmaColumn": "ha_open",  // pandas dataframe column name to use for wma calculation
    "strategySignalColumn": "ha_open", // pandas dataframe candle column name to use for the 
    "strategyName": "WMA_HEIKEN_ASHI_INVERSE", // strategy name selected
    "graphqlEndpoint": "https://gateway.thegraph.com/api/<Your API Token>/subgraphs/id/HMuAwufqZ1YCRmzL2SfHTVkzZovC9VL2UAKhjvRqKiR1",
    "daysToFetch": 60, // needs to be at least 21 days for WMA-Heiken Ashi indicator
    "mongodbEndpoint": "mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.4.2"
}
```
