#!/usr/bin/env python
# encoding=UTF-8


from ioloop import IOLoop
from echoserver import EchoServer


if __name__ == '__main__':
    print ('Starting echo server on port 8000')
    echoServer = EchoServer('0.0.0.0', 8000)
    IOLoop.instance().start()
