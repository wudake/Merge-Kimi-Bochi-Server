"""
DVA 整合鉴权层单元测试
验证：X-User-Id header 信任模式、ProxyFix 子路径感知、login_required 行为
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 在导入 app_simple 前 mock 掉缺失的第三方依赖
sys.modules["edge_tts"] = MagicMock()
sys.modules["edge_tts"].Communicate = MagicMock
sys.modules["qrcode"] = MagicMock()
sys.modules["qrcode"].make = MagicMock()
sys.modules["whisper"] = MagicMock()
sys.modules["whisper"].load_model = MagicMock()

# 同样 mock core 子模块
for mod_name in ["tts_generator", "qr_generator", "editor_advanced", "downloader_pw",
                 "audio_extractor", "local_transcriber", "transcriber", "formatter",
                 "utils", "ads_extractor"]:
    sys.modules[mod_name] = MagicMock()

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core"))

from app_simple import app


class TestDVAAuthIntegration(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["SECRET_KEY"] = "test-secret"

    def test_index_with_x_user_id_header(self):
        """Nginx 传递 X-User-Id 时应允许访问受保护路由"""
        with self.client as c:
            resp = c.get("/", headers={"X-User-Id": "user-123"})
            self.assertEqual(resp.status_code, 200)

    def test_index_without_header_redirects_to_login(self):
        """无 X-User-Id 且无 session 时应重定向到登录页"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_index_with_session_allows_access(self):
        """本地开发兜底：已有 session 时允许访问"""
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_login_with_x_user_id_redirects_to_index(self):
        """Nginx 已鉴权时访问 /login 应直接跳转到首页"""
        resp = self.client.get("/login", headers={"X-User-Id": "user-123"})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/", resp.headers.get("Location", ""))

    def test_login_without_header_renders_form(self):
        """无鉴权时 /login 应渲染登录页"""
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"login", resp.data.lower())

    def test_login_post_creates_session(self):
        """本地开发兜底：POST 登录应创建 session"""
        resp = self.client.post("/login", data={"username": "tester"})
        self.assertEqual(resp.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertTrue(sess.get("logged_in"))
            self.assertEqual(sess.get("username"), "tester")

    def test_logout_clears_session(self):
        """/logout 应清除 session 并重定向到登录页"""
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["username"] = "tester"
        resp = self.client.get("/logout")
        self.assertEqual(resp.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertNotIn("logged_in", sess)

    def test_proxy_fix_prefix(self):
        """ProxyFix 最终会将 X-Forwarded-Prefix 转为 SCRIPT_NAME，url_for 据此生成带前缀的 URL"""
        # 使用 base_url 模拟 SCRIPT_NAME=/dva 的请求上下文
        with app.test_request_context("/", base_url="http://localhost/dva"):
            from flask import url_for
            login_url = url_for("login")
            self.assertEqual(login_url, "/dva/login")


if __name__ == "__main__":
    unittest.main()
