import sys
import os
from typing import List
from itertools import chain, product
from mutagen.mp3 import MP3
from mutagen.id3 import TALB, TIT2, TPE2, TOFN


def generate_permutations(text: str) -> List[str]:
    permutations: List[List[str]] = []
    words = text.split()

    for word in words:
        permutations.append([word.capitalize(), word.upper(), word.lower()])

    # ChatGPT for the win, lol
    result = []
    for sublist in product(*permutations):
        combined = " ".join(sublist)
        result.append(f"({combined})")
        result.append(f"[{combined}]")

    # => ["(Official Video), "[Official Video]", "(OFFICIAL Video)", "[OFFICIAL Video]", ...etc]
    return result


STRINGS_TO_REMOVE_PERMUTATIONS_OF = [
    "official",
    "official video",
    "official lyric video",
    "official music video",
    "official album track",
    "official track",
    "official audio",
    "official live",
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
]

TITLE_SEPARATORS = ["-", "–"]


SUBSTRINGS_TO_REMOVE = list(
    chain.from_iterable(
        (
            generate_permutations(string)
            for string in STRINGS_TO_REMOVE_PERMUTATIONS_OF
        )
    )
)

SUBSTRINGS_TO_REMOVE.extend(STRINGS_TO_ADDITIONALLY_REMOVE)


def main():
    folder_path = sys.argv[1]
    folder = os.scandir(path=folder_path)

    # generate_permutations("hello there")
    for collection in folder:
        process_collection(collection)


def clean_title(title: str, album: str, band: str):
    cleaned_title = title

    # if title starts with band name, remove it
    for char in TITLE_SEPARATORS:
        substring = f"{band.lower()} {char} "
        if cleaned_title.lower().startswith(substring):
            cleaned_title = cleaned_title[len(substring):]

    # additional case for when there is no separator between title and band name
    if cleaned_title.lower().startswith(band.lower()):
        cleaned_title = cleaned_title[len(band):]

    for substring in SUBSTRINGS_TO_REMOVE:
        cleaned_title = cleaned_title.replace(substring, "")

    # need to strip of whitespace for next part
    cleaned_title = cleaned_title.strip()

    if cleaned_title.startswith(("\"", "\'", "``")) and cleaned_title.endswith(("\"", "\'", "``")):
        cleaned_title = cleaned_title[1: -1]

    # if title contains name of album, remove
    cleaned_title.replace(f"({album})", "")
    cleaned_title.replace(f"({album.lower()})", "")
    cleaned_title.replace(f"({album.upper()})", "")

    return cleaned_title.strip()


def process_collection(collection: os.DirEntry):
    if collection.is_file():
        return

    band_name = collection.name
    print(band_name)

    for album in os.scandir(path=collection.path):
        album_name = album.name
        print("    " + album_name)

        for file in os.scandir(album.path):
            extension = os.path.splitext(file.path)[1]
            if not extension == ".mp3":
                return

            f = MP3(file.path)

            title = file.name.replace(".mp3", "")
            cleaned_title = clean_title(title, album_name, band_name)
            f["TIT2"] = TIT2(encoding=3, text=cleaned_title)
            f["TALB"] = TALB(encoding=3, text=album_name)
            f["TPE2"] = TPE2(encoding=3, text=band_name)

            try:
                f["TOFN"]
            except KeyError:
                f["TOFN"] = TOFN(encoding=3, text=title)

            f.save()


if __name__ == "__main__":
    main()
