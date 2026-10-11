#!/usr/bin/env python3
"""Validate independent workspaces and build a deterministic, static catalog."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil

import yaml

ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
REF = re.compile(r"^(?:([A-Za-z0-9_-]+)\.yaml)?#/(dataset|sources/([A-Za-z0-9_-]+))$")
CONNECTION = re.compile(r"\{\{\s*connections\.([A-Za-z0-9_-]+)\.[A-Za-z0-9_-]+\s*\}\}")
MAX_FILE = 20 * 1024 * 1024


def relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Invalid workspace-relative path")
    parts = value.split("/")
    if any(not part or part.startswith(".") or ":" in part for part in parts):
        raise ValueError(f"Path escapes the workspace or is hidden: {value}")
    return PurePosixPath(value)


def read_file(root, path):
    relative_path(path)
    target = root / path
    current = root
    for part in relative_path(path).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symbolic links are not publishable: {path}")
    if not target.is_file() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Missing file in workspace: {path}")
    data = target.read_bytes()
    if len(data) > MAX_FILE:
        raise ValueError(f"File exceeds the CDN size limit: {path}")
    return data


def file_record(root, path):
    data = read_file(root, path)
    return {"path": path, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def build_workspace(root):
    if root.is_symlink():
        raise ValueError("Workspace directories cannot be symbolic links")
    topic = root.name
    if not ID.fullmatch(topic):
        raise ValueError(f"Invalid workspace directory: {topic}")
    manifest = json.loads(read_file(root, "workspace.json"))
    if not ID.fullmatch(manifest.get("id", "")) or manifest.get("kind") != "localPath":
        raise ValueError(f"{topic}: workspace.json must define a portable localPath workspace")
    title = manifest.get("title", "").strip()
    if not title:
        raise ValueError(f"{topic}: workspace title is required")
    metadata = yaml.safe_load(read_file(root, "discover.yaml")) if (root / "discover.yaml").exists() else {}
    metadata = metadata or {}
    tags = metadata.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise ValueError(f"{topic}: tags must be strings")
    resources, charts, ids = [], {}, set()
    for kind, directory in [("chart", "charts"), ("dashboard", "dashboards")]:
        folder = root / directory
        if folder.is_symlink():
            raise ValueError(f"{topic}: resource directories cannot be symbolic links")
        for path in sorted(folder.rglob("*.yaml")):
            relative = path.relative_to(root).as_posix()
            document = yaml.safe_load(read_file(root, relative))
            if not isinstance(document, dict):
                raise ValueError(f"{topic}/{relative}: YAML must be an object")
            header = document.get("chart", {}) if kind == "chart" else document
            if kind == "dashboard" and document.get("kind") != "Dashboard":
                raise ValueError(f"{topic}/{relative}: expected a Dashboard")
            resource_id = header.get("id", "")
            if not ID.fullmatch(resource_id) or resource_id.startswith("builtin_example_") or path.stem != resource_id:
                raise ValueError(f"{topic}/{relative}: invalid ID or mismatched filename")
            if resource_id in ids:
                raise ValueError(f"{topic}: duplicate resource ID {resource_id}")
            ids.add(resource_id)
            if not header.get("title", "").strip():
                raise ValueError(f"{topic}/{relative}: title is required")
            item = {"id": f"{topic}/{kind}/{resource_id}", "resourceID": resource_id, "type": kind,
                    "title": header["title"], "description": header.get("notes", ""), "path": relative,
                    "tags": tags, "document": document}
            if kind == "chart":
                item["chartType"] = header.get("plot", header.get("renderer", "chart"))
                charts[resource_id] = item
            preview = f"previews/{resource_id}.png"
            if (root / preview).exists():
                item["preview"] = file_record(root, preview)
            resources.append(item)

    dependencies, assets, connections, kinds = {}, {}, {}, {}
    for resource_id, item in charts.items():
        dependencies[resource_id], assets[resource_id] = set(), set()
        connections[resource_id], kinds[resource_id] = set(), set()
        for key, value in walk(item["document"]):
            if key == "ref":
                match = REF.fullmatch(value) if isinstance(value, str) else None
                if not match:
                    raise ValueError(f"{topic}/{item['path']}: ref must stay inside this workspace")
                target_id = match[1] or resource_id
                if target_id not in charts:
                    raise ValueError(f"{topic}/{item['path']}: missing local chart {target_id}")
                target = charts[target_id]["document"]
                if (match[3] and match[3] not in target.get("sources", {})) or (not match[3] and "dataset" not in target):
                    raise ValueError(f"{topic}/{item['path']}: missing reference target")
                if target_id != resource_id:
                    dependencies[resource_id].add(target_id)
            if key == "source" and isinstance(value, str):
                kinds[resource_id].add(value)
            if key == "file":
                path = str(relative_path(value))
                if not path.startswith("data/"):
                    raise ValueError(f"{topic}: data files must be in this workspace's data/")
                read_file(root, path)
                assets[resource_id].add(path)
            if key == "file_path":
                path = "data/" + str(relative_path(value))
                read_file(root, path)
                assets[resource_id].add(path)
            if key == "connection" and isinstance(value, str):
                if not ID.fullmatch(value):
                    raise ValueError(f"{topic}: invalid connection reference")
                connections[resource_id].add(value)
            if isinstance(value, str):
                connections[resource_id].update(CONNECTION.findall(value))

    def closure(resource_id, visiting=None):
        visiting = set() if visiting is None else visiting
        if resource_id in visiting:
            raise ValueError(f"{topic}: cyclic chart dependency involving {resource_id}")
        result = {resource_id}
        for dependency in dependencies[resource_id]:
            result.update(closure(dependency, visiting | {resource_id}))
        return result

    required = set(manifest.get("requiredConnections", []))
    if not all(isinstance(value, str) and ID.fullmatch(value) for value in required):
        raise ValueError(f"{topic}: invalid requiredConnections")
    for item in resources:
        document = item.pop("document")
        if item["type"] == "chart":
            selected = closure(item["resourceID"])
        else:
            selected = set()
            for tab in document.get("tabs", []):
                for panel in tab.get("panels", []):
                    chart = panel.get("chart")
                    if chart not in charts:
                        raise ValueError(f"{topic}/{item['path']}: dashboard references a chart outside this workspace")
                    selected.update(closure(chart))
        paths = {item["path"]}
        source_kinds, resource_connections = set(), set()
        for chart in selected:
            paths.add(charts[chart]["path"])
            paths.update(assets[chart])
            source_kinds.update(kinds[chart])
            resource_connections.update(connections[chart])
        item["files"] = sorted(paths)
        item["sourceKinds"] = sorted(source_kinds)
        item["requiredConnections"] = sorted(resource_connections)
        required.update(resource_connections)

    paths = {"workspace.json"} | {item["path"] for item in resources}
    data_root = root / "data"
    if data_root.is_symlink():
        raise ValueError(f"{topic}: data/ cannot be a symbolic link")
    paths.update(path.relative_to(root).as_posix() for path in data_root.rglob("*") if path.is_file() or path.is_symlink())
    files = [file_record(root, path) for path in sorted(paths)]
    if sum(file["size"] for file in files) > 100 * 1024 * 1024:
        raise ValueError(f"{topic}: workspace exceeds the 100 MB installation limit")
    result = {"id": topic, "title": title, "description": metadata.get("description", ""), "tags": tags,
              "license": metadata.get("license", "Apache-2.0"), "requiredConnections": sorted(required),
              "files": files, "resources": resources}
    if (root / "previews/workspace.png").exists():
        result["preview"] = file_record(root, "previews/workspace.png")
    return result


def build_catalog(root, revision):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("sourceRevision must be a complete Git commit SHA")
    workspaces = [build_workspace(path) for path in sorted(root.iterdir())
                  if path.is_dir() and not path.name.startswith(".") and (path / "workspace.json").exists()]
    if not workspaces:
        raise ValueError("No publishable workspaces found")
    return {"schemaVersion": 1, "sourceRevision": revision, "workspaces": workspaces}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    catalog = build_catalog(args.root.resolve(), args.revision)
    args.output.mkdir(parents=True, exist_ok=True)
    data = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    (args.output / "discover.json").write_text(data, encoding="utf-8")
    shutil.copyfile(args.root / "LICENSE", args.output / "LICENSE")
    print(f"Catalog: {len(catalog['workspaces'])} workspaces, {len(data.encode())} bytes, revision {args.revision}")


if __name__ == "__main__":
    main()
