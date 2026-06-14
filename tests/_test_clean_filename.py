from download_completed_to_mtc import clean_filename
tests=[
    'Chương 10: Phật Tổ Như Lai!',
    'Tru Tiên Trận! Khởi!',
    'A/B:C*D?E|F"G<H>I'
]
for t in tests:
    print(clean_filename(t))
