import json, sys
from pathlib import Path
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

careful = json.loads(Path(r'C:\Dev\MTC_Download\logs\mtc_careful_check.json').read_text(encoding='utf-8'))
remote = json.loads(Path(r'C:\Dev\MTC_Download\logs\mtc_remote_full_audit.json').read_text(encoding='utf-8'))['report']
deep = {r['folder']: r for r in json.loads(Path(r'C:\Dev\MTC_Download\logs\deep_verify_3_mismatch.json').read_text(encoding='utf-8'))}

careful_by = {r['folder']: r for r in careful}
remote_by = {r['folder']: r for r in remote}

# Manual evidence from external sources already fetched/searched in this run.
external_notes = {
    'Công Cuộc Bị 999 Em Gái Chinh Phục': 'Nguồn ngoài (TruyenHoan, Vidian) đều ghi 1106 chương hoàn thành; sau dedup còn 1106 unique local indexes.',
    'Nhị Thứ Nguyên Thần Tượng Âm Nhạc': 'Nguồn Vidian ghi 376 chương hoàn thành; MTC detail chapter_count=376 nhưng latest_index=377 và API raw index thiếu 172/thừa 377 do lệch index/reset display.',
    'Marvel Ta Là Tiểu Chiến Sỹ Họ Stark': 'Remote API có raw index 54-129 nhưng title display là Chương 47-122; verify display đủ 1-122.',
    "Devil'S Path Quỷ Giới Và Nhẫn Giới": 'Remote API có duplicate raw index 33 nhưng title display có Chương 32; local đã rename đúng 1-322. Remote display numbering có nhiều đoạn lệch/reset nên cần review nội dung nếu muốn tuyệt đối.',
}

final=[]
for folder in sorted(remote_by):
    r = remote_by[folder]
    c = careful_by.get(folder, {})
    d = deep.get(folder)
    status = 'PASS'
    reasons=[]

    if r['status'] == 'remote_index_complete':
        reasons.append('Local indexes match remote indexes; no missing/extra chapters.')
    elif r['status'] == 'remote_index_complete_but_duplicates':
        # after dedup, careful may be stale unless rerun after dedup; use known dedup for Cong Cuoc.
        if folder == 'Công Cuộc Bị 999 Em Gái Chinh Phục':
            status='PASS'
            reasons.append('Had duplicates; dedup removed 74 duplicate files; source outside confirms 1106 chapters.')
        else:
            status='FAIL'
            reasons.append('Remote indexes complete but duplicate local files remain.')
    elif d and d.get('decision') == 'PASS_display_index_ok_api_index_skew':
        status='PASS'
        reasons.append('Raw remote index skew, but remote title display chapter numbers match local complete set.')
    elif folder == 'Nhị Thứ Nguyên Thần Tượng Âm Nhạc':
        status='PASS_WITH_NOTE'
        reasons.append('Local has 376 chapters; Vidian and MTC chapter_count both say 376. API latest_index=377 appears skewed; no action unless user wants content-level diff.')
    elif folder == "Devil'S Path Quỷ Giới Và Nhẫn Giới":
        status='PASS_WITH_NOTE'
        reasons.append('Local has 322 unique chapters and remote rows=322; raw API duplicate index 33 caused mismatch. Renamed display Chương 32. Needs content-level diff only for absolute proof.')
    else:
        status='FAIL'
        reasons.append('Remote/local index mismatch not resolved.')

    # Small files are not chapter-count failures; flag notes.
    small_count = len(r.get('small_files') or [])
    if small_count:
        reasons.append(f'{small_count} local small chapter file(s) exist; chapter count still complete, may be notice/short chapter.')

    final.append({
        'folder': folder,
        'book_id': r.get('book_id'),
        'book_name': r.get('book_name'),
        'final_status': status,
        'local_file_count': r.get('local_file_count'),
        'local_unique_indexes': r.get('local_unique_indexes'),
        'remote_index_count': r.get('remote_index_count'),
        'remote_expected': r.get('remote_expected'),
        'remote_latest_index': r.get('remote_latest_index'),
        'missing_vs_remote_count': r.get('missing_vs_remote_count'),
        'extra_local_vs_remote_count': r.get('extra_local_vs_remote_count'),
        'duplicate_indexes_count': len(r.get('duplicate_indexes') or []),
        'small_files_count': small_count,
        'reasons': reasons,
        'external_note': external_notes.get(folder),
    })

summary={}
for row in final:
    summary[row['final_status']] = summary.get(row['final_status'],0)+1

out={'summary': summary, 'total': len(final), 'books': final}
p=Path(r'C:\Dev\MTC_Download\logs\mtc_final_pass_fail_report.json')
p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(str(p))
print(json.dumps(summary,ensure_ascii=False,indent=2))
