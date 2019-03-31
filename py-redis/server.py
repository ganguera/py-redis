import asyncore
import socket
import signal

from redis import RedisCommand
from data import RedisDatabase


class RedisHandler(asyncore.dispatcher_with_send):

    def __init__(self, database_manager, sock=None, map=None):
        asyncore.dispatcher_with_send.__init__(self, sock, map)
        self.num_databases = database_manager[0]
        self.databases = database_manager[1]
        self.client_db = 0

    def handle_read(self):
        data = self.recv(8192).decode()
        if data:
            command = RedisCommand.from_handler(data, (self.num_databases, self.databases[self.client_db]))
            code, message = command.execute()
            self.send(message.encode())
            if code == 1:
                self.handle_close()
            elif 10 <= code <= 10 + self.num_databases:
                self.client_db = code - 10
            elif code == 20:
                for datastore in self.databases:
                    datastore.flush()

    def handle_close(self):
        print('Closing connection from {}:{}'.format(*self.addr))
        self.close()


class RedisServer(asyncore.dispatcher):

    def __init__(self, host, port, databases=6):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(50)
        print('Server listening at {}:{}'.format(host, port))
        self.num_databases = databases - 1
        self.databases = list()
        for db in range(databases):
            db = RedisDatabase()
            self.databases.append(db)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print('Opening connection from {}:{}'.format(*addr))
            RedisHandler((self.num_databases, self.databases), sock)

    def handle_close(self):
        print('Server stopping')
        self.close()


if __name__ == '__main__':

    def signal_handler(signal, frame):
        raise asyncore.ExitNow('Server stopping')

    signal.signal(signal.SIGINT, signal_handler)
    server = RedisServer('localhost', 6379)
    try:
       asyncore.loop()
    except Exception as e:
        print('{}: {}'.format(type(e).__name__, e))
