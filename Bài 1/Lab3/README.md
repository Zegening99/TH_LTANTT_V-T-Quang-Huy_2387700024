##Họ và Tên: Võ Tự Quang Huy  
##MSSV: 23DATA1
##Lớp: 2387700024
##LAB 3: SECURELOGGER 
# BÁO CÁO PHÂN TÍCH BẢO MẬT HỆ THỐNG "SECURELOGGER"

## 1. Mục tiêu và phạm vi

**SecureLogger** (`securelogger/logger.py`, tích hợp trong `secure_logger_lab/app.py`) là một hệ thống ghi nhật ký (logging) hướng bảo mật, được thiết kế nhằm:

- Hỗ trợ đa cấp độ log (DEBUG/INFO/WARNING/ERROR/CRITICAL) theo module `logging` chuẩn của Python.
- Tự động **phát hiện và che dấu thông tin định danh cá nhân (PII)** trước khi ghi log.
- Quản lý **luân phiên log (rotation)** kèm nén dữ liệu (gzip) khi file vượt kích thước cho phép.
- **Phát hiện thay đổi trái phép** trên tập tin log (tamper detection) thông qua một file chữ ký (`secure.log.sig`).
- Ghi log theo **cấu trúc JSON** để dễ phân tích/tích hợp SIEM.
- Tích hợp với `SecureValidator` để ghi lại toàn bộ kết quả kiểm tra validation của endpoint `/validate`.

Báo cáo phân tích: (1) kỹ thuật đã áp dụng, (2) lỗ hổng/khả năng bypass **kèm đoạn code minh chứng**, (3) mức đáp ứng nguyên tắc bảo mật, (4) đề xuất khắc phục **kèm code giải pháp**.

---

## 2. Các kỹ thuật bảo mật đã áp dụng

| # | Kỹ thuật | Mô tả | Thành phần liên quan |
| --- | --- | --- | --- |
| 1 | **Che dấu PII (PII masking)** | Regex thay thế email và các cặp `token/apikey/key/password = value` bằng nhãn `<label_masked>` trước khi ghi log | `PII_PATTERNS`, `mask_pii()` |
| 2 | **Ghi log dạng JSON có cấu trúc** | Mỗi dòng log là một object JSON: `timestamp`, `level`, `message`, kèm `data`/`results` nếu có | `JSONFormatter` |
| 3 | **Log rotation theo kích thước** | Giới hạn `MAX_LOG_SIZE = 1MB`, giữ tối đa `BACKUP_COUNT = 2` bản backup, tránh log phình vô hạn | `RotatingFileHandler` (kế thừa) |
| 4 | **Nén log khi rotate** | Sau khi rotate, file cũ được nén bằng gzip, giảm dung lượng lưu trữ | `GZipRotator` |
| 5 | **Tamper-evidence (chống giả mạo log)** | Mỗi dòng log được băm SHA-256 và ghi vào file `secure.log.sig` riêng biệt | `hash_line()`, `append_signature()` |
| 6 | **Cô lập logger, chống rò rỉ log** | `logger.propagate = False` ngăn log bị đẩy lên root logger/handler khác ngoài ý muốn | `get_secure_logger()` |
| 7 | **Audit trail cho hoạt động validate** | Mọi lượt gọi `/validate` (kể cả JSON không hợp lệ) đều được log lại kèm dữ liệu đầu vào/kết quả | `app.py` (`secure_logger.info/warning`) |

---

## 3. Các lỗ hổng / khả năng bypass 

### 3.1 Cơ chế "tamper-evidence" không đủ mạnh — hash không có khóa bí mật

**Code gốc gây lỗ hổng** (`securelogger/logger.py`):

```python
def hash_line(line):
    return hashlib.sha256(line.encode('utf-8')).hexdigest()

def append_signature(line):
    with open(SIGNATURE_FILE, "a", encoding="utf-8") as f:
        f.write(hash_line(line) + "\n")
```

**Vì sao đây là lỗ hổng:** `hash_line()` chỉ là `SHA256(message)` thuần túy — **không có secret key**. Ai ghi được `secure.log` thì cũng ghi được `secure.log.sig` (cùng quyền OS). Kẻ tấn công có thể tái tạo một chữ ký "hợp lệ" sau khi sửa log:

```python
# Kịch bản tấn công: sửa log rồi tự vá lại "chữ ký" cho khớp
tampered_line = '{"timestamp": "...", "level": "INFO", "message": "Fake ok"}'
fake_signature = hashlib.sha256(tampered_line.encode('utf-8')).hexdigest()
# Ghi đè cả 2 file -> verify (nếu có) vẫn "pass"
```

