"""Offline validation of portable Facetra documents; never executes sources or SQL."""
import math
import unicodedata
from datetime import datetime
import re
from urllib.parse import urlsplit

import yaml

try:
    from . import http_collection
except ImportError:
    import http_collection

ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
REF = re.compile(r"^(?:([A-Za-z0-9_-]{1,80})\.yaml)?#/(dataset|sources/([A-Za-z0-9_-]{1,80}))$")


class DocumentLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        # Flatten merge keys as the application does, then reject ambiguous keys.
        self.flatten_mapping(node)
        keys = set()
        for key, _ in node.value:
            value = self.construct_object(key, deep=deep)
            if not isinstance(value, str):
                raise ValueError(f"line {key.start_mark.line + 1}: mapping keys must be strings")
            if value in keys:
                raise ValueError(f"line {key.start_mark.line + 1}: duplicate YAML key {value}")
            keys.add(value)
        return super().construct_mapping(node, deep=deep)


# Exported application YAML uses numbers such as 2.4e+2 and 1e+0.
# SafeLoader otherwise treats the second form as a string.
DocumentLoader.add_implicit_resolver(
    "tag:yaml.org,2002:float", re.compile(r"^[-+]?[0-9]+(?:\.[0-9]*)?[eE][-+]?[0-9]+$"), list("-+0123456789")
)


def load_yaml(data, context):
    try:
        return yaml.load(data, Loader=DocumentLoader)
    except (ValueError, yaml.YAMLError, RecursionError) as error:
        raise ValueError(f"{context}: {error}") from error


def require(condition, context, message):
    if not condition:
        raise ValueError(f"{context}: {message}")


def mapping(value, context, allowed=None, required=()):
    require(isinstance(value, dict) and all(isinstance(key, str) for key in value), context, "expected an object with string keys")
    if allowed is not None:
        require(not set(value) - set(allowed), context, f"unsupported fields: {sorted(set(value) - set(allowed))}")
    require(set(required) <= set(value), context, f"missing fields: {sorted(set(required) - set(value))}")
    return value


def sequence(value, context, minimum=0, maximum=None):
    require(isinstance(value, list), context, "expected a list")
    require(len(value) >= minimum and (maximum is None or len(value) <= maximum), context, "invalid list length")
    return value


def text(value, context, nonempty=True):
    require(isinstance(value, str) and (not nonempty or bool(value.strip())), context, "expected a nonempty string" if nonempty else "expected a string")
    return value


MESSAGE_KEY = re.compile(r"^[A-Za-z0-9_.-]{1,120}$")
LOCALE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")


def localized_text(value, context, nonempty=True):
    """Check display text shape; resource-local reference checks run separately."""
    if isinstance(value, dict):
        mapping(value, context, {"i18n"}, {"i18n"})
        require(isinstance(value["i18n"], str) and MESSAGE_KEY.fullmatch(value["i18n"]), context, "invalid i18n message key")
    else:
        text(value, context, nonempty=nonempty)


def validate_localization(document, context):
    catalog = document.get("i18n")
    messages = {}
    if catalog is not None:
        mapping(catalog, context + ".i18n", {"defaultLocale", "messages"}, {"defaultLocale", "messages"})
        default = text(catalog["defaultLocale"], context + ".i18n.defaultLocale")
        require(LOCALE.fullmatch(default), context + ".i18n.defaultLocale", "invalid locale tag")
        messages = mapping(catalog["messages"], context + ".i18n.messages")
        for key, translations in messages.items():
            location = context + ".i18n.messages." + key
            require(MESSAGE_KEY.fullmatch(key), location, "invalid i18n message key")
            mapping(translations, location)
            seen = set()
            for language, translation in translations.items():
                require(LOCALE.fullmatch(language), location, "invalid locale tag")
                require(language.lower() not in seen, location, "duplicate locale tag ignoring case")
                seen.add(language.lower())
                text(translation, location + "." + language)
            require(default.lower() in seen, location, "missing defaultLocale translation")

    def reference(value, location):
        if isinstance(value, dict):
            localized_text(value, location)
            require(value["i18n"] in messages, location, "missing resource-local i18n message")

    metadata = document.get("metadata")
    if isinstance(metadata, dict):
        for field in ("title", "notes"):
            reference(metadata.get(field), context + ".metadata." + field)
    definitions = document.get("params", [])
    for index, parameter in enumerate(definitions if isinstance(definitions, list) else []):
        if isinstance(parameter, dict):
            reference(parameter.get("label"), f"{context}.params[{index}].label")
    tabs = document.get("tabs", [])
    for index, tab in enumerate(tabs if isinstance(tabs, list) else []):
        if isinstance(tab, dict):
            reference(tab.get("title"), f"{context}.tabs[{index}].title")

    def option(value, location, depth=0):
        require(depth < 64, location, "option is too deeply nested")
        if isinstance(value, dict):
            if "i18n" in value:
                reference(value, location)
            elif "from" not in value:
                for key, child in value.items():
                    option(child, location + "." + key, depth + 1)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                option(child, f"{location}[{index}]", depth + 1)

    chart = document.get("chart")
    if isinstance(chart, dict):
        option(chart.get("option"), context + ".chart.option")


