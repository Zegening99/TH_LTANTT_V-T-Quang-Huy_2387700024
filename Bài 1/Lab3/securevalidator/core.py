# NOTE: Nội dung gốc của securevalidator/core.py nằm ở bài lab TRƯỚC
# ("secure-validator-lab"), không xuất hiện trong các ảnh vừa gửi.
# Theo hướng dẫn ở trang 27, bạn cần copy nguyên file thật từ:
#   secure-validator-lab/securevalidator/  ->  secure_logger_lab/securevalidator/
#
# File dưới đây chỉ là bản STUB tạm thời để app.py chạy được ngay,
# khớp đúng tên hàm mà app.py import. Hãy thay thế bằng code gốc của bạn.

import re


def validate_email(value: str):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, value or ""))


def validate_url(value: str):
    pattern = r'^https?://[^\s]+$'
    return bool(re.match(pattern, value or ""))


def validate_filename(value: str):
    pattern = r'^[\w,\s-]+\.[A-Za-z0-9]+$'
    return bool(re.match(pattern, value or ""))


def sanitize_sql_input(value: str):
    if not value:
        return value
    return re.sub(r"['\";\-\-]", "", value)


def sanitize_html_input(value: str):
    if not value:
        return value
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
