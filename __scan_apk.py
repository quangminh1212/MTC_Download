import zipfile


KEYS = [
	b"https://android.lonoapp.net/api/",
	b"/api/books",
	b"/api/chapters",
	b"filter%5Bbook_id%5D",
	b"search",
	b"library",
	b"favorite",
	b"bookmark",
	b"shelf",
	b"DownloadAllActivity",
	b"book_id",
	b"bookId",
	b"bookIds",
	b"bookTitle",
	b"basebook",
	b"imported.basebook",
	b"chapter WHERE bookId=",
	b"slug",
	b"author",
]


with zipfile.ZipFile("MTC.apk") as archive:
	for name in archive.namelist():
		if not name.endswith(".dex"):
			continue

		data = archive.read(name)
		print(f"### {name}")
		found_any = False
		for key in KEYS:
			index = data.find(key)
			if index < 0:
				continue

			found_any = True
			start = max(0, index - 120)
			end = min(len(data), index + 280)
			snippet = data[start:end].decode("latin1", "ignore")
			print(f"-- key={key.decode('latin1', 'ignore')}")
			print(snippet)
			print("---")

		if not found_any:
			print("(no keyword hits)")
