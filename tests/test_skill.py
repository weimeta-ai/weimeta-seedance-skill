import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
import os
import tempfile
import unittest

FILE=Path(__file__).resolve().parents[1]/"scripts"/"weimeta_video.py"
spec=importlib.util.spec_from_file_location("weimeta_video",FILE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Tests(unittest.TestCase):
    def parse(self,*args):
        return m.parser().parse_args(["generate",*args])

    def test_t2v(self):
        d=m.payload(self.parse("--mode","t2v","--prompt","测试","--ratio","9:16","--duration","8"))
        self.assertEqual(d["model"],m.DEFAULT_MODEL)
        self.assertEqual(d["content"][0]["text"],"测试")
        self.assertEqual(d["duration"],8)

    def test_i2v(self):
        d=m.payload(self.parse("--mode","i2v","--first-frame","https://example.org/image.jpg"))
        self.assertEqual(d["content"][0]["role"],"first_frame")

    def test_i2v_requires_image(self):
        with self.assertRaises(m.SkillError):
            m.payload(self.parse("--mode","i2v"))

    def test_r2v_roles(self):
        d=m.payload(self.parse("--mode","r2v","--image","asset://i","--audio","asset://a","--video","asset://v"))
        self.assertEqual([c["role"] for c in d["content"]],["reference_image","reference_video","reference_audio"])
        self.assertEqual(d["omni_reference_task_type"],"reference")

    def test_edit_duration(self):
        d=m.payload(self.parse("--mode","edit","--video","asset://v"))
        self.assertEqual(d["duration"],-1)
        self.assertEqual(d["ratio"],"adaptive")

    def test_extend_requires_video(self):
        with self.assertRaises(m.SkillError):
            m.payload(self.parse("--mode","extend"))

    def test_disallow_media_in_t2v(self):
        with self.assertRaises(m.SkillError):
            m.payload(self.parse("--prompt","hello","--image","asset://x"))

    def test_disallow_http_media(self):
        with self.assertRaises(m.SkillError):
            m.media("http://example.org/file.mp4","video")

    def test_disallow_local_video(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
            with self.assertRaises(m.SkillError):
                m.media(f.name,"video")

    def test_wrong_edit_duration(self):
        with self.assertRaises(m.SkillError):
            m.payload(self.parse("--mode","edit","--video","asset://v","--duration","8"))

    def test_no_paid_post_by_default(self):
        with patch.object(m,"request",side_effect=AssertionError("NETWORK")):
            self.assertEqual(m.main(["generate","--prompt","hello"]),1)

    def test_dry_run_zero_network(self):
        with patch.object(m,"request",side_effect=AssertionError("NETWORK")):
            self.assertEqual(m.main(["generate","--prompt","hello","--dry-run"]),0)

    def test_doctor_zero_network(self):
        with patch.object(m,"request",side_effect=AssertionError("NETWORK")):
            self.assertEqual(m.main(["doctor"]),0)

    def test_task_id_reject_path_traversal(self):
        with self.assertRaises(m.SkillError):
            m.task("../passwd")

    def test_media_b64_preview_redacted(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as f:
            f.write(b"\x89PNG\r\n\x1a\n")
            f.flush()
            d=m.payload(self.parse("--mode","i2v","--first-frame",f.name))
            self.assertIn("REDACTED",m.preview(d)["content"][0]["image_url"]["url"])

    def test_bad_base_url(self):
        with patch.dict(os.environ,{"WEIMETA_VIDEO_BASE_URL":"http://example.org"}):
            with self.assertRaises(m.SkillError):
                m.endpoint()

    def test_key_fallback_from_local_0600_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"cred.json"
            path.write_text('{"api_key":"unit-test-placeholder"}')
            path.chmod(0o600)
            with patch.dict(os.environ,{"WEIMETA_API_KEY":""}), patch.object(m,"credentials_file",return_value=path):
                self.assertEqual(m.secret(),"unit-test-placeholder")

    def test_insecure_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"cred.json"
            path.write_text('{"api_key":"unit-test-placeholder"}')
            path.chmod(0o644)
            with patch.dict(os.environ,{"WEIMETA_API_KEY":""}), patch.object(m,"credentials_file",return_value=path):
                with self.assertRaises(m.SkillError):
                    m.secret()

    def test_configure_stores_hidden_key_safely(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"config"/"cred.json"
            with patch.object(m,"credentials_file",return_value=path), patch.object(m.sys.stdin,"isatty",return_value=True), patch.object(m.getpass,"getpass",return_value="fake-key"):
                m.configure()
            self.assertEqual(path.stat().st_mode & 0o777,0o600)
            self.assertEqual(json.loads(path.read_text())["api_key"],"fake-key")

    def test_seedance25_rejects_too_short(self):
        with self.assertRaises(m.SkillError):
            m.payload(self.parse("--mode","t2v","--prompt","test","--duration","3"))

    def test_seedance20_limits_duration(self):
        with self.assertRaises(m.SkillError):
            m.payload(self.parse("--mode","t2v","--model","doubao-seedance-2-0-260128","--prompt","test","--duration","16"))

    def test_terminal_includes_expired(self):
        self.assertIn("expired",m.TERMINAL)

    def test_authenticated_catalog_mock(self):
        class Dummy:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self):
                return b'{"data":[{"id":"doubao-seedance-2-5-260628"},{"id":"other-model"}]}'
        with patch.object(m, "secret", return_value="dummy"), patch.object(m.urllib.request, "urlopen", return_value=Dummy()) as call:
            catalog=m.catalog()
        self.assertEqual(catalog["seedance_model_ids"],["doubao-seedance-2-5-260628"])
        self.assertFalse(catalog["fee_information_included"])
        self.assertEqual(call.call_count,1)

    def test_redact_signed_download_url(self):
        raw = {"content": {"video_url": "https://example.com/video.mp4?X-Tos-Signature=secret"}, "id": "task_ok"}
        safe = m.redact_output(raw)
        self.assertNotIn("secret", json.dumps(safe))
        self.assertEqual(safe["id"], "task_ok")
        self.assertEqual(raw["content"]["video_url"], "https://example.com/video.mp4?X-Tos-Signature=secret")

    def test_redact_nested_key_and_data_uri(self):
        safe=m.redact_output({"api_key":"secret","content":[{"image_url":{"url":"data:image/png;base64,AAAA"}}]})
        self.assertEqual(safe["api_key"], "[REDACTED]")
        self.assertEqual(safe["content"][0]["image_url"]["url"], "[INLINE_MEDIA_REDACTED]")

if __name__=="__main__":
    unittest.main()