def resolve_text(value, document, locale=None):
    """Catalog metadata stays a string; downloadable YAML retains every locale."""
    if isinstance(value, str):
        return value
    catalog = document["i18n"]
    translations = catalog["messages"][value["i18n"]]
    candidate = (locale or "").lower()
    while candidate:
        for language, translation in translations.items():
            if language.lower() == candidate:
                return translation
        candidate = candidate.rsplit("-", 1)[0] if "-" in candidate else ""
    return next(text for locale, text in translations.items() if locale.lower() == catalog["defaultLocale"].lower())


def identifier(value, context):
    require(isinstance(value, str) and ID.fullmatch(value), context, "IDs must contain 1–80 letters, digits, underscores or hyphens")
    return value


def number(value, context, low=None, high=None, integer=False):
    try:
        finite = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        finite = False
    require(finite, context, "expected a finite number")
    require(not integer or int(value) == value, context, "expected an integer")
    require((low is None or low <= value) and (high is None or value <= high), context, f"number must be between {low} and {high}")
    return value


def scalar(value, context):
    require(type(value) in (str, int, float, bool), context, "expected a string, number or boolean")
    if type(value) in (int, float):
        number(value, context)


def unique(values, context):
    require(len(set(values)) == len(values), context, "IDs must be unique")


def parameter_value(parameter, value, context):
    scalar(value, context)
    kind = parameter["type"]
    matches = {"string": isinstance(value, str), "date": isinstance(value, str), "boolean": type(value) is bool,
               "integer": type(value) in (int, float) and int(value) == value,
               "number": type(value) in (int, float)}
    require(matches[kind], context, f"expected parameter type {kind}")
    if isinstance(value, str) and parameter.get("required", True):
        text(value, context)
    if parameter["type"] == "date" and (value != "" or parameter.get("required", True)):
        pattern = "%Y-%m-%d"
        try:
            valid = datetime.strptime(value, pattern).strftime(pattern) == value
        except ValueError:
            valid = False
        require(valid, context, "expected a valid ISO calendar date (YYYY-MM-DD)")
    if type(value) in (int, float):
        number(value, context, parameter.get("minimum"), parameter.get("maximum"))
    if parameter.get("options") is not None:
        require(value in parameter["options"], context, "value is outside parameter options")


def parameters(values, context):
    result = {}
    for index, parameter in enumerate(sequence(values, context)):
        location = f"{context}[{index}]"
        mapping(parameter, location, {"name", "label", "type", "default", "required", "minimum", "maximum", "options", "advanced"}, {"name", "type"})
        name = identifier(parameter["name"], location + ".name")
        require(name not in result, location, "duplicate parameter name")
        require(parameter["type"] in ("string", "integer", "number", "boolean", "date"), location, "unsupported parameter type")
        if parameter["type"] == "date":
            require(all(parameter.get(field) is None for field in ("minimum", "maximum")),
                    location, "date parameters cannot have numeric bounds")
        if "label" in parameter:
            localized_text(parameter["label"], location + ".label")
        for field in ("required", "advanced"):
            if field in parameter:
                require(type(parameter[field]) is bool, location + "." + field, "expected a boolean")
        for field in ("minimum", "maximum"):
            if parameter.get(field) is not None:
                number(parameter[field], location + "." + field)
        if parameter.get("minimum") is not None and parameter.get("maximum") is not None:
            require(parameter["minimum"] <= parameter["maximum"], location, "minimum exceeds maximum")
        if parameter.get("options") is not None:
            for value in sequence(parameter["options"], location + ".options"):
                parameter_value(parameter, value, location + ".options")
        if parameter.get("default") is not None:
            parameter_value(parameter, parameter["default"], location + ".default")
        result[name] = parameter
    return result


