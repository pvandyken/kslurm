from __future__ import absolute_import


def time(time: str):
    if ":" in time:
        if "-" in time:
            days, hhmm = time.split("-")
            hours, min = hhmm.split(":")
        else:
            days = 0
            hours, min = time.split(":")
    else:
        try:
            min = int(time)
            hours, days = 0, 0
        except Exception:
            raise TypeError(
                f'Invalid format for time: "{time}"\n'
                f"Must be as [xx-]xx:xx or x where x is a number"
            )
    return str(int(min) + int(hours) * 60 + int(days) * 60 * 24)
