from colorama import Fore, Style

class CS:

    @staticmethod
    def red(string: str) -> str:
        return Fore.RED + string + Style.RESET_ALL
    
    @staticmethod
    def green(string: str) -> str:
        return Fore.GREEN + string + Style.RESET_ALL
    
    @staticmethod
    def purple(string: str) -> str:
        return Fore.MAGENTA + string + Style.RESET_ALL
    
    @staticmethod
    def yellow(string: str) -> str:
        return Fore.YELLOW + string + Style.RESET_ALL

    @staticmethod
    def blue(string: str) -> str:
        return Fore.LIGHTBLUE_EX + string + Style.RESET_ALL