def bindings(value, context):
    for name, binding in mapping(value, context).items():
        identifier(name, context + "." + name)
        if isinstance(binding, dict):
            mapping(binding, context, {"param"}, {"param"})
            identifier(binding["param"], context + ".param")
        else:
            scalar(binding, context + "." + name)


def validate_bindings(value, caller, target, context, inherit=False):
    bindings(value, context)
    for name, binding in value.items():
        require(name in target, context, f"unknown target parameter {name}")
        if isinstance(binding, dict):
            source = binding["param"]
            require(source in caller, context, f"unknown caller parameter {source}")
            require(caller[source]["type"] == target[name]["type"], context, f"parameter type mismatch for {name}")
            if caller[source].get("default") is not None:
                parameter_value(target[name], caller[source]["default"], context + "." + name)
        else:
            parameter_value(target[name], binding, context + "." + name)
    for name, parameter in target.items():
        require(not parameter.get("required", True) or parameter.get("default") is not None or name in value or (inherit and name in caller), context, f"missing required target parameter {name}")


def validate_connection_type(document, context):
    mapping(document, context, {"name", "notes", "fields"}, {"fields"})
    for field in ("name", "notes"):
        if document.get(field) is not None:
            text(document[field], context + "." + field, nonempty=field == "name")
    keys = []
    for index, field in enumerate(sequence(document["fields"], context + ".fields")):
        location = f"{context}.fields[{index}]"
        mapping(field, location, {"key"}, {"key"})
        keys.append(identifier(field["key"], location + ".key"))
    unique(keys, context + ".fields")


def validate_workspace(document, context, *, legacy=False):
    fields = {"title", "description", "license", "requiredConnections"}
    if legacy:
        fields.update({"id", "kind", "isPersonal"})
    mapping(document, context, fields, {"title"})
    text(document["title"], context + ".title")
    if legacy and "id" in document:
        identifier(document["id"], context + ".id")
    if legacy and "kind" in document:
        require(document["kind"] == "localPath", context, "published workspaces require kind: localPath")
    for field in ("description", "license"):
        if document.get(field) is not None:
            text(document[field], context + "." + field, nonempty=False)
    if legacy and "isPersonal" in document:
        require(type(document["isPersonal"]) is bool, context, "isPersonal must be boolean")
    connections = sequence(document.get("requiredConnections", []), context + ".requiredConnections")
    for connection in connections:
        mapping(connection, context + ".requiredConnections", {"alias", "type"}, {"alias"})
        identifier(connection["alias"], context + ".requiredConnections.alias")
        identifier(connection.get("type", "key-value"), context + ".requiredConnections.type")
    unique([connection["alias"] for connection in connections], context + ".requiredConnections")


def reference(value, context, kind):
    match = REF.fullmatch(value) if isinstance(value, str) else None
    require(match is not None, context, "ref must stay inside this workspace")
    require((match[3] is not None) == (kind == "source"), context, f"expected a {kind} reference")
    return match


