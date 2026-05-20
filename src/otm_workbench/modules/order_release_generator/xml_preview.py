import xml.etree.ElementTree as ET
from collections import defaultdict

from otm_workbench.models import OrderReleaseBatch, OrderReleaseBatchRow
from otm_workbench.modules.order_release_generator.batches import parse_json_object


def xid_from_gid(gid: str) -> str:
    return gid.rsplit(".", 1)[-1] if "." in gid else gid


def add_gid(parent: ET.Element, tag_name: str, gid: str) -> None:
    wrapper = ET.SubElement(parent, tag_name)
    gid_node = ET.SubElement(wrapper, "Gid")
    domain = ET.SubElement(gid_node, "DomainName")
    domain.text = gid.split(".", 1)[0] if "." in gid else "OTM1"
    xid = ET.SubElement(gid_node, "Xid")
    xid.text = xid_from_gid(gid)


def build_order_release_xml(batch: OrderReleaseBatch, rows: list[OrderReleaseBatchRow]) -> dict[str, object]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        values = {key: str(value) for key, value in parse_json_object(row.normalized_json).items()}
        release_gid = values.get("release_gid")
        if release_gid:
            grouped[release_gid].append(values)

    root = ET.Element("Transmission")
    body = ET.SubElement(root, "TransmissionBody")
    line_count = 0
    for release_gid in sorted(grouped):
        element = ET.SubElement(body, "GLogXMLElement")
        release = ET.SubElement(element, "Release")
        add_gid(release, "ReleaseGid", release_gid)
        first_row = grouped[release_gid][0]
        add_gid(release, "SourceLocationRef", first_row["source_location_gid"])
        add_gid(release, "DestLocationRef", first_row["destination_location_gid"])
        ET.SubElement(release, "EarlyPickupDate").text = first_row["early_pickup_date"]
        ET.SubElement(release, "LateDeliveryDate").text = first_row["late_delivery_date"]
        for line_number, values in enumerate(grouped[release_gid], start=1):
            line_count += 1
            line = ET.SubElement(release, "ReleaseLine")
            ET.SubElement(line, "LineNumber").text = str(line_number)
            add_gid(line, "ItemRef", values["item_gid"])
            add_gid(line, "PackagedItemRef", values["packaged_item_gid"])
            weight = ET.SubElement(line, "Weight")
            ET.SubElement(weight, "WeightValue").text = values["weight"]
            ET.SubElement(weight, "WeightUOMGid").text = values["weight_uom"]

    return {
        "batch_id": batch.id,
        "release_count": len(grouped),
        "line_count": line_count,
        "xml": ET.tostring(root, encoding="unicode"),
    }
