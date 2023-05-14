# coding: utf-8
import pyperclip


def copy_to_clipboard(text):
    try:
        pyperclip.copy(text)
        print("Copied to clipboard.")
    except pyperclip.PyperclipException:
        print(
            "Cannot copy to clipboard, please copy manually. Please install xclip or xsel."
        )
        print(text)
