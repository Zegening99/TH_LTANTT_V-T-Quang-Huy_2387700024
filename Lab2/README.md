Họ và Tên: Võ Tự Quang Huy
MSSV: 23DATA1
Lớp: 2387700024
LAB 2: GITSECURE 
 # BÁO CÁO PHÂN TÍCH BẢO MẬT HỆ THỐNG PRE-COMMIT "GITSECURE"

## 1. Mục tiêu và phạm vi

Hệ thống **GitSecure** được triển khai dưới dạng một Git pre-commit hook (`.githooks/pre-commit`), thực thi tự động trước khi lệnh `git commit` hoàn tất, nhằm:

- Phát hiện thông tin nhạy cảm (secrets, credentials) bị hardcode trong mã nguồn.
- Kiểm tra quyền truy cập file (permission) bất thường.
- Thực hiện phân tích mã tĩnh (SAST) bằng Bandit đối với mã Python.
- Ghi nhật ký (log) các phát hiện để phục vụ điều tra sau này.
- Chặn (`sys.exit(1)`) commit nếu phát hiện rủi ro.

---

## 2. Các kỹ thuật bảo mật đã áp dụng

| # | Kỹ thuật | Mô tả | File/hàm liên quan |
| --- | --- | --- | --- |
| 1 | **Phát hiện secret bằng regex** | So khớp nội dung file với các pattern: `apikey`, `secret`, `password`, `token`, và AWS Access Key (`AKIA/ASIA`) | `SENSITIVE_PATTERNS`, `scan_sensitive()` |
| 2 | **Kiểm tra quyền file (world-writable)** | Dùng `os.stat()` + `stat.S_IWOTH` để phát hiện file có quyền ghi cho "other" — dấu hiệu cấu hình sai quyền | `check_permissions()` |
| 3 | **SAST tích hợp (Bandit)** | Chạy `bandit -r .` để quét lỗ hổng bảo mật trong code Python (chỉ lọc mức "High") | `run_bandit()` |
| 4 | **Shift-left security / Git hook enforcement** | Chặn commit ngay tại máy dev, trước khi code được đưa vào lịch sử repo | `main()`, `sys.exit(1)` |
| 5 | **Giới hạn phạm vi quét (staged files)** | Chỉ quét các file đang trong vùng staged (`git diff --cached --name-only`) thay vì toàn bộ repo → giảm chi phí xử lý | `main()` |
| 6 | **Audit logging** | Ghi lại từng phát hiện kèm timestamp vào `gitsecure.log` để truy vết | `log()` |

---

## 3. Các lỗ hổng / khả năng bypass

### 3.1 Bypass ở tầng thực thi hook

- **`git commit --no-verify`**: Git cho phép bỏ qua toàn bộ pre-commit hook bằng cờ này. Vì GitSecure chỉ là **client-side hook**, bất kỳ ai có quyền commit đều có thể vô hiệu hóa hoàn toàn hệ thống kiểm tra.
- **Hook không tự động phân phối**: `core.hooksPath` phải được từng thành viên tự cấu hình (`git config core.hooksPath .githooks`). Nếu clone repo mới mà quên chạy lệnh này, hook **không hề chạy** mà không có cảnh báo nào.

### 3.2 Bypass ở tầng phát hiện secret

- **Regex tĩnh, dễ bị né tránh**: các kỹ thuật obfuscation đơn giản có thể qua mặt:
  - Ghép chuỗi: `secret = "sec" + "ret_key_123456"`
  - Đổi tên biến không khớp pattern: `pwd_value = "123456"` (không khớp `password`)
  - Encode base64/hex trước khi lưu.
  - Format khác: `"Password": "abc123"` (JSON key viết hoa, có dấu `:` thay vì `=`).
- **Không có phát hiện theo entropy**: các secret ngẫu nhiên thực sự (ví dụ token JWT, private key) không khớp pattern cố định sẽ lọt qua, vì hệ thống không đo entropy chuỗi như các công cụ chuyên dụng (Gitleaks, TruffleHog).
- **Không quét lịch sử commit**: hook chỉ chặn commit **mới**; nếu secret đã từng lọt vào lịch sử Git trước khi có GitSecure, nó vẫn tồn tại vĩnh viễn trong repo.

### 3.3 Bypass ở tầng kiểm tra quyền file

- **Vô hiệu hóa trên Windows**: bản cập nhật của `check_permissions()` có đoạn:

  ```python
  if platform.system() == "Windows":
      return False
  ```

  Điều này khiến kiểm tra world-writable **bị tắt hoàn toàn** trên Windows (chỉ hoạt động trên Unix/Linux/macOS) — đây là kiểu "fail-open" (mất an toàn khi gặp trường hợp không xử lý được), vi phạm nguyên tắc *fail-safe default*.

### 3.4 Bypass ở tầng SAST (Bandit)

- **Parse output bằng string-matching mong manh**: `"SEVERITY: High" in result.stdout` — chỉ cần Bandit đổi định dạng output (khác phiên bản) là điều kiện này không còn đúng, khiến toàn bộ lỗi High severity **không bị phát hiện** mà không có cảnh báo.
- **Bỏ qua Medium/Low severity**: các lỗ hổng mức trung bình (SQL injection tiềm ẩn, hardcoded bind, v.v.) không bị chặn.
- **Chỉ áp dụng cho Python**: không có SAST cho các ngôn ngữ khác nếu repo đa ngôn ngữ.

### 3.5 Lỗ hổng ở tầng ghi log

- **Log không được bảo vệ toàn vẹn**: `gitsecure.log` là file văn bản thuần, không có cơ chế ký/hash như trong lab SecureLogger (không có `secure.log.sig`). Kẻ tấn công có quyền ghi vào thư mục dự án có thể **sửa hoặc xóa log** để xóa dấu vết mà không bị phát hiện.

