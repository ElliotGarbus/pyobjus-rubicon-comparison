"""Why Rubicon's alloc then init keeps footprint though every object is freed.

Usage: rubicon_alloc_init.py FIXTURE

Run with a Rubicon environment's Python. Records:

- the objects one call of each creation path leaves for Python's cycle
  collector, from gc.DEBUG_SAVEALL, and where the first was created
- the same with a plain ctypes cast, without Rubicon, of a ctypes instance
  and of an integer address
- malloc's live memory and the footprint after 10,000 alloc then init calls,
  with an autorelease pool drained every 1,000 as in M3
- the footprint kept after each of 4 batches of 10,000, to show whether it
  grows or is reused

Prints one line, "S6RESULT " and JSON.
"""
import ctypes
import gc
import json
import os
import sys
import tracemalloc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class _MallocStats(ctypes.Structure):
    _fields_ = [("blocks_in_use", ctypes.c_uint), ("size_in_use", ctypes.c_size_t),
                ("max_size_in_use", ctypes.c_size_t), ("size_allocated", ctypes.c_size_t)]


def malloc_in_use():
    stats = _MallocStats()
    ctypes.CDLL(None).malloc_zone_statistics(None, ctypes.byref(stats))
    return stats.size_in_use


def left_for_collector(make):
    """Objects one call leaves for the cycle collector, by type, and where the
    first was created."""
    gc.collect()
    tracemalloc.start(25)
    gc.set_debug(gc.DEBUG_SAVEALL)
    import bench
    pool = bench.pool_push()
    make()
    bench.pool_pop(pool)
    gc.collect()
    garbage = list(gc.garbage)
    gc.garbage.clear()
    gc.set_debug(0)
    where = None
    if garbage:
        tb = tracemalloc.get_object_traceback(garbage[0])
        if tb:
            where = ["{}:{}".format(os.path.basename(f.filename), f.lineno) for f in tb][-4:]
    tracemalloc.stop()
    types = {}
    for o in garbage:
        types[type(o).__name__] = types.get(type(o).__name__, 0) + 1
    return {"count": len(garbage), "types": types, "created_at": where}


def main():
    ctypes.CDLL(sys.argv[1])
    import bench
    import rubicon.objc
    from rubicon.objc import ObjCClass
    Item = ObjCClass("S6Item")
    t = ObjCClass("S6Target").alloc().init()

    class Class(ctypes.c_void_p):
        pass

    paths = {"alloc_init": lambda: Item.alloc().init(), "new": lambda: Item.new(),
             "alloc_only": lambda: Item.alloc(), "method_result_then_a_call": lambda: t.makeItem().description,
             "method_result_no_call": lambda: t.makeItem()}
    for make in paths.values():
        for _ in range(20):
            make()
    result = {"rubicon": rubicon.objc.__version__, "python": sys.version.split()[0],
              "left_for_collector": {name: left_for_collector(make) for name, make in paths.items()}}
    result["plain_ctypes"] = {
        "cast_of_ctypes_instance": left_for_collector(lambda: ctypes.cast(Class(12345), Class)),
        "cast_of_integer": left_for_collector(lambda: ctypes.cast(12345, Class))}

    def batch():
        for _ in range(10):
            pool = bench.pool_push()
            for _ in range(1000):
                Item.alloc().init()
            pool_counts = bench.item_counts()
            bench.pool_pop(pool)
        bench.collect()
        return pool_counts

    bench.collect()
    start_counts = bench.item_counts()
    fp0, mu0 = bench.footprint(), malloc_in_use()
    kept = []
    for _ in range(4):
        batch()
        kept.append(bench.footprint() - fp0)
    end_counts = bench.item_counts()
    result["batches"] = {"objects_per_batch": 10_000, "footprint_kept_after_each_batch": kept,
                         "malloc_in_use_change": malloc_in_use() - mu0,
                         "created": end_counts["created"] - start_counts["created"],
                         "freed": end_counts["deallocated"] - start_counts["deallocated"]}
    print("S6RESULT " + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
