ssh_remotely
========
`remotely` is a simple and secure remote code execution API that supports both 
asynchronous and blocking execution via SSH. 

`remotely` can be used for:
- run python code `remotely` on a different machine via ssh in parallel
- access different resources on another machine

Dependencies:
============

To successfully run `remotely` you need ssh access to a remote machine, on
which `python3` is installed.

Usage:
=====

You use the remotely decorator for any function you want to run remotely.

```python
from remotely import remotely

@remotely(SERVER, PORT, USERNAME, PASSWORD)
def remote_code():
    # import required packages
    # DO NOT use `print`
    # do something here
    result = 1
    return result

# function will be executed on the remote server
a = remote_code()
print("The server returned", a)
```

The asynchronous (non-blocking) version runs the function as a separate process 
on the remote server and supports simple job management functions (join and kill).

```python
def foo(arg1, arg2):
    return arg1 + arg2

from remotely import RemoteClient
rc = RemoteClient(SERVER, PORT, USERNAME, PASSWORD)
pid = rc.run(foo, arg1, arg2)
output = rc.join(pid)
output = rc.kill(pid)
```

Limitation:
-----------

- To use external packages on the remote server, they need to be installed there.
- Do not use any `print` statements, or anything else which prints something on
    a shell. If you do so, the return value from the function, can not be recovered

TODO:
- non blocking impl
- eine binary die prozesse teleported?
- 
