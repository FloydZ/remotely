#!/usr/bin/env python3

import time
import asyncio
from remotely import RemoteClient, remotely, callback, ROOT_DIR, COMMAND


HOST = "127.0.0.1"
PORT = 22
USERNAME = "kek"
PASSWORD = "lol"


def foo1(num_a, num_b):
    """
    test functions
    """
    return num_a + num_b


def foo2(num_a: int, num_b: int, num_c: int):
    """
    test function
    """
    import time
    time.sleep(2)
    return num_a + num_b + num_c


def foo3():
    """
    test function
    """
    return 1


@remotely(HOST, PORT, USERNAME, PASSWORD)
def foo1_(num_a, num_b):
    """
    testing the function decorator
    """
    return num_a + num_b


def test_remote_sync_client():
    """
    testing client
    """
    client = RemoteClient(HOST, PORT, USERNAME, PASSWORD, async_=False)
    num_a = client.run(foo2, 1, 1, 0)
    assert num_a == 2


# currently not working
#async def test_remote_async_client():
#    """
#    testing async client
#    """
#    client = RemoteClient(HOST, PORT, USERNAME, PASSWORD, async_=True)
#    num_a = client.run(foo2, 1, 1, 0)
#    await num_a()
#    assert num_a == 2


def test_decorate_client():
    """
    check the decoration
    """
    num_a = foo1_(2, 3)
    assert num_a == 5


#asyncio.run(test_remote_async_client())
#test_remote_sync_client()
test_decorate_client()