def source(value, context):
    common = {"source", "display", "depends_on"}
    if "ref" in value:
        mapping(value, context, {"ref", "with", "display"}, {"ref"})
        reference(value["ref"], context, "source")
        bindings(value.get("with", {}), context + ".with")
    else:
        kind = value.get("source")
        fields = {"duckdb": {"file"}, "http": {"url", "method", "headers", "params", "json", "data", "format", "recordsPath", "pagination", "foreach", "extract", "limits", "retry"},
                  "database": {"connection", "sql"}, "sqlite": {"file_path", "sql"}}
        require(isinstance(kind, str) and kind in fields, context, "source must be duckdb, http, database or sqlite")
        mapping(value, context, common | fields[kind], {"source"})
        for field in {"duckdb": ["file"], "http": ["url"], "database": ["connection", "sql"], "sqlite": ["file_path", "sql"]}[kind]:
            text(value.get(field), context + "." + field)
        dependencies = value.get("depends_on") or []
        sequence(dependencies, context+".depends_on", maximum=32)
        for dependency in dependencies: identifier(dependency, context+".depends_on")
        unique(dependencies, context+".depends_on")
        if kind == "database":
            identifier(value["connection"], context + ".connection")
        if kind == "http":
            method = text(value.get("method", "get"), context + ".method").lower()
            require(method in ("get", "post"), context, "HTTP supports get and post")
            require(not ("json" in value and "data" in value), context, "use either json or data")
            require(method != "get" or not {"json", "data"} & value.keys(), context, "GET cannot have a body")
            require(value.get("format", "json") in ("json", "csv", "html", "xml"), context, "invalid HTTP format")
            if "recordsPath" in value:
                require(value.get("format", "json") == "json", context, "recordsPath requires JSON")
                for part in sequence(value["recordsPath"], context + ".recordsPath"):
                    text(part, context + ".recordsPath")
            for field in ("headers", "params", "data"):
                if field in value:
                    for child in mapping(value[field], context + "." + field).values():
                        if field == "headers":
                            text(child, context + ".headers", nonempty=False)
                        else:
                            scalar(child, context + "." + field)
            if "json" in value:
                json_value(value["json"], context + ".json")
            http_collection.validate(value, context, (mapping, text, number, identifier, require, json_value))
            if "{{" not in value["url"]:
                url = urlsplit(value["url"])
                require(url.scheme == "https" and url.hostname and not url.username and not url.password and not url.fragment, context, "HTTP requires HTTPS without user info or fragment")
    if "display" in value:
        require(value["display"] in ("df", "json", "text"), context, "display must be df, json or text")


def json_value(value, context, depth=0):
    require(depth < 64, context, "JSON body is too deeply nested or contains a recursive alias")
    if isinstance(value, dict):
        for child in mapping(value, context).values():
            json_value(child, context, depth + 1)
    elif isinstance(value, list):
        for child in value:
            json_value(child, context, depth + 1)
    elif value is not None:
        scalar(value, context)


def echarts_option(value, chart, params, context, depth=0):
    require(depth < 64, context, "ECharts option is too deeply nested")
    if isinstance(value, dict) and "i18n" in value:
        localized_text(value, context)
    elif isinstance(value, dict) and "from" in value and (chart.get("renderer", "echarts") == "echarts" or isinstance(value["from"], str)):
        origin = value["from"]
        if origin == "script":
            require(chart.get("renderer", "echarts") == "echarts", context, "script bindings require ECharts")
        if origin in ("params", "script"):
            mapping(value, context, {"from", "name"}, {"name"})
            name = text(value["name"], context + ".name")
            require(name in (params if origin == "params" else chart.get("scripts", {})), context, f"unknown {origin} binding {name}")
        else:
            mapping(value, context, {"from", "field", "fields", "x", "y", "rows", "color_by_sign", "color_by"})
            require(origin == chart["dataset"], context, "binding must reference chart.dataset")
            modes = ["field" in value, "fields" in value, "rows" in value, "x" in value or "y" in value]
            require(sum(modes) == 1, context, "choose one of field, fields, x/y or rows")
            for field in ("field", "x", "y"):
                if field in value or (field in ("x", "y") and modes[3]):
                    text(value.get(field), context + "." + field)
            for field in ("fields", "color_by"):
                if field in value:
                    for child in sequence(value[field], context + "." + field, 1):
                        text(child, context + "." + field)
            if "rows" in value:
                require(value["rows"] is True, context, "use rows: true")
            if "color_by_sign" in value:
                require(type(value["color_by_sign"]) is bool, context, "color_by_sign must be boolean")
            if "color_by" in value:
                require(len(value["color_by"]) == 2 and not value.get("color_by_sign"), context, "color_by needs two fields and excludes color_by_sign")
            require(not modes[2] or not (value.get("color_by_sign") or "color_by" in value), context, "rows cannot use color bindings")
    elif isinstance(value, dict):
        mapping(value, context)
        for key, child in value.items():
            echarts_option(child, chart, params, context + "." + key, depth + 1)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            echarts_option(child, chart, params, f"{context}[{index}]", depth + 1)
    elif isinstance(value, str) and value.startswith("js:"):
        text(value[3:], context)
    elif value is not None:
        scalar(value, context)


