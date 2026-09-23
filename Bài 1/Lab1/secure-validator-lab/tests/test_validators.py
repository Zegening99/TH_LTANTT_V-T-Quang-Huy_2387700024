import unittest
from securevalidator import (
    validate_email, validate_url, validate_filename,
    sanitize_sql_input, sanitize_html_input
)

class TestValidators(unittest.TestCase):
    def setUp(self):
        print("\n Running:", self._testMethodName)

    def test_validate_email_valid(self):
        self.assertTrue(validate_email("user@example.com"))  

    def test_validate_email_invalid(self):
        self.assertFalse(validate_email("user@@example..com"))

    def test_validate_url_valid(self):
        self.assertTrue(validate_url("https://example.com"))

    def test_validate_url_invalid(self):
        self.assertFalse(validate_url("ftp://example.com"))

    def test_validate_filename_valid(self):
        self.assertTrue(validate_filename("report.pdf"))

    def test_validate_filename_traversal(self):
        self.assertFalse(validate_filename("../../etc/passwd"))

    def test_sanitize_sql_input_injection(self):
        input_str = "' OR 1=1 --"
        sanitized = sanitize_sql_input(input_str)
        self.assertNotIn("'", sanitized)
        self.assertNotIn("--", sanitized)
        self.assertNotIn("OR", sanitized.upper())

    def test_sanitize_sql_input_safe_text(self):
        input_str = "hello world"
        sanitized = sanitize_sql_input(input_str)
        self.assertEqual(sanitized, "hello world")

    def test_sanitize_html_input_script(self):
        input_str = '<script>alert("XSS")</script>'
        sanitized = sanitize_html_input(input_str)
        self.assertEqual(sanitized, '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;')

    def test_sanitize_html_input_safe_text(self):
        input_str = "Hello World"
        sanitized = sanitize_html_input(input_str)
        self.assertEqual(sanitized, "Hello World")

    # ================================
    # CÁC TEST MỚI: tìm điểm mù của validate_email
    # ================================

    def test_validate_email_unicode_homograph(self):
        # Kỳ vọng: domain chứa ký tự lạ (ä) phải bị từ chối vì rủi ro giả mạo domain
        self.assertFalse(validate_email("test@gmäil.com"))

    def test_validate_email_double_dot_local_bypass(self):
        # Kỳ vọng: 2 dấu chấm liền nhau ở local-part là không hợp lệ theo RFC
        self.assertFalse(validate_email("test..a@gmail.com"))

    def test_validate_email_leading_dot_bypass(self):
        # Kỳ vọng: dấu chấm ở đầu local-part là không hợp lệ theo RFC
        self.assertFalse(validate_email(".test@gmail.com"))

    def test_validate_email_double_dot_domain_bypass(self):
        # Kỳ vọng: 2 dấu chấm liền nhau ở domain là không hợp lệ
        self.assertFalse(validate_email("test@gmail..com"))


if __name__ == "__main__":
    unittest.main()