import sys
from colorama import Style, Fore

def yes_no(question, default="yes"):
    """Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(Style.BRIGHT + Fore.BLUE + ":: " + Fore.RESET + question + prompt + Style.NORMAL)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def option(question, options, default=1):
    print(question)
    options = list(options)
    for idx, element in enumerate(options):
        print("{}) {}".format(idx+1,element))
    while True:
        i = input("{Style.BRIGHT}{Fore.BLUE}:: {Fore.RESET}Please pick[{}]: {Style.RESET_ALL}".format(default, Style=Style, Fore=Fore))
        try:
            if i == "":
                i = default
            else:
                i = int(i)
            if 0 < i <= len(options):
                return options[i-1]
        except:
            pass
    return None

def password(question):
    from getpass import getpass
    while True:
        password = getpass(question)
        if password:
            return password