def vela_option(value, params, context):
    required = {"time", "open", "high", "low", "close"}
    option = mapping(value, context, required | {"volume", "time_unit", "timeframe", "show_volume", "indicators"}, required)
    for field in required | ({"volume"} if "volume" in option else set()):
        text(option[field], context + "." + field)
    require(option.get("time_unit", "iso8601") in ("iso8601", "seconds", "milliseconds"), context, "unsupported time_unit")
    timeframe = text(option.get("timeframe", "1d"), context + ".timeframe")
    require(re.fullmatch(r"[1-9][0-9]{0,5}[mhdw]", timeframe), context, "timeframe requires a positive m/h/d/w interval")
    if "show_volume" in option:
        require(type(option["show_volume"]) is bool, context, "show_volume must be boolean")
        require(not option["show_volume"] or "volume" in option, context, "show_volume requires volume")
    for index, indicator in enumerate(sequence(option.get("indicators", []), context + ".indicators", 0, 16)):
        location = f"{context}.indicators[{index}]"
        mapping(indicator, location, {"type", "inputs"}, {"type"})
        text(indicator["type"], location + ".type")
        for name, value in mapping(indicator.get("inputs", {}), location + ".inputs").items():
            if isinstance(value, dict):
                mapping(value, location + ".inputs." + name, {"from", "name"}, {"from", "name"})
                parameter = text(value["name"], location + ".inputs." + name)
                require(value["from"] == "params" and parameter in params, location, "input must reference a defined parameter")
            else:
                scalar(value, location + ".inputs." + name)


def validate_metadata(document, context):
    validate_localization(document, context)
    metadata = mapping(document.get("metadata"), context + ".metadata",
                       {"id", "title", "notes", "tags"}, {"id", "title"})
    identifier(metadata["id"], context + ".metadata.id")
    localized_text(metadata["title"], context + ".metadata.title")
    if "notes" in metadata:
        localized_text(metadata["notes"], context + ".metadata.notes", nonempty=False)
    validate_tags(metadata.get("tags", []), context + ".metadata.tags")


