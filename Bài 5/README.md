# BUOI5 - Phân tích và kiểm thử bảo mật

Nguồn: `lab-05 (1).pdf`, 24 trang, Bài 5. Đã đọc toàn bộ phần chữ và đối chiếu trực quan các trang có ảnh mã nguồn. Cấu trúc theo ảnh mẫu BUOI3 của bạn:

```text
BUOI5/
├── LAB01/                 # SAST-TOOL, mục 5.2
│   ├── examples/
│   ├── rules/
│   ├── sast_tool/
│   ├── tests/
│   ├── image/             # để bạn chèn ảnh thực hành
│   ├── requirements.txt
│   ├── report_01.sarif
│   ├── report_02.sarif
│   ├── verification.txt
│   └── README.md
├── LAB02/                 # DAST-TOOL, mục 5.4
│   ├── tests/
│   ├── image/             # để bạn chèn ảnh thực hành
│   ├── __init__.py
│   ├── memory_analyzer.py
│   ├── network_traffic_analyzer.py
│   ├── runtime_monitor.py
│   ├── security_behavior_checker.py
│   ├── virtual_sandbox.py
│   ├── main.py
│   ├── app.py
│   ├── requirements.txt
│   ├── verification.txt
│   └── README.md
├── .gitignore
└── README.md
```

## Bắt đầu trong VS Code

1. Nếu dùng ZIP, giải nén trước. Chọn **File → Open Folder... → BUOI5**.
2. Mở [hướng dẫn LAB01](LAB01/README.md), nhấn Ctrl+Shift+V để xem.
3. Mở Terminal → New Terminal, chọn PowerShell; làm tuần tự bước tạo `.venv`, cài thư viện, chạy test, chạy chương trình trong README của từng LAB.
4. Làm xong LAB01 thì mở terminal mới từ BUOI5 và chuyển sang [hướng dẫn LAB02](LAB02/README.md). Mỗi LAB dùng môi trường riêng `.venv`.
5. Chụp ảnh quá trình chạy thật trong VS Code và lưu vào `LAB01/image` hoặc `LAB02/image` theo danh sách trong README. Các thư mục này hiện chỉ có `.gitkeep`, chưa có ảnh.

## Đối chiếu file với PDF

| Trang | File/nội dung đã chép |
|---|---|
| 1-3 | Lý thuyết AST, pattern matching, chất lượng mã; làm bối cảnh, không phải LAB riêng |
| 4 | Yêu cầu SAST, cấu trúc và requirements LAB01 |
| 5 | examples/vulnerable_01.py |
| 6 | examples/vulnerable_02.py, rules/default_rules.json, sast_tool/__init__.py, ast_analyzer.py |
| 7-8 | code_quality_checker.py, sarif_reporter.py, security_rule_engine.py, phần đầu vuln_pattern_matcher.py |
| 9 | phần còn lại vuln_pattern_matcher.py, sast_tool/main.py, tests/__init__.py |
| 10-12 | 5 file unit test SAST (6 test case) và hướng dẫn chạy/xem báo cáo |
| 13 | Kết quả minh họa và thao tác Git trong tài liệu; không tự commit/push |
| 14-16 | Lý thuyết DAST và yêu cầu bài thực hành |
| 17 | requirements LAB02, memory_analyzer.py, network_traffic_analyzer.py |
| 18 | runtime_monitor.py, security_behavior_checker.py |
| 19 | virtual_sandbox.py, main.py |
| 20-21 | app.py, test_memory_analyzer.py, test_network_traffic_analyzer.py, đầu test_runtime_monitor.py |
| 22 | phần còn lại test_runtime_monitor.py, test_security_behavior_checker.py, test_virtual_sandbox.py |
| 23 | Lệnh chạy main, Flask và hướng dẫn Git trong PDF |
| 24 | Trang trống |

## Nguyên tắc giữ mã nguồn

Giữ tên file, module, class, hàm, test, endpoint, chuỗi mẫu và logic trong ảnh code của PDF. Chỉ đổi thư mục bao ngoài `sast-tool` thành `LAB01`, `dast-tool` thành `LAB02` để khớp cấu trúc yêu cầu. Phục hồi thụt dòng/xuống dòng từ ảnh và thêm newline cuối file; không thêm chức năng hoặc sửa các hạn chế logic của bài. Mã Python là mã thông dịch: đã kiểm tra cú pháp/biên dịch bytecode và chạy thực tế, không tạo file exe.

Các file bổ sung phục vụ bàn giao: README, thư mục image với `.gitkeep`, `.gitignore`, log verification và hai báo cáo SAST sinh khi chạy thử. Kịch bản kiểm chứng và môi trường agent nằm ngoài BUOI5, không đưa vào ZIP.

## Kết quả đã chạy thật ngày 20/10/2026

| Hạng mục | Kết quả |
|---|---|
| Cú pháp toàn bộ file Python | Đạt |
| LAB01 unit test nguyên bản | 6/6 đạt |
| SAST vulnerable_01.py | Thành công, 8 issues |
| SAST vulnerable_02.py | Thành công, 4 issues |
| Báo cáo SAST | Đã sinh và đọc lại JSON của cả hai báo cáo |
| LAB02 unit test nguyên bản | 5/5 đạt |
| LAB02 main.py | Chạy thành công, stdout sandbox đúng |
| GET /api/monitor | HTTP 200 |
| GET /api/memory | HTTP 200, overflow_test=true |
| GET /api/network | HTTP 200 |
| GET /api/security | HTTP 200 |
| POST /api/sandbox | HTTP 200, echo Hello Sandbox đúng, stderr rỗng |
| Ảnh chụp VS Code | Bạn tự bổ sung, chưa có |
| SARIF Viewer trong VS Code | Chưa kiểm chứng trực tiếp extension |
| Git commit/push | Chưa thực hiện |

Xem log gốc: [LAB01/verification.txt](LAB01/verification.txt), [LAB02/verification.txt](LAB02/verification.txt). Không coi test đạt là bằng chứng mọi khả năng lý thuyết đều có trong mã mẫu. Các giới hạn cụ thể đã ghi trong README từng LAB.

## Môi trường kiểm chứng

Windows, Python 3.11; flake8 7.4.1, sarif-om 1.0.4, jsonpickle 4.1.4, psutil 7.2.2, Flask 3.1.3. Requirements giữ theo PDF, không khóa phiên bản. Có DeprecationWarning của jsonpickle về thay đổi mặc định trong tương lai, không có test thất bại.

API sandbox thực thi shell và không có cơ chế cách ly thật; README hướng dẫn chạy server trên loopback bằng Flask CLI. File app.py vẫn giữ `0.0.0.0:5000` đúng bản gốc. Dịch vụ kiểm chứng đã được dừng sau khi thử.
