from colorama import Fore, Style

def color(color: str, s: str):
    return color + s + Style.RESET_ALL

def green(s: str):
    return color(Fore.GREEN, s)

def bold(s: str):
    return color(Style.BRIGHT, s)

def dim(s: str):
    return color(Style.DIM, s)

def cyan(s: str):
    return color(Fore.CYAN, s)

def yellow(s: str):
    return color(Fore.YELLOW, s)

def magenta(s: str):
    return color(Fore.MAGENTA, s)