Ngoài ra mỗi dòng được băm **độc lập** (không hash-chain), nên **xóa hẳn** một cặp (dòng log + dòng chữ ký) không để lại dấu vết gì.

---

### 3.2 PII masking không khớp định dạng dữ liệu thực tế (JSON)

**Code gốc gây lỗ hổng:**

```python
PII_PATTERNS = {
    "email": r'[\w\.-]+@[\w\.-]+\.\w+',
    "token": r'(?i)(token|apikey|key|password)\s*=\s*["\']?[\w\-]{4,}["\']?',
}

def mask_pii(text):
    for label, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"<{label}_masked>", text, flags=re.IGNORECASE)
    return text
```

**Vì sao đây là lỗ hổng:** pattern `"token"` chỉ khớp cú pháp `key = value` (dấu `=`). Nhưng dữ liệu thực tế log ra trong `app.py` lại là `str(dict)` từ `request.get_json()`, dùng dấu **`:`**:

```python
# app.py
secure_logger.info("Validation check performed",
                    extra={"data": data, "results": results})
# data = {"password": "abc123", "email": "a@b.com"}  -> str(data) chứa "'password': 'abc123'"
```

Chạy thử để chứng minh mask KHÔNG hoạt động với dữ liệu dạng dict/JSON:

```python
>>> mask_pii(str({"password": "abc123", "email": "a@b.com"}))
"{'password': 'abc123', '<email_masked>'}"
# -> password vẫn còn nguyên văn "abc123", chỉ email bị mask!
```

---

### 3.3 Không giới hạn quyền truy cập file log

**Code gốc (thiếu sót):**

```python
handler = SecureRotatingFileHandler(
    LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding="utf-8"
)
# -> file secure.log được tạo với quyền mặc định của OS (thường 644),
#    bất kỳ user nào trên máy cũng đọc được nội dung log (chứa PII, payload SQLi/XSS...)
```

---

### 3.4 Ghi đồng thời không có khóa file (race condition)

**Code gốc (thiếu sót):**

```python
def append_signature(line):
    with open(SIGNATURE_FILE, "a", encoding="utf-8") as f:
        f.write(hash_line(line) + "\n")
    # -> không có fcntl.flock(); nhiều worker Flask ghi cùng lúc
    #    có thể làm xen kẽ nội dung, lệch cặp (log, signature)
```

---

### 3.5 Fail-silent khi ghi log/chữ ký thất bại

**Code gốc gây lỗ hổng:**

```python
class SecureRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            super().emit(record)
            append_signature(msg)
        except Exception:
            self.handleError(record)   # <-- nuốt lỗi âm thầm, không cảnh báo ai
```

---

## 4. Đánh giá theo các nguyên tắc bảo mật

| Nguyên tắc | Đáp ứng? | Ghi chú |
| --- | --- | --- |
| **Confidentiality (bảo mật PII)** | ❌ Chưa đạt | Regex mask không khớp định dạng JSON thực tế → password/email có thể lọt nguyên văn vào log |
| **Integrity / Tamper-evidence** | ❌ Chưa đạt | Hash không dùng khóa bí mật (không phải HMAC), không phải hash-chain, chưa có hàm verify |
| **Availability (log không bị mất)** | ⚠️ Đạt một phần | Có rotation chống phình log, nhưng lỗi ghi bị nuốt âm thầm, không có backup off-site |
| **Non-repudiation (chống chối bỏ)** | ❌ Chưa đạt | Vì thiếu khóa bí mật, người có quyền ghi log hoàn toàn có thể tự tạo cặp (log, chữ ký) hợp lệ giả |
| **Least privilege** | ❌ Chưa đạt | Không có kiểm soát quyền file trên `secure.log`/`secure.log.sig` trong code |
| **Data minimization** | ⚠️ Đạt một phần | Có mask nhưng không đầy đủ, không có chính sách retention/xóa log theo thời gian |
| **Structured & auditable logging** | ✅ Đạt | JSON format, đa cấp độ log, có audit trail cho endpoint `/validate` |

**Kết luận:** Lab đạt phần "cấu trúc" (structured logging, rotation, multi-level logging), nhưng **hai tính năng cốt lõi — "che dấu PII" và "phát hiện thay đổi trái phép" — chưa đạt hiệu quả thực tế**.

---

## 5. Đề xuất giải pháp khắc phục (kèm code)

### 5.1 Sửa PII masking để khớp cả định dạng JSON và mở rộng phạm vi

