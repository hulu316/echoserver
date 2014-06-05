#!/usr/bin/env python
# encoding=UTF-8

import socket
import select
import errno

from ioloop import IOLoop
from iostream import EchoStream


class EchoServer(object):
    def __init__(self, address, port):
        self.io_loop = IOLoop.instance()
        self._socket = self.bind_socket(address, port)
        self.io_loop.add_handler(self._socket.fileno(), self.accept_handler, select.EPOLLIN)
        #self._handled = 0

    @staticmethod
    def bind_socket(address, port):
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(0)
        sock.bind((address, port))
        sock.listen(5)
        return sock

    def accept_handler(self, fd, events):
        while True:
            try:
                connection, address = self._socket.accept()
            except socket.error as e:
                if e.args[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return
                if e.args[0] == errno.ECONNABORTED:
                    continue
                raise
            try:
                stream = EchoStream(connection, address)
                self.handle_stream(stream, address)
            except Exception as e:
                print 'In echoserver:', e
                raise

    def handle_stream(self, stream, address):
        def _handle_chunk(chunck):
            eol = chunck.find('\r\n')
            start_line = chunck[:eol]
            uri = start_line.split(' ')[1]
            args = uri.split('?')[-1].split('=')
            if len(args) != 2 or args[0] != 'say':
                word = 'Please use "?say=something"'
            else:
                word = args[1]
            stream.write_to_fd(word)
            stream.close()

            # For ab testing...
            #self._handled += 1
            #if not (self._handled % 100):
                #print self._handled

        stream.read_until(b'\r\n\r\n', _handle_chunk)

