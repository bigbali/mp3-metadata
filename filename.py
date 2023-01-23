import sys
import os
from mutagen.mp3 import MP3
from mutagen.id3 import TALB, TIT2, TPE2, TOFN

chars = ["-", "–"]
substrgings_to_remove = [
    "(OFFICIAL)",
    "(Official)",
    "(official)",
    "[OFFICIAL]",
    "[official]",
    "(OFFICIAL TRACK)",
    "(Official Track)",
    "(Official track)",
    "(official track)",
    "[OFFICIAL TRACK]",
    "[Official Track]",
    "[Official track]",
    "[official track]",
    "(OFFICIAL AUDIO)",
    "(Official Audio)",
    "(Official audio)",
    "(official audio)",
    "[OFFICIAL AUDIO]",
    "[Official Audio]",
    "[Official audio]",
    "[official audio]",
    "(OFFICIAL VIDEO)",
    "(Official Video)",
    "(Official video)",
    "(official video)",
    "[OFFICIAL VIDEO]",
    "[Official Video]",
    "[Official video]",
    "[official video]",
    "(MUSIC VIDEO)",
    "(Music Video)",
    "(music video)",
    "(music video)",
    "[MUSIC VIDEO]",
    "[Music Video]",
    "[music video]",
    "[music video]",
    "(MUSIC)",
    "(Music)",
    "(music)",
    "[MUSIC]",
    "[Music]",
    "[music]",
    "(OFFICIAL MUSIC VIDEO)",
    "(Official Music Video)",
    "(Official music video)",
    "(official music video)",
    "[OFFICIAL MUSIC VIDEO]",
    "[Official Music Video]",
    "[Official music video]",
    "[official music video]",
    "(OFFICIAL LYRIC VIDEO)",
    "(Official Lyric Video)",
    "(Official lyric video)",
    "(official lyric video)",
    "[OFFICIAL LYRIC VIDEO]",
    "[Official Lyric Video]",
    "[Official lyric video]",
    "[official lyric video]",
    "(LYRIC VIDEO)",
    "(Lyric Video)",
    "(Lyric video)",
    "(lyric video)",
    "[LYRIC VIDEO]",
    "[Lyric Video]",
    "[Lyric video]",
    "[lyric video]",
    "(LYRIC)",
    "(Lyric)",
    "(lyric)",
    "[LYRIC]",
    "[Lyric]",
    "[lyric]",
    "(Album Track)",
    "(Album track)",
    "(BONUS)",
    "(Bonus)",
    "(bonus)",
    "[BONUS]",
    "[Bonus]",
    "[bonus]",
    "(BONUS TRACK)",
    "(Bonus Track)",
    "(bonus track)",
    "[BONUS TRACK]",
    "[Bonus Track]",
    "[bonus track]",
    "| Napalm Records",
]
# TODO contains: live


def main():
    folder_path = sys.argv[1]
    folder = os.scandir(path=folder_path)
    for collection in folder:
        process_collection(collection)


def clean_title(title: str, album: str, band: str):
    cleaned_title = title

    # if title starts with band name, cut it
    for char in chars:
        substring = f"{band.lower()} {char} "
        if cleaned_title.lower().startswith(substring):
            cleaned_title = cleaned_title[len(substring) :]

    for substring in substrgings_to_remove:
        cleaned_title = cleaned_title.replace(substring, "")

    # if any of the following is additionally included, remove it
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
                print("no TOFN")
                f["TOFN"] = TOFN(encoding=3, text=title)

            f.save()


if __name__ == "__main__":
    main()
