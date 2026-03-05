from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "yc_mcp_catalog.py"
MANIFEST_PATH = REPO_ROOT / "references" / "contracts" / "skill_manifest.yaml"
MANIFEST_SCHEMA_PATH = REPO_ROOT / "references" / "contracts" / "skill_manifest.schema.json"
MCP_CATALOG_PATH = REPO_ROOT / "references" / "mcp" / "catalog.yaml"
MCP_CATALOG_SCHEMA_PATH = REPO_ROOT / "references" / "contracts" / "mcp_catalog.schema.json"


def load_module():
    spec = importlib.util.spec_from_file_location("yc_mcp_catalog", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load yc_mcp_catalog module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CatalogCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_module()

    def base_args(self, **overrides: object) -> argparse.Namespace:
        values: dict[str, object] = {
            "manifest": str(MANIFEST_PATH),
            "manifest_schema": str(MANIFEST_SCHEMA_PATH),
            "mcp_catalog": str(MCP_CATALOG_PATH),
            "mcp_catalog_schema": str(MCP_CATALOG_SCHEMA_PATH),
            "registry": str(REPO_ROOT / "references" / "mcp" / "registry.md"),
            "navigation": str(REPO_ROOT / "references" / "navigation.md"),
            "codex_setup": str(REPO_ROOT / "references" / "mcp" / "codex-setup.md"),
            "offline": False,
            "name": "",
            "task_type": "",
            "service": "",
            "intent": "",
            "operation": "",
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def assert_envelope(self, payload: dict) -> None:
        self.assertEqual(payload.get("version"), "2.0")
        self.assertIn("status", payload)
        self.assertIn("data", payload)
        self.assertIn("checks", payload)
        self.assertIn("limitations", payload)
        self.assertIn("sources", payload)
        self.assertIn("errors", payload)

    def test_validate_contracts_envelope(self) -> None:
        payload, code = self.mod._cmd_validate_contracts(self.base_args())
        self.assertEqual(code, 0)
        self.assert_envelope(payload)
        self.assertEqual(payload["status"], "ok")

    def test_invalid_manifest_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bad_manifest = Path(td) / "bad_manifest.yaml"
            bad_manifest.write_text("version: 1\n", encoding="utf-8")

            args = self.base_args(manifest=str(bad_manifest))
            payload, code = self.mod._cmd_validate_contracts(args)

            self.assertEqual(code, 1)
            self.assert_envelope(payload)
            self.assertEqual(payload["status"], "error")
            error_codes = [item["code"] for item in payload["errors"]]
            self.assertIn("contract_manifest_invalid", error_codes)

    def test_invalid_catalog_not_written_in_offline_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bad_catalog = Path(td) / "catalog.yaml"
            bad_catalog.write_text(
                "version: 1\nsource_repo: https://github.com/yandex-cloud/mcp\n",
                encoding="utf-8",
            )
            before = bad_catalog.read_text(encoding="utf-8")

            args = self.base_args(mcp_catalog=str(bad_catalog), offline=True)
            payload, code = self.mod._cmd_refresh_mcp_catalog(args)

            self.assertEqual(code, 1)
            self.assert_envelope(payload)
            self.assertEqual(payload["status"], "error")
            after = bad_catalog.read_text(encoding="utf-8")
            self.assertEqual(before, after)

    def test_resolve_no_match_returns_non_mcp_fallback(self) -> None:
        args = self.base_args(
            task_type="auth",
            service="billing",
            intent="no-such-intent",
            operation="",
        )
        payload, code = self.mod._cmd_resolve_mcp(args)

        self.assertEqual(code, 0)
        self.assert_envelope(payload)
        self.assertEqual(payload["status"], "mcp_unavailable")
        self.assertIn("non_mcp_fallback", payload["data"])

    def test_toolkit_operation_filtering_is_deterministic(self) -> None:
        args = self.base_args(
            task_type="mcp_setup",
            service="compute",
            intent="toolkit",
            operation="unsupported_operation",
        )
        payload, code = self.mod._cmd_resolve_mcp(args)

        self.assertEqual(code, 0)
        self.assert_envelope(payload)
        self.assertEqual(payload["status"], "mcp_unavailable")

    def test_mcp_json_parsing_helpers(self) -> None:
        with mock.patch.object(
            self.mod,
            "_run_cmd",
            return_value=(json.dumps([{"name": "toolkit-mcp-server"}]), "", 0),
        ):
            items, raw = self.mod._mcp_list_json()
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["name"], "toolkit-mcp-server")
            self.assertIn("stdout", raw)

        with mock.patch.object(
            self.mod,
            "_run_cmd",
            return_value=(json.dumps({"name": "toolkit-mcp-server"}), "", 0),
        ):
            item, _raw = self.mod._mcp_get_json("toolkit-mcp-server")
            self.assertEqual(item["name"], "toolkit-mcp-server")

        with mock.patch.object(self.mod, "_run_cmd", return_value=("", "boom", 1)):
            with self.assertRaises(RuntimeError):
                self.mod._mcp_list_json()

        with mock.patch.object(
            self.mod,
            "_run_cmd",
            return_value=("", "Permission denied: token rejected", 1),
        ):
            with self.assertRaises(RuntimeError):
                self.mod._mcp_list_json()

    def test_plan_missing_env_is_warning_not_permission_denied(self) -> None:
        args = self.base_args(
            task_type="mcp_setup",
            service="resource-manager",
            intent="docs",
        )
        with mock.patch.object(
            self.mod,
            "_mcp_list_json",
            return_value=([], {"stdout": "[]", "stderr": ""}),
        ):
            with mock.patch.dict(os.environ, {"YC_IAM_TOKEN": ""}, clear=False):
                payload, code = self.mod._cmd_plan_mcp_install(args)

        self.assertEqual(code, 0)
        self.assert_envelope(payload)
        self.assertEqual(payload["status"], "needs_install")
        self.assertEqual(payload["data"]["status"], "needs_install")
        self.assertIn("YC_IAM_TOKEN", payload["data"]["auth_env"]["missing_env"])
        self.assertFalse(payload["data"]["auth_env"]["ready"])
        self.assertEqual(payload["errors"], [])

    def test_report_missing_env_is_warning_not_permission_denied(self) -> None:
        args = self.base_args(
            task_type="mcp_setup",
            service="resource-manager",
            intent="docs",
        )
        with mock.patch.object(
            self.mod,
            "_mcp_list_json",
            return_value=([], {"stdout": "[]", "stderr": ""}),
        ):
            with mock.patch.dict(os.environ, {"YC_IAM_TOKEN": ""}, clear=False):
                payload, code = self.mod._cmd_report_mcp_install(args)

        self.assertEqual(code, 0)
        self.assert_envelope(payload)
        self.assertEqual(payload["status"], "not_installed")
        self.assertEqual(payload["data"]["status"], "not_installed")
        self.assertIn("YC_IAM_TOKEN", payload["data"]["auth_env"]["missing_env"])
        self.assertFalse(payload["data"]["auth_env"]["ready"])
        self.assertEqual(payload["errors"], [])

    def test_docs_render_is_deterministic(self) -> None:
        manifest, manifest_errors = self.mod._load_manifest(MANIFEST_PATH, MANIFEST_SCHEMA_PATH)
        catalog, catalog_errors = self.mod._load_catalog(MCP_CATALOG_PATH, MCP_CATALOG_SCHEMA_PATH)
        self.assertFalse(manifest_errors)
        self.assertFalse(catalog_errors)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            routing: dict[str, str] = {}
            for task_type in manifest["routing"]["task_workflow"]:
                routing[task_type] = str(root / "workflows" / f"{task_type}.md")
            manifest["routing"]["task_workflow"] = routing

            profiles: dict[str, str] = {}
            for language in manifest["languages"]["profiles"]:
                profiles[language] = str(root / "languages" / f"{language}.md")
            manifest["languages"]["profiles"] = profiles

            navigation = root / "navigation.md"
            registry = root / "registry.md"
            codex_setup = root / "codex-setup.md"

            first_written = self.mod._render_files(
                manifest=manifest,
                manifest_path=MANIFEST_PATH,
                catalog=catalog,
                catalog_path=MCP_CATALOG_PATH,
                navigation_path=navigation,
                registry_path=registry,
                codex_setup_path=codex_setup,
            )
            first_snapshot = {
                path: Path(path).read_text(encoding="utf-8") for path in sorted(first_written)
            }

            second_written = self.mod._render_files(
                manifest=manifest,
                manifest_path=MANIFEST_PATH,
                catalog=catalog,
                catalog_path=MCP_CATALOG_PATH,
                navigation_path=navigation,
                registry_path=registry,
                codex_setup_path=codex_setup,
            )
            second_snapshot = {
                path: Path(path).read_text(encoding="utf-8") for path in sorted(second_written)
            }

            self.assertEqual(first_snapshot, second_snapshot)

    def test_integration_smoke_refresh_resolve_plan(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            copied_catalog = root / "catalog.yaml"
            copied_catalog.write_text(MCP_CATALOG_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            registry = root / "registry.md"

            refresh_args = self.base_args(
                mcp_catalog=str(copied_catalog),
                registry=str(registry),
                offline=True,
            )
            refresh_payload, refresh_code = self.mod._cmd_refresh_mcp_catalog(refresh_args)
            self.assertEqual(refresh_code, 0)
            self.assertEqual(refresh_payload["status"], "offline_used_cache")

            resolve_args = self.base_args(
                mcp_catalog=str(copied_catalog),
                task_type="mcp_setup",
                service="resource-manager",
                intent="docs",
            )
            resolve_payload, resolve_code = self.mod._cmd_resolve_mcp(resolve_args)
            self.assertEqual(resolve_code, 0)
            self.assertIn(resolve_payload["status"], {"ok", "mcp_unavailable"})

            with mock.patch.object(
                self.mod,
                "_mcp_list_json",
                return_value=([], {"stdout": "[]", "stderr": ""}),
            ):
                with mock.patch.dict(os.environ, {"YC_IAM_TOKEN": "test-token"}, clear=False):
                    plan_args = self.base_args(
                        mcp_catalog=str(copied_catalog),
                        task_type="mcp_setup",
                        service="resource-manager",
                        intent="docs",
                    )
                    plan_payload, plan_code = self.mod._cmd_plan_mcp_install(plan_args)
                    self.assertEqual(plan_code, 0)
                    self.assertIn(
                        plan_payload["status"],
                        {"needs_install", "already_installed", "mcp_unavailable"},
                    )


if __name__ == "__main__":
    unittest.main()
