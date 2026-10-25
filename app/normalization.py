
import json
import re
from typing import Any

from bs4 import BeautifulSoup


def clean_value(value: Any) -> Any:
    if value is None:
        return None

    if not isinstance(value, str):
        return value

    value = re.sub(r"\s+", " ", value).strip()

    if not value:
        return None

    if value.lower() in {"true", "yes"}:
        return True

    if value.lower() in {"false", "no"}:
        return False

    # Preserve IDs containing leading zeroes.
    if re.fullmatch(r"-?(0|[1-9]\d*)(\.\d+)?", value):
        try:
            return float(value) if "." in value else int(value)
        except ValueError:
            return value

    return value


def decode_sveltekit(payload: dict[str, Any]) -> Any:
    """Decode the indexed data graph returned by SvelteKit."""
    nodes = payload.get("nodes", [])

    data_node = next(
        (
            node
            for node in nodes
            if node.get("type") == "data"
            and isinstance(node.get("data"), list)
        ),
        None,
    )

    if data_node is None:
        return payload

    values = data_node["data"]
    cache: dict[int, Any] = {}
    resolving: set[int] = set()

    def resolve(index: int) -> Any:
        if index in cache:
            return cache[index]

        if index < 0 or index >= len(values):
            return None

        if index in resolving:
            return None

        resolving.add(index)
        value = values[index]

        if isinstance(value, list):
            result = [resolve_item(item) for item in value]
        elif isinstance(value, dict):
            result = {
                key: resolve_item(item)
                for key, item in value.items()
            }
        else:
            result = value

        resolving.remove(index)
        cache[index] = result
        return result

    def resolve_item(value: Any) -> Any:
        # SvelteKit represents object properties and array elements
        # using integer references into the data array.
        if isinstance(value, int) and not isinstance(value, bool):
            return resolve(value)

        if isinstance(value, list):
            return [resolve_item(item) for item in value]

        if isinstance(value, dict):
            return {
                key: resolve_item(item)
                for key, item in value.items()
            }

        return value

    return resolve(0)


def normalize_meter_detail(payload: Any) -> Any:
    """Convert decoded meter details into a clean REST representation."""
    if not isinstance(payload, dict):
        return payload

    meter_id = payload.get("meterId")
    raw_detail = payload.get("detail", {})
    raw_hierarchy = payload.get("hierarchy", {})

    if isinstance(raw_detail, dict):
        detail_rows = raw_detail.get("data", [])
    else:
        detail_rows = raw_detail

    details: dict[str, Any] = {}

    if isinstance(detail_rows, list):
        for row in detail_rows:
            if isinstance(row, dict):
                name = row.get("parameterName")
                value = row.get("parameterValue")

                if isinstance(name, str):
                    details[name] = clean_value(value)

    hierarchy = {}

    if isinstance(raw_hierarchy, dict):
        field_names = {
            "Zone": "zone",
            "Circle": "circle",
            "Division": "division",
            "Subdivision": "subdivision",
            "Sub Station": "substation",
            "Substation": "substation",
            "Feeder": "feeder",
            "DT": "dt",
        }

        for source, target in field_names.items():
            if source in raw_hierarchy:
                hierarchy[target] = clean_value(raw_hierarchy[source])

    # Include the meter ID even if it wasn't present in the detail rows.
    if meter_id is not None:
        details["Meter ID"] = meter_id

    return {
        "meter_id": meter_id or details.get("Meter ID"),
        "serial_no": details.get("Serial No"),
        "make": details.get("Make"),
        "phase_type": details.get("Phase Type"),
        "installation_status": details.get("Installation Status"),
        "installation_type": details.get("Installation Type"),
        "hierarchy": hierarchy,
    }


def parse_html_tables(html: str) -> list[dict[str, Any]]:
    """Turn HTML tables into records using the first row as headers."""
    soup = BeautifulSoup(html, "html.parser")
    records: list[dict[str, Any]] = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")

        if not rows:
            continue

        first_cells = rows[0].find_all(["th", "td"])
        headers = [
            re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).strip()
            for cell in first_cells
        ]

        if not headers or not any(headers):
            continue

        for row in rows[1:]:
            cells = row.find_all(["th", "td"])
            values = [
                clean_value(cell.get_text(" ", strip=True))
                for cell in cells
            ]

            if not values:
                continue

            record = {}

            for idx, value in enumerate(values):
                key = (
                    headers[idx]
                    if idx < len(headers) and headers[idx]
                    else f"column_{idx + 1}"
                )
                record[key] = value

            records.append(record)

    return records


def parse_response(content: str, content_type: str) -> Any:
    if "json" in content_type.lower():
        try:
            payload = json.loads(content)

            if (
                isinstance(payload, dict)
                and payload.get("type") == "data"
                and isinstance(payload.get("nodes"), list)
            ):
                return decode_sveltekit(payload)

            return payload

        except json.JSONDecodeError:
            pass

    soup = BeautifulSoup(content, "html.parser")

    # Avoid treating a login page as valid data.
    title = (
        soup.title.get_text(" ", strip=True).lower()
        if soup.title
        else ""
    )

    if "login" in title or soup.find("input", {"type": "password"}):
        raise ValueError(
            "Upstream returned a login page; the session may have expired."
        )

    tables = parse_html_tables(content)

    if tables:
        return tables

    text = soup.get_text(" ", strip=True)
    return {"text": re.sub(r"\s+", " ", text).strip()}
