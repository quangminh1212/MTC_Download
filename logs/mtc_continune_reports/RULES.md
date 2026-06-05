# Rule tải, lưu, đặt tên và kiểm tra truyện

## 1. Nguyên tắc chung
- Mỗi truyện là một folder riêng ở root repo.
- Mỗi chương là một file `.txt` riêng trong folder truyện.
- Không lưu file tải tạm, log chạy tool, cache, response API vào repo nếu không cần thiết.
- File sinh ra khi chạy tool phải nằm ngoài repo hoặc được thêm vào `.gitignore`.
- Chỉ commit nội dung đã tải xong, giải mã xong, kiểm tra xong.

## 2. Tải truyện
- Luôn tải theo `book_id`/ID truyện chính xác, không đoán theo tên gần giống.
- Khi tải thiếu chương, chỉ tải bổ sung chương thiếu, không tải lại toàn bộ nếu không cần.
- Nếu API trả `content` dạng mã hóa `eyJpdiI6...`, phải giải mã trước khi lưu commit.
- Nếu giải mã lỗi một chương, dùng dữ liệu cache/API trong `C:\Dev\MTC_DOWNLOAD` để đối chiếu lại ID chương.
- Không ghi đè nội dung cũ khi chưa xác minh chương mới đúng `index`, đúng tiêu đề, đúng truyện.

## 3. Lưu truyện
- Folder truyện đặt ngay tại root repo, tên là tên truyện đã làm sạch.
- Mỗi folder truyện phải có đúng một file JSON là `info.json`.
- Tất cả metadata của truyện, bao gồm danh sách/thông tin chương nếu có từ API, phải được tích hợp trong `info.json`.
- Không tạo hoặc giữ các JSON riêng khác trong folder truyện như `chapters_manifest.json`.
- Mỗi file chương phải dùng UTF-8.
- Nội dung file chương dùng format:

```text
============================================================
Chương <số> <tên chương>
============================================================

<nội dung chương>
```

- Không để payload mã hóa, JSON thô, HTML tag thừa, byte rác hoặc dòng debug trong file chương.

## 4. Đặt tên folder và file
- Tên folder/file không được chứa ký tự cấm Windows/Git: `< > : " / \ | ? *`.
- Bỏ ký tự trang trí không cần thiết trong tên file: ngoặc thừa, dấu câu rác, ký tự control.
- Tên file chương dùng mẫu:

```text
Chương <index> <tên chương>.txt
```

- Nếu tiêu đề chương trống, dùng:

```text
Chương <index>.txt
```

- Không dùng dấu `:` trong tên file, thay bằng khoảng trắng.
- Không để hai file trùng cùng một số chương trong cùng folder.

## 5. Kiểm tra sau khi tải
- Quét toàn folder truyện để chắc chắn không còn payload mã hóa dạng `eyJpdiI6...` hoặc chuỗi base64 dài bất thường.
- Quét lỗi ký tự chắc chắn:
  - ký tự thay thế `�` (`U+FFFD`)
  - control-char rác
  - mojibake rõ như `ChÆ°Æ¡ng`, `áº`, `á»`, `Ã`, `Â`
- Kiểm tra dòng 5-7 của từng file vì đây thường là vùng còn sót tiêu đề rác sau giải mã.
- Nếu ngay dưới dòng tiêu đề chương xuất hiện một dòng gần trùng tiêu đề (thiếu/mất vài ký tự, sai mã), phải xóa dòng đó.
- Dòng 7 nếu có rác/fragment tiêu đề phải sửa hoặc xóa, nhưng không xóa các dòng ngắt nhịp hợp lệ như `...`, `….`, `……`.
- Mở mẫu vài chương đầu, giữa, cuối để kiểm tra mắt thường trước khi commit.

## 6. Sửa lỗi nội dung
- Ưu tiên sửa tối thiểu đúng chỗ lỗi, không rewrite toàn file nếu không cần.
- Với mojibake toàn file, dùng `ftfy` hoặc logic phục hồi encoding đã kiểm chứng trước khi ghi đè.
- Với dòng đầu body bị rác sau giải mã, giữ tiêu đề từ tên file/header và xóa đoạn rác.
- Nếu không chắc nội dung đúng, đối chiếu lại bằng API/cache trong `C:\Dev\MTC_DOWNLOAD`.

## 7. Commit
- Commit theo từng folder truyện.
- Commit message trong repo này phải đúng tên folder top-level để qua hook.
- Không push remote.
- Sau mỗi đợt sửa, cập nhật công việc đã làm vào đúng ngày trong `C:\Dev\Work\2026` và commit repo `Work`.