def validate_chart(document, context):
    mapping(document, context, {"i18n", "metadata", "params", "sources", "dataset", "chart"}, {"metadata", "dataset", "chart"})
    validate_metadata(document, context)
    params = parameters(document.get("params", []), context + ".params")
    sources = mapping(document.get("sources", {}), context + ".sources")
    require(len(sources) <= 32, context, "at most 32 sources per chart")
    for name, value in sources.items():
        identifier(name, context + ".sources")
        mapping(value, context + ".sources." + name)
        source(value, context + ".sources." + name)
    dataset = mapping(document["dataset"], context + ".dataset", {"id", "sources", "sql", "ref", "with"}, {"id"})
    identifier(dataset["id"], context + ".dataset.id")
    if "ref" in dataset:
        require(not {"sources", "sql"} & dataset.keys(), context, "dataset ref excludes sources and sql")
        reference(dataset["ref"], context + ".dataset.ref", "dataset")
        bindings(dataset.get("with", {}), context + ".dataset.with")
    else:
        require("with" not in dataset, context, "with requires ref")
        inputs = sequence(dataset.get("sources"), context + ".dataset.sources", 1, 32)
        names = []
        for value in inputs:
            mapping(value, context + ".dataset.sources", {"id", "ref", "with"}, {"id", "ref"})
            names.append(identifier(value["id"], context + ".dataset.sources.id").lower())
            reference(value["ref"], context + ".dataset.sources.ref", "source")
            bindings(value.get("with", {}), context + ".dataset.sources.with")
        unique(names, context + ".dataset.sources")
        require(len(inputs) == 1 or "sql" in dataset, context, "multiple dataset inputs require sql")
        if "sql" in dataset:
            text(dataset["sql"], context + ".dataset.sql")
    chart = mapping(document["chart"], context + ".chart")
    renderer = chart.get("renderer", "default")
    fields = {"default": {"plot", "x", "y", "average", "color", "x_end"}, "value": {"value"}, "echarts": {"option", "scripts"}, "vela": {"option"}, "html": {"option"}, "vega_lite": {"option"}}
    require(isinstance(renderer, str) and renderer in fields, context, "unsupported chart renderer")
    mapping(chart, context + ".chart", {"dataset", "renderer"} | fields[renderer], {"dataset"})
    require(chart["dataset"] == dataset["id"], context, "chart.dataset must equal dataset.id")
    if renderer == "default":
        require(chart.get("plot") in ("line", "area", "bar", "pie", "scatter", "heatmap", "rule"), context, "unsupported native plot")
        plot = chart["plot"]
        require("color" not in chart or plot == "heatmap", context, "color requires heatmap")
        require("x_end" not in chart or plot == "rule", context, "x_end requires rule")
        require(plot not in ("scatter", "heatmap", "rule") or "average" not in chart, context, "coordinate marks do not support average")
        if plot == "heatmap":
            text(chart.get("color"), context + ".chart.color")
        if plot == "rule":
            text(chart.get("x_end"), context + ".chart.x_end")
        for field in ("x", "y"):
            text(chart.get(field), context + ".chart." + field)
        if "average" in chart:
            text(chart["average"], context + ".chart.average")
            require(chart["plot"] != "pie", context, "pie does not support average")
    elif renderer == "value":
        text(chart.get("value"), context + ".chart.value")
    elif renderer == "vela":
        vela_option(chart.get("option"), params, context + ".chart.option")
    else:
        if renderer == "html":
            option = mapping(chart.get("option"), context + ".chart.option", {"html", "css", "data"}, {"html"})
            text(option["html"], context + ".chart.option.html")
            if "css" in option:
                require(isinstance(option["css"], str), context, "css must be text")
            if "data" in option:
                require(isinstance(option["data"], (dict, list)), context, "data must be an object or array")
        if renderer == "vega_lite":
            option = mapping(chart.get("option"), context + ".chart.option")
            require(any(key in option for key in ("mark", "layer", "facet", "hconcat", "vconcat", "concat", "repeat")), context, "Vega-Lite requires a mark or composed view")
        require(chart["dataset"] not in ("params", "script"), context, "reserved dataset ID")
        require(bool(mapping(chart.get("option"), context + ".chart.option")), context, "option cannot be empty")
        for name, script in mapping(chart.get("scripts", {}), context + ".chart.scripts").items():
            require(re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", name), context, "invalid script name")
            text(script, context + ".chart.scripts." + name)
        echarts_option(chart["option"], chart, params, context + ".chart.option")


def chart_references(document):
    """Yield only definition references, never similarly named keys in user JSON."""
    for name, value in document.get("sources", {}).items():
        if "ref" in value:
            yield "sources/" + name, value, "source"
    dataset = document["dataset"]
    if "ref" in dataset:
        yield "dataset", dataset, "dataset"
    else:
        for value in dataset["sources"]:
            yield "dataset", value, "source"


def validate_chart_graph(charts, context, paths=None):
    paths = paths or {}
    definitions = {name: parameters(document.get("params", []), context + "/" + name + ".params") for name, document in charts.items()}
    edges = {}
    for name, document in charts.items():
        for source_name, definition in document.get("sources", {}).items():
            for dependency in definition.get("depends_on") or []:
                location = f"{context}/{paths.get(name, name + '.yaml')}.sources/{source_name}"
                require(dependency in document.get("sources", {}), location, "missing source dependency")
                edges.setdefault((name, "sources/" + source_name), []).append((name, "sources/" + dependency))
        for node, value, kind in chart_references(document):
            location = f"{context}/{paths.get(name, name + '.yaml')}.{node}"
            match = reference(value["ref"], location, kind)
            target = match[1] or name
            require(target in charts, location, f"missing local chart {target}")
            require(match[3] is None or match[3] in charts[target].get("sources", {}), location, "missing reference target")
            validate_bindings(value.get("with", {}), definitions[name], definitions[target], location + ".with", inherit=target == name)
            edges.setdefault((name, node), []).append((target, match[2]))
    visited = set()

    def visit(node, active):
        require(node not in active and len(active) < 64, context, f"cyclic or excessively deep reference at {node}")
        if node in visited:
            return
        for target in edges.get(node, []):
            visit(target, active | {node})
        visited.add(node)

    for node in edges:
        visit(node, set())


def validate_dashboard(document, charts, context):
    mapping(document, context, {"i18n", "version", "kind", "metadata", "params", "tabs"}, {"version", "kind", "metadata", "params", "tabs"})
    validate_metadata(document, context)
    require(type(document["version"]) is int and document["version"] == 1 and document["kind"] == "Dashboard", context, "expected version: 1 and kind: Dashboard")
    params = parameters(document["params"], context + ".params")
    tab_ids, panel_ids = [], []
    for tab in sequence(document["tabs"], context + ".tabs", 1):
        mapping(tab, context + ".tabs", {"id", "title", "panels", "layout"}, {"id", "title", "panels"})
        tab_ids.append(identifier(tab["id"], context + ".tabs.id"))
        localized_text(tab["title"], context + ".tabs.title")
        grid = tab.get("layout")
        if grid is not None:
            mapping(grid, context + ".layout", {"type", "columns", "row_height", "gap", "min_width"}, {"type"})
            require(grid["type"] == "grid", context, "layout type must be grid")
            columns = number(grid.get("columns", 12), context + ".layout.columns", 1, 12, integer=True)
            row = number(grid.get("row_height", 40), context + ".layout.row_height", 24, 120)
            gap = number(grid.get("gap", 12), context + ".layout.gap", 0, 32)
            width = number(grid.get("min_width", 1200), context + ".layout.min_width", 320, 2400)
            require(width > (columns - 1) * gap, context, "min_width must exceed column gaps")
        for panel in sequence(tab["panels"], context + ".panels"):
            mapping(panel, context + ".panels", {"id", "chart", "height", "params", "width", "row_span", "responsive"}, {"id", "chart"})
            panel_ids.append(identifier(panel["id"], context + ".panels.id"))
            identifier(panel["chart"], context + ".panels.chart")
            require(panel["chart"] in charts, context, "dashboard references a missing chart in this workspace")
            number(panel.get("height", 240), context + ".panels.height", 160, 600)
            if grid is None:
                require(not {"width", "row_span", "responsive"} & panel.keys(), context, "panel layout fields require a grid tab")
            else:
                number(panel.get("width", columns), context + ".panels.width", 1, columns, integer=True)
                span = number(panel.get("row_span", 4), context + ".panels.row_span", 1, 24, integer=True)
                require(span * row + (span - 1) * gap >= 160, context, "grid card must be at least 160 points high")
                if "responsive" in panel:
                    responsive = mapping(panel["responsive"], context + ".responsive", {"compact"}, {"compact"})
                    compact = mapping(responsive["compact"], context + ".compact", {"card_height"}, {"card_height"})
                    number(compact["card_height"], context + ".compact.card_height", 160, 600)
            target = parameters(charts[panel["chart"]].get("params", []), context + ".chart.params")
            validate_bindings(panel.get("params", {}), params, target, context + ".panels.params")
    unique(tab_ids, context + ".tabs")
    unique(panel_ids, context + ".panels")


def normalized_tags(tags):
    result, seen = [], set()
    for value in tags:
        name = value.strip()
        key = "".join(c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn").lower()
        if key not in seen:
            seen.add(key)
            result.append(name)
    return result


def validate_tags(tags, context):
    require(isinstance(tags, list), context, "tags must be a list of strings")
    for tag in tags:
        require(isinstance(tag, str) and bool(tag.strip()), context, "tags must be nonempty strings")
        require(len(tag.strip()) <= 64 and not any(unicodedata.category(c) == "Cc" for c in tag), context,
                "tags must contain 1–64 characters without control characters")
