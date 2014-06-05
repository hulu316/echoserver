#!/usr/bin/env python
# encoding=UTF-8

import select
import socket
import errno
import collections

from ioloop import IOLoop


class EchoStream(object):
    def __init__(self, socket, *args, **kwargs):
        self.io_loop = IOLoop.instance()
        self.socket = socket
        self.socket.setblocking(0)

        self._read_callback = None
        self.max_buffer_size = 104857600
        self.read_chunk_size = 4096
        self._read_buffer_size = 0
        self._read_buffer = []
        self._write_buffer = []

        self._state = None
        self._closed = False

    def read_from_fd(self):
        try:
            chunk = self.socket.recv(self.read_chunk_size)
        except socket.error as e:
            if e.args[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                return None
            else:
                raise
        if not chunk:
            self.close()
            return None
        return chunk

    def _read_to_buffer(self):
        try:
            chunk = self.read_from_fd()
        except (socket.error, IOError, OSError) as e:
            self.close()
            raise
        if chunk is None:
            return 0
        self._read_buffer.append(chunk)
        self._read_buffer_size += len(chunk)
        if self._read_buffer_size >= self.max_buffer_size:
            self.close()
            raise IOError("Reached maximum read buffer size")
        return len(chunk)

    def read_until(self, delimiter, callback):
        self._read_callback = callback
        self._read_delimiter = delimiter
        while not self.closed():
            if self._read_to_buffer() == 0:
                break
        if self._read_from_buffer():
            return
        self._maybe_add_error_listener()

    def _read_from_buffer(self):
        if self._read_buffer_size:
            chunck = ''.join(self._read_buffer)
            loc = chunck.find(self._read_delimiter)
            if loc != -1:
                callback = self._read_callback
                delimiter_len = len(self._read_delimiter)
                consume_len = loc + delimiter_len
                self._read_callback = None
                self._read_delimiter = None
                self._read_buffer = [chunck[consume_len:]]
                self._read_buffer_size -= consume_len
                callback(chunck[:consume_len])
                return True
        return False

    def write_to_fd(self, data):
        return self.socket.send(data)

    def _handle_events(self, fd, events):
        if self.closed():
            return
        if events & select.EPOLLIN:
            while not self.closed():
                if self._read_to_buffer() == 0:
                    break
            if self._read_from_buffer():
                return

    def _maybe_add_error_listener(self):
        if self.closed():
            return
        if self._state is None:
            self.io_loop.add_handler(self.socket.fileno(), self._handle_events, select.EPOLLIN)
            self._state = select.EPOLLIN
        else:
            self.io_loop.update_handler(self.socket.fileno(), self._state)

    def closed(self):
        return self._closed

    def close(self):
        if not self.closed():
            self._closed = True
            if self._state is not None:
                self.io_loop.remove_handler(self.socket.fileno())
                self._state = None
            self.socket.close()
            self.socket = None
