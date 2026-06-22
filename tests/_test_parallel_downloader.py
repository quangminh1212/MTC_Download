import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import download_top5_bookmarks_to_mtc as mod
from mtc_status_utils import is_completed_status, is_ongoing_status


class DownloaderHelpersTest(unittest.TestCase):
    def test_build_unique_chapters_dedupes_ids(self):
        unique, duplicates = mod.build_unique_chapters([
            {'id': 11, 'name': 'A'},
            {'id': 12, 'name': 'B'},
            {'id': 11, 'name': 'A duplicate'},
        ])
        self.assertEqual([item['id'] for item in unique], [11, 12])
        self.assertEqual(duplicates, [11])

    def test_find_missing_chapters_uses_existing_ids(self):
        chapters = [
            {'id': 11, 'index': 1, 'name': 'A'},
            {'id': 12, 'index': 2, 'name': 'B'},
            {'id': 13, 'index': 3, 'name': 'C'},
        ]
        missing = mod.find_missing_chapters(chapters, {12})
        self.assertEqual([item['id'] for item in missing], [11, 13])

    def test_book_folder_name_uses_canonical_mtc_folder(self):
        folder = mod.book_folder_name(12345, 'Tên truyện, có dấu phẩy')
        self.assertFalse(folder.endswith('__12345'))
        self.assertFalse(folder.startswith('__'))

    def test_chapter_filename_uses_mtc_rule_not_technical_id(self):
        name = mod.chapter_filename({'id': 11, 'index': 7, 'name': 'Chương 7: Tiêu đề thử'})
        self.assertIn('7', name)
        self.assertFalse(name.startswith('chapter_'))
        self.assertTrue(name.endswith('.txt'))

    def test_format_chapter_text_includes_header_and_title(self):
        text = mod.format_chapter_text('Chương 7 Tiêu đề thử', 'Nội dung dòng 1\nNội dung dòng 2')
        self.assertTrue(text.startswith('=' * 60))
        self.assertIn('Chương 7 Tiêu đề thử', text)
        self.assertIn('Nội dung dòng 1', text)

    def test_collect_existing_ids_only_counts_valid_files(self):
        temp_dir = Path(tempfile.mkdtemp())
        try:
            chapters = [{'id': 11, 'index': 1, 'name': 'Chương 1: A'}]
            target = temp_dir / mod.chapter_filename(chapters[0])
            target.write_text('x' * 21, encoding='utf-8')
            self.assertEqual(mod.collect_existing_ids(temp_dir, chapters), {11})
        finally:
            shutil.rmtree(temp_dir)

    def test_reconcile_existing_chapter_files_moves_same_number_duplicates(self):
        temp_dir = Path(tempfile.mkdtemp())
        try:
            chapters = [{'id': 100, 'index': 5, 'name': 'Chương 5: Tên đúng'}]
            keep = temp_dir / mod.chapter_filename(chapters[0])
            extra = temp_dir / 'Chương 5 Tên sai cũ.txt'
            keep.write_text('x' * 100, encoding='utf-8')
            extra.write_text('y' * 80, encoding='utf-8')
            result = mod.reconcile_existing_chapter_files(temp_dir, chapters)
            self.assertTrue(keep.exists())
            self.assertFalse(extra.exists())
            self.assertEqual(len(result['duplicates']), 1)
        finally:
            shutil.rmtree(temp_dir)

    def test_normalize_existing_chapter_files_promotes_technical_name(self):
        temp_dir = Path(tempfile.mkdtemp())
        try:
            chapters = [{'id': 11, 'index': 1, 'name': 'Tên Chương 1'}]
            technical = temp_dir / mod.technical_chapter_filename(1, 11)
            technical.write_text('nội dung hợp lệ' * 5, encoding='utf-8')
            result = mod.normalize_existing_chapter_files(temp_dir, chapters)
            canonical = temp_dir / mod.chapter_filename(chapters[0])
            self.assertTrue(canonical.exists())
            self.assertEqual(len(result['moved']), 1)
            self.assertEqual(result['duplicates'], [])
        finally:
            shutil.rmtree(temp_dir)

    def test_maybe_commit_verified_book_skips_incomplete(self):
        result = mod.maybe_commit_verified_book(Path('C:/Dev/MTC/Bo A'), 'Bộ A', False)
        self.assertEqual(result['status'], 'not_complete')

    @mock.patch('download_top5_bookmarks_to_mtc.subprocess.run')
    def test_maybe_commit_verified_book_commits_only_folder_changes(self, run_mock):
        folder = Path('C:/Dev/MTC/Bo A')
        run_mock.side_effect = [
            mock.Mock(returncode=0, stdout='Bo A/file1.txt\n', stderr=''),
            mock.Mock(returncode=0, stdout='', stderr=''),
            mock.Mock(returncode=0, stdout='Bo A/file1.txt\nBo A/file2.txt\n', stderr=''),
            mock.Mock(returncode=0, stdout='[main abc123] Bộ A', stderr=''),
        ]
        result = mod.maybe_commit_verified_book(folder, 'Bộ A', True)
        self.assertEqual(result['status'], 'committed')
        self.assertEqual(result['staged_count'], 2)
        commit_cmd = run_mock.call_args_list[3].args[0]
        self.assertEqual(commit_cmd[-4:], ['-m', 'Bộ A', '--', str(folder)])

    @mock.patch('download_top5_bookmarks_to_mtc._clear_stale_git_lock', return_value=True)
    @mock.patch('download_top5_bookmarks_to_mtc.time.sleep')
    @mock.patch('download_top5_bookmarks_to_mtc.subprocess.run')
    def test_maybe_commit_verified_book_retries_after_index_lock(self, run_mock, _sleep, _clear_lock):
        folder = Path('C:/Dev/MTC/Bo A')
        run_mock.side_effect = [
            mock.Mock(returncode=0, stdout='Bo A/file1.txt\n', stderr=''),
            mock.Mock(returncode=0, stdout='', stderr=''),
            mock.Mock(returncode=0, stdout='Bo A/file1.txt\n', stderr=''),
            mock.Mock(returncode=1, stdout='', stderr='fatal: Unable to create index.lock'),
            mock.Mock(returncode=0, stdout='', stderr=''),
            mock.Mock(returncode=0, stdout='Bo A/file1.txt\n', stderr=''),
            mock.Mock(returncode=0, stdout='[main abc123] Bộ A', stderr=''),
        ]
        result = mod.maybe_commit_verified_book(folder, 'Bộ A', True)
        self.assertEqual(result['status'], 'committed')

    @mock.patch('download_top5_bookmarks_to_mtc.subprocess.run')
    def test_maybe_commit_verified_book_skips_when_clean(self, run_mock):
        folder = Path('C:/Dev/MTC/Bo A')
        run_mock.return_value = mock.Mock(returncode=0, stdout='', stderr='')
        result = mod.maybe_commit_verified_book(folder, 'Bộ A', True)
        self.assertEqual(result['status'], 'nothing_to_commit')

    def test_status_helpers_classify_books(self):
        self.assertTrue(is_completed_status({'status_name': 'Hoàn thành'}))
        self.assertTrue(is_completed_status({'status': 2}))
        self.assertTrue(is_ongoing_status({'status_name': 'Còn tiếp'}))
        self.assertTrue(is_ongoing_status({'status': 1}))
        self.assertFalse(is_completed_status({'status_name': 'Còn tiếp'}))

    def test_select_unfinished_books_skips_completed_first(self):
        books = [
            {'id': 1, 'name': 'A', 'status_name': 'Hoàn thành'},
            {'id': 2, 'name': 'B', 'status_name': 'Còn tiếp'},
            {'id': 3, 'name': 'C', 'status_name': 'Còn tiếp'},
        ]
        selected, skipped = mod.select_unfinished_books(books, 2)
        self.assertEqual([b['id'] for b in selected], [2, 3])
        self.assertEqual([b['id'] for b in skipped], [1])


if __name__ == '__main__':
    unittest.main()