### 3.6 Thiếu kiểm soát tập trung

- Toàn bộ cơ chế chỉ chạy **phía client**, không có tầng thực thi bắt buộc phía server (server-side hook, CI/CD gate, branch protection). Do đó GitSecure chỉ mang tính **khuyến nghị (advisory)**, không phải **kiểm soát bắt buộc (mandatory control)**.

---

## 4. Đánh giá theo các nguyên tắc bảo mật

| Nguyên tắc | Đáp ứng? | Ghi chú |
| --- | --- | --- |
| **Shift-left security** (phát hiện sớm) | ✅ Đạt một phần | Có chặn tại thời điểm commit, nhưng dễ bị bypass bằng `--no-verify` |
| **Defense in depth** (nhiều lớp phòng thủ) | ❌ Chưa đạt | Chỉ có một lớp duy nhất (client hook); thiếu lớp server-side/CI |
| **Fail-safe default** (mặc định an toàn khi lỗi) | ❌ Chưa đạt | Trên Windows, kiểm tra permission "fail-open" (bỏ qua thay vì cảnh báo) |
| **Auditability / Non-repudiation** (có thể truy vết, chống chối bỏ) | ⚠️ Đạt một phần | Có logging nhưng log không có cơ chế chống giả mạo (tamper-evidence) |
| **Least privilege** | ⚠️ Không trực tiếp áp dụng | Chỉ dò world-writable, chưa kiểm soát quyền truy cập theo vai trò |
| **Confidentiality của secrets** | ⚠️ Đạt một phần | Regex giảm rủi ro rõ ràng nhưng không chống được obfuscation/entropy cao |
| **Toàn vẹn mã nguồn (SAST)** | ⚠️ Đạt một phần | Chỉ phủ Python, chỉ mức High, parser dễ vỡ |

**Kết luận:** Hệ thống đã đạt được mục tiêu cơ bản là "triển khai một pre-commit hook có khả năng kiểm tra mã nguồn trước khi commit", nhưng **chưa đáp ứng đầy đủ** các nguyên tắc bảo mật nền tảng như *defense in depth* và *fail-safe default*, và đặc biệt dễ bị vô hiệu hóa hoàn toàn bởi chính người dùng cuối (client-side control).

---

## 5. Đề xuất giải pháp khắc phục

1. **Bổ sung lớp kiểm soát phía server/CI (bắt buộc kép — defense in depth)** Chạy lại đúng logic quét (secret scan + permission + SAST) trong pipeline CI/CD (GitHub Actions/GitLab CI) ở mỗi Pull Request, kết hợp branch protection rule "require status checks" — đảm bảo dù dev bypass hook local (`--no-verify`) thì merge vẫn bị chặn.
2. **Thay/khuyến khích dùng công cụ secret-scanning chuyên dụng** Tích hợp thêm **Gitleaks** hoặc **TruffleHog** (có entropy analysis + signature database cập nhật liên tục) song song với regex tự viết, giảm false negative với secret dạng ngẫu nhiên không theo pattern cố định.
3. **Tự động phân phối hook cho cả nhóm** Dùng framework `pre-commit` (Python) hoặc `husky` để hook được cài tự động khi `pip install`/`npm install`, tránh trường hợp thành viên quên `git config core.hooksPath`.
4. **Sửa lỗi fail-open trên Windows** Thay vì `return False` khi `platform.system() == "Windows"`, cần triển khai kiểm tra ACL tương đương của Windows (ví dụ dùng `icacls`/`win32security`) hoặc tối thiểu ghi log cảnh báo "permission check skipped on this OS" thay vì im lặng bỏ qua.
5. **Parse output Bandit theo JSON thay vì string-matching** Dùng `bandit -r . -f json`, `json.loads()` kết quả, và xét cả mức **Medium** trở lên tùy chính sách rủi ro của tổ chức, tránh phụ thuộc vào định dạng text có thể thay đổi giữa các phiên bản.
6. **Bảo vệ toàn vẹn file log (áp dụng kỹ thuật từ lab SecureLogger)** Áp dụng cơ chế hash-chain/ký từng dòng log tương tự `secure.log.sig` trong `securelogger` để `gitsecure.log` có tính chống giả mạo (tamper-evident), phát hiện được nếu log bị chỉnh sửa.
7. **Quét lại lịch sử Git định kỳ** Bổ sung job định kỳ (hoặc pre-push hook) chạy full-repo scan trên toàn bộ lịch sử commit bằng Gitleaks để phát hiện secret đã lọt vào trước khi có GitSecure; nếu phát hiện, thực hiện quy trình rotate secret + rewrite history (`git filter-repo`/BFG).
8. **Giám sát việc bypass** Ghi nhận (qua CI) số lần Pull Request được tạo mà không qua kiểm tra local, để có cơ sở đánh giá mức độ tuân thủ của team.

---

## 6. Tóm tắt

GitSecure là một ví dụ tốt về **shift-left security** ở mức cơ bản: kết hợp secret-pattern scanning, kiểm tra quyền file và SAST (Bandit) ngay tại thời điểm commit. Tuy nhiên, vì đây thuần túy là **client-side control**, hệ thống dễ bị vô hiệu hóa (`--no-verify`, quên cấu hình hooksPath) và có một số điểm yếu kỹ thuật (regex tĩnh, fail-open trên Windows, parser Bandit mong manh, log không tamper-evident). Để đạt mức độ bảo mật đầy đủ theo mô hình *defense in depth*, cần bổ sung lớp kiểm soát bắt buộc phía server/CI và nâng cấp các thành phần phát hiện đã liệt kê ở Mục 5.