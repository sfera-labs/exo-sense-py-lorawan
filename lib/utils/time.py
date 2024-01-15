import os
import time

_ticks_diff_f = None

def _ticks_diff_use_new_api():
    rel = os.uname().release.split('.')
    maj = int(rel[0])
    if maj > 1:
        return True
    if maj < 1:
        return False
    min = int(rel[1])
    return min > 18

def _ticks_diff_inv(t1, t2):
    return time.ticks_diff(t2, t1)

def _ticks_diff_set():
    global _ticks_diff_f
    if _ticks_diff_use_new_api():
        _ticks_diff_f = time.ticks_diff
    else:
        _ticks_diff_f = _ticks_diff_inv

def ticks_diff(t1, t2):
    if _ticks_diff_f is None:
        _ticks_diff_set()
    return _ticks_diff_f(t1, t2)
