from typing import List
from itertools import chain, product
from mutagen.mp3 import MP3
from mutagen.id3 import TALB, TIT2, TPE1, TPE2, TOFN
from emoji import replace_emoji
from log import INDENT, error, print_indent, Color
import os
import sys


def generate_permutations(text: str) -> List[str]:
    permutations: List[str] = []
    words = text.split()

    for word in words:
        permutations.append(f"({word})")
        permutations.append(f"[{word}]")

    return permutations


STRINGS_TO_REMOVE_PERMUTATIONS_OF = [
    "official",
    "official video",
    "official audio",
    "official lyric video",
    "official music video",
    "official album track",
    "official track",
    "official audio",
    "official live",
    "official visualizer",
    "official hd video",
    "music",
    "music video",
    "bonus",
    "bonus track",
    "lyric",
    "lyric video",
    "audio",
    "track",
    "live",
    "album track",
    "album",
    "video projection",
    "art video"
]

STRINGS_TO_ADDITIONALLY_REMOVE = [
    "| Napalm Records",
    "–",
    "—"
]

TITLE_SEPARATORS = ["-", "–", "—"]

SUBSTRINGS_TO_REMOVE = list(
    chain.from_iterable(
        (
            generate_permutations(string)
            for string in STRINGS_TO_REMOVE_PERMUTATIONS_OF
        )
    )
)

SUBSTRINGS_TO_REMOVE.extend(STRINGS_TO_ADDITIONALLY_REMOVE)

DEBUG = False


def main():
    folder_path = sys.argv[1]
    folder = os.scandir(path=folder_path)

    global DEBUG
    DEBUG = True if len(sys.argv) > 2 and sys.argv[2] == "debug" else False
    if DEBUG:
        debug_permutations = open("debug_permutations.txt", "w")
        for substring in SUBSTRINGS_TO_REMOVE:
            debug_permutations.write(substring + "\n")
        debug_permutations.close()

        # We'll be appending to this file later but first we need to get rid of content from previous runs
        debug_cleaned_titles = open("debug_cleaned_titles.txt", "w")
        debug_cleaned_titles.truncate(0)
        debug_cleaned_titles.close()

    for collection in folder:
        process_collection(collection)


def remove_emojis(string: str):
    return replace_emoji(string)

# TODO after permutations are checked, also check them without [] and ()


def clean_title(title: str, album: str, band: str):
    cleaned_title = remove_emojis(title)

    # if title starts with band name, remove it
    for char in TITLE_SEPARATORS:
        substring = f"{band.lower()} {char} "
        if cleaned_title.lower().startswith(substring):
            cleaned_title = cleaned_title[len(substring):]

    # additional case for when there is no separator between title and band name
    if cleaned_title.lower().startswith(band.lower()):
        cleaned_title = cleaned_title[len(band):]

    # TODO replace permutations with plain lowercase() -> find() -> slice()
    for substring in SUBSTRINGS_TO_REMOVE:
        # cleaned_title = cleaned_title.replace(substring, "")

        # ///
        index_to_remove = cleaned_title.find(substring)

        if index_to_remove != -1:
            cleaned_title = cleaned_title[:index_to_remove] + \
                cleaned_title[(len(substring) - 1):]

    # need to strip of whitespace for next part
    cleaned_title = cleaned_title.strip()

    if cleaned_title.startswith(("\"", "\'", "``")) and cleaned_title.endswith(("\"", "\'", "``")):
        cleaned_title = cleaned_title[1: -1]

    # if title contains name of album, remove
    cleaned_title.replace(f"({album})", "")
    cleaned_title.replace(f"({album.lower()})", "")
    cleaned_title.replace(f"({album.upper()})", "")

    return cleaned_title.strip()


def write_metadata(file: os.DirEntry[str], artist: str, album: str, title: str):
    f = MP3(file.path)
    f["TIT2"] = TIT2(encoding=3, text=title)
    f["TALB"] = TALB(encoding=3, text=album)
    f["TPE1"] = TPE1(encoding=3, text=artist)
    f["TPE2"] = TPE2(encoding=3, text=artist)

    try:
        f["TOFN"]
    except KeyError:
        f["TOFN"] = TOFN(encoding=3, text=title)

    f.save()


def process_collection(collection: os.DirEntry):
    if collection.is_file():
        return

    band_name = collection.name
    print_indent(0, band_name)

    if DEBUG:  # Clear debug file of previous content
        debug_cleaned_titles = open(
            "debug_cleaned_titles.txt", "a", encoding="utf-8")
        debug_cleaned_titles.write(band_name + "\n")

    for album in os.scandir(path=collection.path):
        album_name = album.name
        print_indent(1, album_name)

        if DEBUG:
            debug_cleaned_titles.write("    " + album_name + "\n")

        for file in os.scandir(album.path):
            _, extension = os.path.splitext(file.path)
            if bool(extension) and extension != ".mp3":
                return

            title = file.name.replace(".mp3", "")
            cleaned_title = clean_title(title, album_name, band_name)

            if DEBUG:
                debug_cleaned_titles.write(
                    f"{INDENT}{INDENT}{title} => {cleaned_title}\n")

            write_metadata(file=file, artist=band_name,
                           album=album_name, title=cleaned_title)

            filepath = file.path.replace(title, cleaned_title)

            # Accidentally removed file extensions, haha
            if not filepath.endswith(".mp3"):
                filepath = filepath + ".mp3"

            try:
                os.rename(file.path, filepath)
            except Exception as e:
                already_exists = type(e) is FileExistsError

                if already_exists:
                    error(
                        f"Could not rename {Color.YELLOW}{file.path}{Color.END} to {Color.YELLOW}{filepath}{Color.END} because the latter already exists.")
                else:
                    error(
                        f"Could not rename {Color.YELLOW}{file.path}{Color.END} to {Color.YELLOW}{filepath}.")

    if DEBUG:
        debug_cleaned_titles.close()


if __name__ == "__main__":
    main()