```python
import re

PII_PATTERNS = {
    "email": r'[\w\.-]+@[\w\.-]+\.\w+',
    # Khớp cả "key = value" và "key": "value" / 'key': 'value'
    "token": r'(?i)(token|apikey|key|password)["\']?\s*[:=]\s*["\']?[\w\-]{4,}["\']?',
    "phone_vn": r'\b(0|\+84)(\d{9,10})\b',
    "credit_card": r'\b(?:\d[ -]*?){13,16}\b',
    "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
}

def mask_pii(text):
    for label, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"<{label}_masked>", text, flags=re.IGNORECASE)
    return text
```

Tốt hơn nữa — mask **trực tiếp trên dict** trước khi `str()`, thay vì mask trên chuỗi đã stringify (chính xác và ổn định hơn nhiều):

```python
SENSITIVE_KEYS = {"password", "token", "apikey", "key", "secret"}

def mask_dict(data: dict) -> dict:
    if not isinstance(data, dict):
        return data
    return {
        k: ("<masked>" if k.lower() in SENSITIVE_KEYS else v)
        for k, v in data.items()
    }

# Trong JSONFormatter.format():
if hasattr(record, "data"):
    record_dict["data"] = mask_pii(str(mask_dict(record.data)))
```

### 5.2 Chuyển từ hash thuần sang HMAC có khóa bí mật + hash-chain

```python
import hmac, hashlib, os

SECRET_KEY = os.environ["GITSECURE_LOG_KEY"].encode()  # lưu ngoài code, VD: biến môi trường/Vault
_last_signature = ""

def sign_line(line: str) -> str:
    global _last_signature
    payload = (_last_signature + line).encode('utf-8')
    sig = hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()
    _last_signature = sig
    return sig

def append_signature(line):
    sig = sign_line(line)
    with open(SIGNATURE_FILE, "a", encoding="utf-8") as f:
        f.write(sig + "\n")
```

→ Vì mỗi chữ ký phụ thuộc vào chữ ký trước đó (`_last_signature`), **xóa hoặc sửa bất kỳ dòng nào** cũng làm toàn bộ chuỗi phía sau không còn khớp khi verify. Vì dùng HMAC với `SECRET_KEY` không lộ ra ngoài, kẻ tấn công không thể tự tính lại chữ ký hợp lệ dù biết thuật toán.

### 5.3 Bổ sung hàm xác minh (hiện code gốc chưa có)

```python
def verify_log():
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        log_lines = f.readlines()
    with open(SIGNATURE_FILE, "r", encoding="utf-8") as f:
        sig_lines = [s.strip() for s in f.readlines()]

    if len(log_lines) != len(sig_lines):
        return False, "Số dòng log và chữ ký không khớp -> có thể đã bị xóa dòng"

    last_sig = ""
    for i, (line, sig) in enumerate(zip(log_lines, sig_lines)):
        expected = hmac.new(SECRET_KEY, (last_sig + line).encode('utf-8'),
                             hashlib.sha256).hexdigest()
        if expected != sig:
            return False, f"Phát hiện giả mạo tại dòng {i+1}"
        last_sig = sig
    return True, "Log toàn vẹn"
```

### 5.4 Giới hạn quyền file log

```python
import os, stat

handler = SecureRotatingFileHandler(
    LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding="utf-8"
)
os.chmod(LOG_FILE, stat.S_IRUSR | stat.S_IWUSR)          # 600: chỉ owner đọc/ghi
os.chmod(SIGNATURE_FILE, stat.S_IRUSR | stat.S_IWUSR)
```

### 5.5 Thêm file locking khi ghi đồng thời

```python
import fcntl

def append_signature(line):
    sig = sign_line(line)
    with open(SIGNATURE_FILE, "a", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)   # khóa độc quyền khi ghi
        try:
            f.write(sig + "\n")
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

### 5.6 Không fail-silent với lỗi ghi log bảo mật

```python
import sys

class SecureRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            super().emit(record)
            append_signature(msg)
        except Exception as e:
            # Cảnh báo chủ động thay vì nuốt lỗi âm thầm
            print(f"[CRITICAL] SecureLogger failed to write/sign log: {e}",
                  file=sys.stderr)
            self.handleError(record)
```

---

## 6. Tóm tắt

SecureLogger có khung logging có cấu trúc tốt (JSON, rotation, multi-level), nhưng hai chức năng bảo mật cốt lõi chưa hoạt động đúng như kỳ vọng: **PII masking bỏ sót dữ liệu định dạng JSON** (Mục 3.2) và **chữ ký log không có khóa bí mật nên có thể bị giả mạo** (Mục 3.1). Các đoạn code giải pháp ở Mục 5 (HMAC + hash-chain, hàm `verify_log()`, mask theo dict, giới hạn quyền file, file locking, fail-loud) giải quyết trực tiếp từng lỗ hổng đã nêu.
