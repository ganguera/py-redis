# Python 3 Partial Redis Server Implementation

Some time ago I partially implemented a text-based protocol Redis Server for Python 2.

Recently, though, I decided to adapt it to Python 3 and include support for RESP (REdis Serialization Protocol) so that I could run redis-benchmark and redis-cli.<br/>Although I made some small changes and adjustments, the credits for the RESP Implementation belong to [WayHome](https://github.com/wayhome/redis_protocol).

Since I started from the original Python 2 code, this implementation still uses the Asyncore Library (deprecated since Python 3.6).

The current version supports the following commands:

Connection:
* ECHO
* PING
* QUIT
* SELECT (6 databases provided by default. Up to 10 due to implementation considerations)

Hashes:
* HSET

Keys:
* DEL
* KEYS

Lists:
* LPOP
* LPUSH
* LRANGE
* RPOP
* RPUSH

Server:
* COMMAND (Partially implemented to avoid redis-cli errors)
* DBSIZE
* FLUSHALL
* FLUSHDB

Sets:
* SADD
* SPOP

Strings:
* GET
* INCR
* MSET
* SET

Sorted Sets:
* ZADD
* ZCARD
* ZRANGE
* ZRANK