# MTC_Download

## Layout
- `scripts/` → runnable Python tooling
- `scripts/download/` → download/export flows
- `scripts/audit/` → checking, inventory, reports
- `scripts/repair/` → fix/rebuild missing content
- `scripts/cleanup/` → rename/sanitize/dedupe
- `scripts/reverse/` → APK, dex, libapp reverse-engineering
- `scripts/ops/` → orchestration/helpers/batch scripts
- `data/` → JSON manifests, reports, sample data
- `docs/` → user docs and analysis notes
- `archives/` → `MTC.apk`, `MTC.zip`, extracted artifacts source
- `logs/` → runtime logs and reports
- `tests/` → smoke/unit scripts

## Core files
- `scripts/mtc_downloader.py`
- `scripts/mtc_api_analysis.py`
- `scripts/mtc_exporter.py`
- `scripts/download/download_one_book_decrypted_to_mtc.py`
- `scripts/audit/sync_mtc_via_info.py`

## Notes
- `archives/mtc_extracted/` is generated from `archives/MTC.apk`.
- Keep downloads/reports in `data/` or `logs/`, not repo root.
- Prefer adding new automation under the closest subfolder above.
