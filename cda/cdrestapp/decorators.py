import cProfile
import pstats
import io
from pstats import SortKey


def cprofile(func):
    def wrapper(*args, **kwargs):
        pr_filename = ".".join((__name__, func.__name__, "prof"))
        pr = cProfile.Profile()
        result = pr.runcall(func, *args, **kwargs)
        s = io.StringIO()
        sort_by = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
        ps.dump_stats(pr_filename)
        ps.print_stats(20)
        return result

    return wrapper
