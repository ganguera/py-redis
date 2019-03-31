class RedisDatabase(object):

    def flush(self):
        for value in list(vars(self)):
            delattr(self, value)
