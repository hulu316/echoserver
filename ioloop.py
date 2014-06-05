#!/usr/bin/env python
# encoding=UTF-8

import select
import errno


class IOLoop(object):
    def __init__(self):
        self._handlers = {}
        self._events = {}
        self._impl = select.epoll()

    @staticmethod
    def instance():
        if not hasattr(IOLoop, '_instance'):
            IOLoop._instance = IOLoop()
        return IOLoop._instance

    def add_handler(self, fd, handler, events):
        self._handlers[fd] = handler
        self._impl.register(fd, events)

    def update_handler(self, fd, events):
        self._impl.modify(fd, events)

    def remove_handler(self, fd):
        self._handlers.pop(fd, None)
        self._events.pop(fd, None)
        try:
            self._impl.unregister(fd)
        except Exception:
            print('Error deleting fd from IOLoop')

    def start(self):
        try:
            poll_timeout = 3600.0
            while True:
                try:
                    event_pairs = self._impl.poll(poll_timeout)
                except Exception as e:
                    if (getattr(e, 'errno', None) == errno.EINTR or
                        (isinstance(getattr(e, 'args', None), tuple) and
                         len(e.args) == 2 and e.args[0] == errno.EINTR)):
                        continue
                    else:
                        raise
                self._events.update(event_pairs)
                while self._events:
                    fd, events = self._events.popitem()
                    try:
                        self._handlers[fd](fd, events)
                    except (OSError, IOError) as e:
                        if e.args[0] == errno.EPIPE:
                            # Happens when the client closes the connection
                            pass
                        else:
                            print("Exception in callback %r" % self._handlers.get(fd))
                    except Exception:
                        print("Exception in callback %r" % self._handlers.get(fd))
        finally:
            pass

    def stop(self):
        pass


