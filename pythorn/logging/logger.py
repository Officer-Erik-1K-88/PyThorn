import sys

__all__ = ["Logger"]

class Logger:
    def __init__(self, debug_level=0):
        from pythorn.logging.counter import Counter
        self.debug_level = debug_level
        self.log_count = Counter("log")
        self.errors = Counter("error")
        self.warns = Counter("warn")
        self.infos = Counter("info")
        self.seps = Counter("seps")
        self._default_files = {
            "default": sys.stdout,
            "ERROR": sys.stderr,
            "WARN": sys.stderr,
        }

    def get_default_file(self, log_type, fallback_type: str="default"):
        file = self._default_files.get(log_type, self._default_files.get(fallback_type))
        if file is None:
            return self._default_files["default"]
        return file

    def set_default_file(self, log_type, file):
        old = self._default_files.get(log_type)
        if file is None:
            if log_type == "default":
                self._default_files["default"] = sys.stdout
            else:
                old = self._default_files.pop(log_type, None)
        else:
            self._default_files[log_type] = file
        return old

    def base_log(self, *msgs, level=0, sep=' ', end="\n", file=None, flush=False):
        if self.debug_level < level:
            return False
        if file is None:
            file = self.get_default_file("base")
        msg_count = len(msgs)
        if msg_count <= 0:
            raise RuntimeError("Must have at least one object in msgs")
        print_msg = str(msgs[0])
        for i in range(1, msg_count):
            print_msg += sep + str(msgs[i])
        print(print_msg, end=end, file=file, flush=flush)
        return True

    def log(self, title, *msgs, level=0, title_sep=' ', sep=' ', end="\n", file=None, flush=False):
        if title is None:
            raise TypeError("Log title must not be None")
        if file is None:
            file = self.get_default_file(title, "log")
        title = f"[{title}]"
        if msgs:
            messages = list(msgs)
            messages[0] = f"{title}{title_sep}{messages[0]}"
        else:
            messages = [title]
        passed = self.base_log(*messages, level=level, sep=sep, end=end, file=file, flush=flush)

        self.log_count.add(1, not passed)
        return passed

    def error(self, *msgs, **kwargs):
        passed = self.log("ERROR", *msgs, **kwargs)
        self.errors.add(1, not passed)
        return passed

    def warn(self, *msgs, **kwargs):
        passed = self.log("WARN", *msgs, **kwargs)
        self.warns.add(1, not passed)
        return passed

    def info(self, *msgs, **kwargs):
        passed = self.log("INFO", *msgs, **kwargs)
        self.infos.add(1, not passed)
        return passed

    def log_sep(self, size=50, title=None, *, size_is_sep_count=False, sep="-", end="\n", file=None, flush=False):
        if file is None:
            file = self.get_default_file("seperator")
        if title is not None:
            title = f">{title}<"
            if size_is_sep_count:
                size += len(title)
        else:
            title = sep
        print(title.center(size, sep), end=end, file=file, flush=flush)
        self.seps.add(1)

    def percent(self, name: str, current: float=0, cap: int=100, step: float=1):
        from pythorn.logging.counter import Percent
        return Percent(name, current, cap, step, self)

    def count(self, name: str, step: float=1):
        from pythorn.logging.counter import Counter
        return Counter(name, step=step, logger=self)
