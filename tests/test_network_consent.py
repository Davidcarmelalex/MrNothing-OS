"""Offline regression tests for the legacy network diagnostics consent boundary."""
import importlib.util
import os
import socket
import subprocess
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "modules" / "network" / "network.py"
SPEC = importlib.util.spec_from_file_location("network_module_under_test", MODULE_PATH)
NETWORK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NETWORK)


class NetworkDiagnosticsConsentTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {}, clear=False)
        self.environment.start()
        os.environ.pop(NETWORK.ALLOWED_TARGETS_ENV, None)
        self.limiter = NETWORK.ProbeRateLimiter()
        self.limiter_patch = patch.object(NETWORK, "RATE_LIMITER", self.limiter)
        self.limiter_patch.start()

    def tearDown(self):
        self.limiter_patch.stop()
        self.environment.stop()

    def allow(self, value="192.168.56.10"):
        os.environ[NETWORK.ALLOWED_TARGETS_ENV] = value

    def test_target_parser_accepts_only_private_ipv4_literals(self):
        self.assertEqual(NETWORK._canonical_private_ipv4("192.168.56.10"), "192.168.56.10")
        self.assertEqual(NETWORK._canonical_private_ipv4("10.0.0.7"), "10.0.0.7")
        self.assertEqual(NETWORK._canonical_private_ipv4("127.0.0.1"), "127.0.0.1")
        for value in (
            "8.8.8.8", "example.com", "https://192.168.56.10",
            "192.168.56.10;id", "-n", "::1", "0.0.0.0", " 192.168.56.10",
        ):
            with self.subTest(value=value):
                self.assertIsNone(NETWORK._canonical_private_ipv4(value))

    def test_allowlist_is_exact_and_malformed_entry_denies_all(self):
        self.allow("192.168.56.10,10.0.0.7")
        self.assertEqual(
            NETWORK._load_allowed_targets(),
            frozenset({"192.168.56.10", "10.0.0.7"}),
        )
        self.allow("192.168.56.10,8.8.8.8")
        self.assertEqual(NETWORK._load_allowed_targets(), frozenset())
        self.allow("192.168.56.10, 10.0.0.7")
        self.assertEqual(NETWORK._load_allowed_targets(), frozenset())
        self.allow("x" * (NETWORK.MAX_ALLOWLIST_CHARS + 1))
        self.assertEqual(NETWORK._load_allowed_targets(), frozenset())

    def test_missing_allowlist_denies_before_confirmation_or_network(self):
        with patch("builtins.input") as prompt, patch.object(NETWORK.subprocess, "run") as run:
            result = NETWORK.ping_host("192.168.56.10")
        self.assertEqual(result["error"], "TARGET_NOT_ALLOWLISTED")
        prompt.assert_not_called()
        run.assert_not_called()

    def test_confirmation_is_exact_and_target_bound(self):
        with patch("builtins.input", return_value="ALLOW PING 192.168.56.10 COUNT-1"):
            self.assertTrue(NETWORK._confirm("PING", "192.168.56.10", "COUNT-1"))
        with patch("builtins.input", return_value="ALLOW PING 192.168.56.11 COUNT-1"):
            self.assertFalse(NETWORK._confirm("PING", "192.168.56.10", "COUNT-1"))
        with patch("builtins.input", side_effect=EOFError):
            self.assertFalse(NETWORK._confirm("PING", "192.168.56.10", "COUNT-1"))

    def test_declined_confirmation_has_no_probe_or_executable_resolution(self):
        self.allow()
        with (
            patch("builtins.input", return_value="no"),
            patch.object(NETWORK, "_resolve_ping_binary") as resolve,
            patch.object(NETWORK.subprocess, "run") as run,
            patch.object(NETWORK, "log") as log,
        ):
            result = NETWORK.ping_host("192.168.56.10")
        self.assertEqual(result["error"], "CONFIRMATION_DENIED")
        resolve.assert_not_called()
        run.assert_not_called()
        log.assert_not_called()

    def test_noninteractive_confirmation_fails_closed(self):
        self.allow()
        with (
            patch("builtins.input", side_effect=EOFError),
            patch.object(NETWORK.subprocess, "run") as run,
        ):
            result = NETWORK.ping_host("192.168.56.10")
        self.assertEqual(result["error"], "CONFIRMATION_DENIED")
        run.assert_not_called()

    def test_non_allowlisted_target_is_denied_before_confirmation(self):
        self.allow("192.168.56.11")
        with patch("builtins.input") as prompt, patch.object(NETWORK.subprocess, "run") as run:
            result = NETWORK.ping_host("192.168.56.10")
        self.assertEqual(result["error"], "TARGET_NOT_ALLOWLISTED")
        prompt.assert_not_called()
        run.assert_not_called()

    def test_ping_count_is_bounded_before_confirmation(self):
        self.allow()
        with patch("builtins.input") as prompt, patch.object(NETWORK.subprocess, "run") as run:
            for count in (0, 4, -1, True, 1.5):
                result = NETWORK.ping_host("192.168.56.10", count=count)
                self.assertEqual(result["error"], "INVALID_COUNT")
        prompt.assert_not_called()
        run.assert_not_called()

    def test_confirmed_ping_uses_fixed_argv_shell_false_and_timeout(self):
        self.allow()
        output = (
            "64 bytes from 192.168.56.10: icmp_seq=1 ttl=64 time=0.2 ms\n"
            "1 packets transmitted, 1 received, 0% packet loss\n"
            "rtt min/avg/max/mdev = 0.2/0.2/0.2/0.0 ms\n"
        )
        completed = subprocess.CompletedProcess([], 0, output, "")
        with (
            patch("builtins.input", return_value="ALLOW PING 192.168.56.10 COUNT-1"),
            patch.object(NETWORK, "_resolve_ping_binary", return_value="/usr/bin/ping"),
            patch.object(NETWORK.subprocess, "run", return_value=completed) as run,
            patch.object(NETWORK, "log"),
        ):
            result = NETWORK.ping_host("192.168.56.10", count=1)
        self.assertEqual(result["status"], "REPLIED")
        self.assertEqual(result["packet_loss"], "0%")
        self.assertEqual(result["avg_latency"], "0.2 ms")
        args, kwargs = run.call_args
        self.assertEqual(args[0], [
            "/usr/bin/ping", "-n", "-c", "1", "-W", "2", "192.168.56.10",
        ])
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["timeout"], NETWORK.PING_TIMEOUT_SECONDS)
        self.assertIs(kwargs["check"], False)

    def test_unavailable_ping_binary_fails_closed(self):
        self.allow()
        with (
            patch("builtins.input", return_value="ALLOW PING 192.168.56.10 COUNT-1"),
            patch.object(NETWORK, "_resolve_ping_binary", return_value=None),
            patch.object(NETWORK.subprocess, "run") as run,
        ):
            result = NETWORK.ping_host("192.168.56.10")
        self.assertEqual(result["error"], "PING_UNAVAILABLE")
        run.assert_not_called()

    def test_rate_limiter_enforces_target_cooldown_and_window_quota(self):
        limiter = NETWORK.ProbeRateLimiter()
        self.assertTrue(limiter.acquire("192.168.56.10", now=0))
        self.assertFalse(limiter.acquire("192.168.56.10", now=5))
        self.assertTrue(limiter.acquire("192.168.56.10", now=10))
        self.assertTrue(limiter.acquire("192.168.56.10", now=20))
        self.assertFalse(limiter.acquire("192.168.56.10", now=30))

    def test_rate_limiter_enforces_global_quota(self):
        limiter = NETWORK.ProbeRateLimiter()
        for index in range(NETWORK.RATE_LIMITER._maximum_global):
            self.assertTrue(limiter.acquire(f"target-{index}", now=0))
        self.assertFalse(limiter.acquire("target-overflow", now=0))

    def test_speed_test_is_disabled_without_invoking_a_process(self):
        with patch.object(NETWORK.subprocess, "run") as run:
            result = NETWORK.speed_test()
        self.assertEqual(result["error"], "DISABLED_UNBOUNDED_PROVIDER_SELECTION")
        run.assert_not_called()

    def test_public_ip_decline_makes_no_http_request(self):
        with (
            patch("builtins.input", return_value="no"),
            patch.object(NETWORK, "build_opener") as build_opener,
        ):
            self.assertIsNone(NETWORK.get_public_ip())
        build_opener.assert_not_called()

    def test_public_ip_uses_only_fixed_https_host_after_exact_consent(self):
        class Response:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                return False
            def read(self, size):
                self.size = size
                return b"8.8.8.8"

        response = Response()
        opener = Mock()
        opener.open.return_value = response
        with (
            patch("builtins.input", return_value="ALLOW PUBLIC-IP api.ipify.org HTTPS-GET"),
            patch.object(NETWORK, "build_opener", return_value=opener) as build_opener,
            patch.object(NETWORK, "log"),
        ):
            self.assertEqual(NETWORK.get_public_ip(), "8.8.8.8")
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, NETWORK.PUBLIC_IP_URL)
        self.assertEqual(opener.open.call_args.kwargs["timeout"], NETWORK.PUBLIC_IP_TIMEOUT_SECONDS)
        self.assertEqual(response.size, NETWORK.MAX_PUBLIC_IP_RESPONSE_BYTES + 1)
        proxy_handler = build_opener.call_args.args[0]
        self.assertEqual(proxy_handler.proxies, {})
        self.assertIsInstance(build_opener.call_args.args[2], NETWORK._NoRedirectHandler)

    def test_public_ip_response_is_bounded_and_validated(self):
        class Response:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                return False
            def read(self, _size):
                return b"8.8.8.8" * 8

        opener = Mock()
        opener.open.return_value = Response()
        with (
            patch("builtins.input", return_value="ALLOW PUBLIC-IP api.ipify.org HTTPS-GET"),
            patch.object(NETWORK, "build_opener", return_value=opener),
        ):
            self.assertIsNone(NETWORK.get_public_ip())

    def test_redirect_handler_refuses_second_destination(self):
        handler = NETWORK._NoRedirectHandler()
        request = NETWORK.Request(NETWORK.PUBLIC_IP_URL)
        self.assertIsNone(handler.redirect_request(request, None, 302, "Found", {}, "https://other.example/"))

    def test_monitor_requires_allowlist_and_bounded_parameters(self):
        self.allow()
        with patch.object(NETWORK, "ping_host") as ping:
            self.assertEqual(
                NETWORK.monitor_connectivity("192.168.56.10", duration=301)["error"],
                "INVALID_DURATION",
            )
            self.assertEqual(
                NETWORK.monitor_connectivity("192.168.56.10", duration=60, interval=5)["error"],
                "INVALID_INTERVAL",
            )
            self.assertEqual(
                NETWORK.monitor_connectivity("192.168.56.10", duration=300, interval=10)["error"],
                "INVALID_INTERVAL",
            )
        ping.assert_not_called()

    def test_monitor_requires_a_fresh_ping_confirmation_for_each_probe(self):
        self.allow()
        results = [
            {"host": "192.168.56.10", "status": "REPLIED"},
            {"host": "192.168.56.10", "error": "CONFIRMATION_DENIED"},
        ]
        with (
            patch.object(NETWORK, "ping_host", side_effect=results) as ping,
            patch.object(NETWORK.time, "sleep"),
        ):
            report = NETWORK.monitor_connectivity("192.168.56.10", duration=60, interval=30)
        self.assertEqual(report["status"], "STOPPED")
        self.assertEqual(len(report["results"]), 2)
        self.assertEqual(ping.call_args_list[0].args, ("192.168.56.10",))
        self.assertEqual(ping.call_args_list[1].args, ("192.168.56.10",))

    def test_local_ip_uses_interface_ioctl_without_network_send(self):
        fake_socket = Mock()
        fake_socket.fileno.return_value = 7
        address_bytes = b"\x00" * 20 + socket.inet_aton("192.168.56.10") + b"\x00" * 8
        with (
            patch.object(NETWORK.socket, "if_nameindex", return_value=[(1, "lo"), (2, "wlan0")]),
            patch.object(NETWORK.socket, "socket", return_value=fake_socket) as create_socket,
            patch("fcntl.ioctl", return_value=address_bytes) as ioctl,
        ):
            self.assertEqual(NETWORK.get_local_ip(), "192.168.56.10")
        create_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_DGRAM)
        ioctl.assert_called_once()
        fake_socket.connect.assert_not_called()
        fake_socket.send.assert_not_called()
        fake_socket.close.assert_called_once()

    def test_source_has_no_legacy_unbounded_network_helpers(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("8.8.8.8", source)
        self.assertNotIn("speedtest-cli", source)
        self.assertNotIn('"curl"', source)
        self.assertNotIn("shell=True", source)
        self.assertNotIn("confirm=None", source)
        self.assertIn("MRNOTHING_NETWORK_ALLOWED_TARGETS", source)
        self.assertIn("ProxyHandler({})", source)
        self.assertIn("per-probe", source.lower())


if __name__ == "__main__":
    unittest.main()
