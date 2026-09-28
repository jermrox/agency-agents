"""Read price, stock and seller from a retailer product page.

Retailers embed schema.org ``Product`` / ``Offer`` markup as JSON-LD so search
engines can show price and availability; reading that block is far more
stable than scraping the page layout, and it is the data the retailer has
chosen to publish. If the page has no such markup, or robots.txt disallows
the fetch, or the site answers 403, we stop and say so -- the parent can log
the price by hand with ``add-price``. We never try to get around a block.
"""

from __future__ import annotations

import html
import json
import logging
from html.parser import HTMLParser
from typing import Any, Iterable

from .http import FetchError, allowed_by_robots, fetch
from .models import Observation

log = logging.getLogger(__name__)

AVAILABILITY = {
    "instock": "in_stock",
    "limitedavailability": "low_stock",
    "outofstock": "out_of_stock",
    "soldout": "out_of_stock",
    "discontinued": "out_of_stock",
    "preorder": "preorder",
    "presale": "preorder",
    "backorder": "backorder",
    "onlineonly": "online_only",
    "instoreonly": "store_only",
}


class CollectError(RuntimeError):
    pass


class _LDCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._on = False
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag == "script":
            kind = dict((k.lower(), v or "") for k, v in attrs).get("type", "").lower()
            self._on = kind.startswith("application/ld+json")
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._on:
            self._on = False
            if "".join(self._buf).strip():
                self.blocks.append("".join(self._buf).strip())

    def handle_data(self, data: str) -> None:
        if self._on:
            self._buf.append(data)


def _decode(block: str) -> Any:
    try:
        return json.loads(block, strict=False)
    except ValueError:
        return json.loads(html.unescape(block), strict=False)


def _nodes(payload: Any, depth: int = 0) -> Iterable[dict[str, Any]]:
    if depth > 6:
        return
    if isinstance(payload, list):
        for item in payload:
            yield from _nodes(item, depth + 1)
    elif isinstance(payload, dict):
        yield payload
        for key in ("@graph", "mainEntity", "itemListElement", "item", "hasVariant"):
            if isinstance(payload.get(key), (list, dict)):
                yield from _nodes(payload[key], depth + 1)


def _types(node: dict[str, Any]) -> set[str]:
    raw = node.get("@type")
    values = raw if isinstance(raw, list) else [raw]
    return {v.rstrip("/").split("/")[-1].split(":")[-1].lower() for v in values if isinstance(v, str)}


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except ValueError:
        return None


def _first_offer(offers: Any) -> dict[str, Any] | None:
    if isinstance(offers, dict):
        if "offers" in offers and "price" not in offers and "lowPrice" not in offers:
            return _first_offer(offers["offers"])
        return offers
    if isinstance(offers, list):
        priced = [o for o in offers if isinstance(o, dict) and _num(o.get("price")) is not None]
        return min(priced, key=lambda o: _num(o.get("price")) or 0) if priced else None
    return None


def extract_products(page_html: str) -> list[dict[str, Any]]:
    """Every schema.org Product on the page, flattened to the fields we use."""
    parser = _LDCollector()
    parser.feed(page_html)
    out = []
    for block in parser.blocks:
        try:
            payload = _decode(block)
        except ValueError:
            log.debug("skipping undecodable JSON-LD block")
            continue
        for node in _nodes(payload):
            if not _types(node) & {"product", "productgroup"}:
                continue
            offer = _first_offer(node.get("offers"))
            if not offer:
                continue
            price = _num(offer.get("price", offer.get("lowPrice")))
            if price is None:
                continue
            availability = str(offer.get("availability", "")).rstrip("/").split("/")[-1].lower()
            seller = offer.get("seller")
            seller_name = seller.get("name") if isinstance(seller, dict) else (seller if isinstance(seller, str) else None)
            brand = node.get("brand")
            rating = node.get("aggregateRating") or {}
            spec = offer.get("priceSpecification")
            list_price = None
            for s in spec if isinstance(spec, list) else [spec]:
                if isinstance(s, dict) and "ListPrice" in str(s.get("priceType", "")):
                    list_price = _num(s.get("price"))
            out.append({
                "name": node.get("name"),
                "brand": brand.get("name") if isinstance(brand, dict) else brand,
                "sku": node.get("sku"),
                "mpn": node.get("mpn"),
                "gtin": node.get("gtin13") or node.get("gtin12") or node.get("gtin"),
                "price": price,
                "currency": offer.get("priceCurrency", "USD"),
                "list_price": list_price,
                "stock_status": AVAILABILITY.get(availability, "unknown"),
                "seller": seller_name,
                "rating": _num(rating.get("ratingValue")) if isinstance(rating, dict) else None,
                "review_count": int(_num(rating.get("reviewCount") or rating.get("ratingCount")) or 0)
                if isinstance(rating, dict) and (rating.get("reviewCount") or rating.get("ratingCount")) else None,
            })
    return out


def observation_from_page(key: str, retailer: str, url: str, page_html: str,
                          unit_count: float | None = None, unit_label: str | None = None) -> Observation:
    products = extract_products(page_html)
    if not products:
        raise CollectError(f"No schema.org Product price on {url}; log it with add-price instead.")
    p = products[0]
    sold_by = None
    if p["seller"]:
        sold_by = retailer.lower() in p["seller"].lower() or (p["brand"] or "~").lower() in p["seller"].lower()
    return Observation(
        key=key, retailer=retailer, price=p["price"], source="jsonld", currency=p["currency"] or "USD",
        list_price=p["list_price"], stock_status=p["stock_status"], seller=p["seller"],
        sold_by_retailer=sold_by, url=url, rating=p["rating"], review_count=p["review_count"],
        unit_count=unit_count, unit_label=unit_label,
    )


def collect(key: str, retailer: str, url: str, **kwargs: Any) -> Observation:
    if not allowed_by_robots(url):
        raise CollectError(f"robots.txt disallows {url}; not fetching. Log it with add-price instead.")
    try:
        body = fetch(url).decode("utf-8", "replace")
    except FetchError as exc:
        raise CollectError(f"{retailer}: {exc}. Not retrying around a block; use add-price.") from exc
    return observation_from_page(key, retailer, url, body, **kwargs)
