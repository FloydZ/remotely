#!/usr/bin/env python
""" remotely execute python functions """

import marshal
import base64
import time
import select
import logging
import os
from enum import Enum
import paramiko
from pathlib import Path
from typing import Union, Callable
import asyncio
import functools


logging.getLogger().setLevel(logging.DEBUG)


# get the source path of this file
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BUFFER_SIZE = 1 << 10
REMOTE_TMP_DIR = Path("/tmp")
REMOTE_WRAPPER_FILE_NAME = "wrapper.py"
REMOTE_WRAPPER_FILE = REMOTE_TMP_DIR.joinpath(REMOTE_WRAPPER_FILE_NAME)
COMMAND = "/usr/bin/env python3 " + str(REMOTE_WRAPPER_FILE) + " "
SSH_USERNAME = "SSH_USERNAME"
SSH_PASSWORD = "SSH_PASSWORD"


class AuthMethod(Enum):
    """

    """
    password = 0
    env = 1
    keyfile = 2


def callback(stdout, stderr):
    """
    callback function for the ssh tunnel
    """
    ret = None

    while not stdout.channel.exit_status_ready():
        logging.debug("Status of stdout worker is %s",
                      stdout.channel.exit_status_ready())

        time.sleep(0.1)
        if stdout.channel.recv_ready():
            logging.debug("Worker stdout.channel.recv_ready: %s",
                          stdout.channel.recv_ready())

            tmp, _, _ = select.select([stdout.channel], [], [], 0.0)
            if len(tmp) > 0:
                data = stdout.channel.recv(BUFFER_SIZE).decode("ascii")
                data = base64.b64decode(data)
                data = marshal.loads(data)
                logging.debug("Output: %s", data)

                ret = data

    while not stderr.channel.exit_status_ready():
        logging.error("Status of stderr worker is %s",
                      stderr.channel.exit_status_ready())

        time.sleep(0.1)
        if stderr.channel.recv_ready():
            logging.error("Worker stderr.channel.recv_ready: %s",
                          stderr.channel.recv_ready())
            tmp, _, _ = select.select([stderr.channel], [], [], 0.0)
            if len(tmp) > 0:
                logging.error("Error: %s",
                              stderr.channel.recv(BUFFER_SIZE).decode("utf-8"))

    return ret


async def async_callback(stdout, stderr):
    """
    async callback function for the ssh tunnel
    """
    ret = None
    while not stdout.channel.exit_status_ready():
        logging.debug("Status of worker is %s",
                      stdout.channel.exit_status_ready())

        if stdout.channel.recv_ready():
            logging.debug("Worker stdout.channel.recv_ready: %s",
                          stdout.channel.recv_ready())

            tmp, _, _ = select.select([stdout.channel], [], [], 0.0)
            if len(tmp) > 0:
                data = stdout.channel.recv(BUFFER_SIZE).decode("ascii")
                data = base64.b64decode(data)
                data = marshal.loads(data)
                logging.debug("Output: %s", data)

                ret = data

        time.sleep(1.)

    while not stderr.channel.exit_status_ready():
        logging.error("ERROR of worker is %s",
                      stderr.channel.exit_status_ready())

        time.sleep(1)
        if stderr.channel.recv_ready():
            logging.error("Worker stderr.channel.recv_ready: %s",
                          stderr.channel.recv_ready())
            tmp, _, _ = select.select([stderr.channel], [], [], 0.0)
            if len(tmp) > 0:
                logging.error("Error: %s",
                              stderr.channel.recv(BUFFER_SIZE).decode("utf-8"))

    return ret


def remotely(host: str, port: int, username: str = "", password: str = "",
             method: Union[AuthMethod.password, None] = None, async_: bool = True):
    """
    synchronous decorator for executing code remotely.
    NOTE: you can keep the username/password empty. If so, first
    we try to read the username/passwort from the environment. More
    precise the variables `SSH_USERNAME` and `SSH_PASSWORD` are read.
    If this method fails, too, a private key will be tried

    @param host: remotely server ip
    @param port: remotely server port
    @param username:
    @param password:
    @param method:
    """
    client = RemoteClient(host=host, port=port, username=username, password=password,
                          method=method, async_=async_)

    def decorator_inner(func):
        def decorate(*args, **kwargs):
            """
            a new connection for every decorator is made.
            """
            return client.run(func, *args, **kwargs)
        return decorate
    return decorator_inner


class RemoteClient:
    """ kek """
    def __init__(self, host: str = "127.0.0.1", port: int = 22, username: str = "", password: str = "",
                 method: Union[AuthMethod.password, None] = None, async_=True):
        """
        class for asynchronous remote execution
        """
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()

        if method is None:
            connected = False
            try:
                self.client.connect(host, port=port, username=username, password=password)
                connected = True
            except paramiko.AuthenticationException as _:
                pass

            if not connected:
                try:
                    username2 = os.environ[SSH_USERNAME]
                    password2 = os.environ[SSH_PASSWORD]
                    self.client.connect(host, port=port, username=username2, password=password2)
                    connected = True
                except paramiko.AuthenticationException as _:
                    pass

            if not connected:
                try:
                    self.client.connect(host, port=port)
                    connected = True
                except paramiko.AuthenticationException as _:
                    logging.error("could not connect")
                    return

            assert connected
        elif method == AuthMethod.password:
            self.client.connect(host, port=port, username=username, password=password)
        elif method == AuthMethod.env:
            username2 = os.environ[SSH_USERNAME]
            password2 = os.environ[SSH_PASSWORD]
            self.client.connect(host, port=port, username=username2, password=password2)
        elif method == AuthMethod.keyfile:
            self.client.connect(host, port=port)
        else:
            logging.error("unknown auth method")
            return

        # plant the receiver on the remote machine
        sftp = self.client.open_sftp()
        sftp.put(ROOT_DIR + "/wrapper.py", str(REMOTE_WRAPPER_FILE))

        self.method = method
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.async_ = async_

    def set_async(self, async_=True):
        """
        sets the async mode
        """
        self.async_ = async_

    def run(self, func, *args, **kwargs):
        """
        run function on remote server
        @return the return value of `func`
        """
        # TODO not workin
        #if isinstance(func, Callable):
        #    logging.error("wrong type")
        #    return None

        lines = func.__code__
        code_str = base64.b64encode(marshal.dumps(lines)).decode("ascii")
        args_str = base64.b64encode(marshal.dumps(args)).decode("ascii")
        kwds_str = base64.b64encode(marshal.dumps(kwargs)).decode("ascii")

        cmd = COMMAND + code_str + " " + args_str + " " + kwds_str
        logging.debug(cmd)
        _, ssh_stdout, ssh_stderr = self.client.exec_command(cmd, get_pty=True)

        assert not ssh_stderr.channel.closed
        assert self.client.get_transport().is_active()
        assert not ssh_stderr.closed
        assert not ssh_stdout.closed

        # TODO
        #kif self.async_:
        #k    asyncio.run(async_callback(ssh_stdout, ssh_stderr))
        #kelse:
        return callback(ssh_stdout, ssh_stderr)

#    def join(self, pid, timeout=None):
#        """
#        Block the calling thread until the function terminate or timeout occurs.
#        @param pid: process id from run()
#        @param timeout: if timeout is none then there's no timeout
#        """
#        pass
#
#    def kill(self, pid):
#        """
#        Terminate the process using Process.terminate() call
#        @param pid: process id from run()
#        """
#        pass
