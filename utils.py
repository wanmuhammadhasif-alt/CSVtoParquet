import os

def format_size(size):

    units = ["B","KB","MB","GB","TB"]

    i = 0

    while size >= 1024 and i < len(units)-1:

        size /= 1024

        i += 1

    return f"{size:.2f} {units[i]}"