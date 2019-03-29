import re
import time
import random
from redis_protocol.protocol import deserialize, serialize_string, serialize_error, serialize_integer, serialize_bulk_string, serialize_array

class RedisCommand(object):

    def __init__(self, command, arguments, database_manager):
        self.command = command.upper()
        self.arguments = arguments
        self.num_databases = database_manager[0]
        self.datastore = database_manager[1]

    @classmethod
    def from_handler(cls, arguments, datastore):
        arguments = deserialize(arguments)
        command = arguments[0]
        arguments = arguments[1:]
        return RedisCommand(command, arguments, datastore)

    def execute(self):
        return getattr(self, self.command)()

    def QUIT(self):
        return (1, serialize_string('OK'))

    def PING(self):
        if self.arguments:
            return (0, serialize_string('{}'.format(' '.join(self.arguments))))
        else:
            return (0, serialize_string('PONG'))

    def ECHO(self):
        return (0, serialize_bulk_string('{}'.format(' '.join(self.arguments))))

    def SELECT(self):
        db = int(self.arguments[0])
        if db > self.num_databases:
            return (0, serialize_error('ERR DB index is out of range'))
        else:
            return (10 + db, serialize_string('OK'))

    def COMMAND(self):
        output = ''
        for item in dir(self):
            if item.isupper():
                output += '{}\n'.format(item)
        return (0, serialize_array('{}'.format(output)))

    def KEYS(self):
        if self.arguments[0] == '*':
            pattern = '.*'
        else:
            pattern = self.arguments[0]
        pattern = re.compile(pattern)
        output = ''
        for value in vars(self.datastore):
            if pattern.search(value):
                output += '{}\n'.format(value)
        return (0, serialize_array('{}'.format(output)))

    def SET(self):
        key = self.arguments[0]
        value = self.arguments[1]
        options = self.arguments[2:]
        mode = None
        expire = None
        for option in options:
            if mode == 'EX':
                expire = int(time.time()) + int(option)
            mode = option
        setattr(self.datastore, key, (value, expire))
        return (0, serialize_string('OK'))

    def GET(self):
        key = self.arguments[0]
        try:
            value, expire = getattr(self.datastore, key)
            if expire is not None and expire <= int(time.time()):
                self.DEL(key)
                raise Exception
            else:
                return (0, serialize_bulk_string('{}'.format(value)))
        except:
            return (0, serialize_bulk_string(None))

    def DEL(self, key=None):
        if key is None:
            for index, key in enumerate(self.arguments):
                try:
                    delattr(self.datastore, key)
                except:
                    pass
            return (0, serialize_integer('{}'.format(index + 1)))
        else:
            delattr(self.datastore, key)

    def DBSIZE(self):
        return (0, serialize_integer('{}'.format(len(vars(self.datastore)))))

    def INCR(self):
        key = self.arguments[0]
        value, expire = getattr(self.datastore, key, (0, None))
        try:
            value = int(value) + 1
        except:
            return (0, serialize_error('ERR value is not an integer or out of range'))
        setattr(self.datastore, key, (value, expire))
        return (0, serialize_integer('{}'.format(value)))

    def ZADD(self):
        def byScore(item):
            return item[0]

        key = self.arguments[0]
        score = self.arguments[1]
        member = self.arguments[2]
        array = getattr(self.datastore, key, list())
        if [value for value in array if value[1] == member]:
            array.remove(value)
        array.append((score, member))
        array = sorted(array, key=byScore)
        setattr(self.datastore, key, array)
        return (0, serialize_integer('1'))

    def ZCARD(self):
        key = self.arguments[0]
        array = getattr(self.datastore, key, list())
        return (0, serialize_integer('{}'.format(len(array))))

    def ZRANK(self):
        key = self.arguments[0]
        member = self.arguments[1]
        array = getattr(self.datastore, key, list())
        if not [position for position, value in enumerate(array) if value[1] == member]:
            return (0, serialize_bulk_string(None))
        else:
            return (0, serialize_integer('{}'.format([position for position, value in enumerate(array) if value[1] == member][0])))

    def ZRANGE(self):
        key = self.arguments[0]
        start = int(self.arguments[1])
        stop = int(self.arguments[2])
        array = getattr(self.datastore, key, list())
        if abs(start) > len(array):
            return (0, serialize_array(''))
        if abs(stop) > len(array) or stop == -1:
            stop = None
        output = ''
        for value in [value[1] for value in array[start:stop]]:
            output += '{}\n'.format(value)
        return (0, serialize_array('{}'.format(output)))

    def LPUSH(self):
        key = self.arguments[0]
        value = self.arguments[1]
        array = getattr(self.datastore, key, list())
        array.insert(0, value)
        setattr(self.datastore, key, array)
        return (0, serialize_integer('{}'.format(len(array))))

    def RPUSH(self):
        key = self.arguments[0]
        value = self.arguments[1]
        array = getattr(self.datastore, key, list())
        array.append(value)
        setattr(self.datastore, key, array)
        return (0, serialize_integer('{}'.format(len(array))))

    def LPOP(self):
        key = self.arguments[0]
        array = getattr(self.datastore, key, list())
        try:
            result = array.pop(0)
        except IndexError:
            result = None
        return (0, serialize_bulk_string(result))

    def RPOP(self):
        key = self.arguments[0]
        array = getattr(self.datastore, key, list())
        try:
            result = array.pop()
        except IndexError:
            result = None
        return (0, serialize_bulk_string(result))

    def SADD(self):
        key = self.arguments[0]
        member = self.arguments[1]
        array = getattr(self.datastore, key, set())
        array.add(member)
        setattr(self.datastore, key, array)
        return (0, serialize_integer('1'))

    def HSET(self):
        key = self.arguments[0]
        k = self.arguments[1]
        value = self.arguments[2]
        data = getattr(self.datastore, key, dict())
        data.update(k=value)
        setattr(self.datastore, key, data)
        return (0, serialize_integer('1'))

    def SPOP(self):
        key = self.arguments[0]
        array = getattr(self.datastore, key, None)
        if array is None:
            return (0, serialize_bulk_string(None))
        try:
            result = array.pop()
        except KeyError:
            return (0, serialize_bulk_string(None))
        setattr(self.datastore, key, array)
        return (0, serialize_bulk_string(result))

    def LRANGE(self):
        key = self.arguments[0]
        start = int(self.arguments[1])
        stop = int(self.arguments[2])
        array = getattr(self.datastore, key, list())
        output = ''
        if stop == -1:
            stop = None
        else:
            stop += 1
        for value in array[start:stop]:
            output += '{}\n'.format(value)
        return (0, serialize_array('{}'.format(output)))

    def MSET(self):
        arguments = iter(self.arguments)
        for key in arguments:
            setattr(self.datastore, key, (next(arguments), None))
        return (0, serialize_string('OK'))
