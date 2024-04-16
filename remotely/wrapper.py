#!/usr/bin/env python3
""" client side of the script """

import base64
from collections.abc import Callable
import marshal
import pickle
import sys
import types
import multiprocessing as mp

DEBUG_MODE = True
ASYNC = False
LOG = "/tmp/w.log"
f = None
if DEBUG_MODE:
    f = open(LOG, "w")
    f.write("open\n")
    f.flush()

if __name__ == '__main__':
    if DEBUG_MODE:
        f.write("len(sys.argv):")
        f.write(str(len(sys.argv)))
        f.write("\n")
        f.flush()

    assert len(sys.argv) >= 2
    FUNC_STR = sys.argv[1]
    if DEBUG_MODE:
        f.write("funcstr:")
        f.write(FUNC_STR)
        f.write("\n")
        f.flush()

    # local config
    jobs = {}

    # encoding/unmarshalling
    code = marshal.loads(base64.b64decode(FUNC_STR))
    func = types.FunctionType(code, globals(), "remote_func")
    assert isinstance(func, Callable)

    # read the args
    args = {}
    kwargs = {}
    if len(sys.argv) >= 3:
        args = marshal.loads(base64.b64decode(sys.argv[2]))

    if len(sys.argv) >= 4:
        kwargs = marshal.loads(base64.b64decode(sys.argv[3]))

    if DEBUG_MODE:
        f.write("func:")
        f.write(str(func.__code__))
        f.write("\n")
        f.write("args:")
        f.write(str(args))
        f.write("\n")
        f.write("kwargs:")
        f.write(str(kwargs))
        f.write("\n")
        f.flush()

    output = " "
    if ASYNC:
        # create a process wrapper and use queue to get func output
        queue = mp.Queue()

        def wrapper(ifunc, que):
            """ async wrapper around function call """

            def wrapper2(*args2, **kwds2):
                ret = ifunc(*args2, **kwds2)
                que.put(ret)

            return wrapper2


        p = mp.Process(target=wrapper(func, queue), )
        p.start()
        jobs[(p.pid)] = (p, queue)
        output = base64.b64encode(pickle.dumps(p.pid))
    else:
        # block and run
        assert isinstance(func, Callable)
        output = func(*args, **kwargs)

        if DEBUG_MODE:
            f.write("output kek:")
            f.write(str(output))
            f.write("\n")
            f.flush()
        output = base64.b64encode(marshal.dumps(output)).decode("ascii")

    if DEBUG_MODE:
        f.write("output:")
        f.write(output)
        f.write("\n")
        f.flush()
    # this is read by the script
    print(output)
