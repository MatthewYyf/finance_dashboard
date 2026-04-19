from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models import PortfolioPosition, PortfolioSnapshot
from app.services.market_data_service import get_current_prices

import time
import requests
import xml.etree.ElementTree as ET
import pandas as pd

from dotenv import load_dotenv
import os

load_dotenv()


FLEX_BASE = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"
USER_AGENT = "PythonFinanceDashboard/1.0"


TOKEN = os.getenv('ibkr_flex_query')
QUERY_ID = os.getenv('ibkr_flex_query_id')


def _parse_xml(text: str) -> ET.Element:
    return ET.fromstring(text)


def _get_child_text(root: ET.Element, tag: str):
    node = root.find(tag)
    return node.text.strip() if node is not None and node.text is not None else None


def send_flex_request(token: str, query_id: str, flex_version: int = 3) -> str:
    """
    Step 1: Ask IBKR to generate the report.
    Returns the reference code.
    """
    url = f"{FLEX_BASE}/SendRequest"
    params = {
        "t": token,
        "q": query_id,
        "v": flex_version,
    }
    headers = {
        "User-Agent": USER_AGENT
    }

    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()

    root = _parse_xml(resp.text)

    status = _get_child_text(root, "Status")
    if status != "Success":
        error_code = _get_child_text(root, "ErrorCode")
        error_message = _get_child_text(root, "ErrorMessage")
        raise RuntimeError(f"Flex SendRequest failed: {error_code} - {error_message}")

    reference_code = _get_child_text(root, "ReferenceCode")
    if not reference_code:
        raise RuntimeError("Flex SendRequest succeeded but no ReferenceCode was returned.")

    return reference_code


def get_flex_statement(token: str, reference_code: str, flex_version: int = 3) -> str:
    """
    Step 2: Retrieve the generated report XML.
    Returns the XML response body as text.
    """
    url = f"{FLEX_BASE}/GetStatement"
    params = {
        "t": token,
        "q": reference_code,
        "v": flex_version,
    }
    headers = {
        "User-Agent": USER_AGENT
    }

    resp = requests.get(url, params=params, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.text


def wait_for_statement(token: str, reference_code: str, retries: int = 10, delay_seconds: int = 5) -> str:
    """
    Poll GetStatement until the report is ready.
    IBKR may return an XML error like '1004 Statement is incomplete at this time'.
    """
    for attempt in range(1, retries + 1):
        xml_text = get_flex_statement(token, reference_code)

        # If the response is the final report, it will usually contain FlexStatements / FlexStatement
        if "<FlexStatement" in xml_text or "<FlexStatements" in xml_text:
            return xml_text

        # Otherwise it may be an error/status XML
        try:
            root = _parse_xml(xml_text)
            status = _get_child_text(root, "Status")
            if status == "Fail":
                error_code = _get_child_text(root, "ErrorCode")
                error_message = _get_child_text(root, "ErrorMessage")

                # Common "not ready yet" cases from IBKR docs
                if error_code in {"1001", "1003", "1004", "1005", "1006", "1008", "1009"}:
                    print(f"Attempt {attempt}/{retries}: report not ready yet ({error_code}: {error_message})")
                    time.sleep(delay_seconds)
                    continue

                raise RuntimeError(f"Flex GetStatement failed: {error_code} - {error_message}")
        except ET.ParseError:
            pass

        # Fallback retry
        print(f"Attempt {attempt}/{retries}: unexpected response, retrying...")
        time.sleep(delay_seconds)

    raise TimeoutError("Timed out waiting for IBKR Flex statement to become available.")


def extract_open_positions(xml_text: str) -> pd.DataFrame:
    """
    Parse OpenPosition rows from the returned Flex XML into a DataFrame.
    Exact attributes depend on the fields you selected in your Flex Query template.
    """
    root = _parse_xml(xml_text)

    rows = []
    for elem in root.iter():
        # Common tag name in Flex output
        if elem.tag == "OpenPosition":
            rows.append(dict(elem.attrib))

    if not rows:
        print("No <OpenPosition> rows found. Check that your Flex Query includes Open Positions.")
        return pd.DataFrame()

    return pd.DataFrame(rows)

def extract_nav(xml_text: str) -> tuple:
    """
    Extract Net Asset Value (NAV) from IBKR Flex XML file.
    Returns a tuple: (total, cash, stock)
    """
    root = _parse_xml(xml_text)
    for elem in root.iter("EquitySummaryByReportDateInBase"):
        attribs = elem.attrib
        total = float(attribs.get("total", "nan"))
        cash = float(attribs.get("cashLong", "nan"))
        stock = float(attribs.get("stockLong", "nan"))
        return (total, cash, stock)
    print("No <EquitySummaryByReportDateInBase> rows found.")
    return (float('nan'), float('nan'), float('nan'))

def positions_df_to_list(df: pd.DataFrame) -> list:
    """
    Convert a DataFrame of open positions to a list of dicts for the API response.
    Expects columns: symbol (or conid), position, costBasisPerShare.
    """
    positions = []
    if not df.empty:
        for _, row in df.iterrows():
            position = {
                "symbol": row.get("symbol", row.get("conid", "")),  # Prefer 'symbol', fallback to 'conid'
                "shares": float(row.get("position", 0)),
                "avg_cost": float(row.get("costBasisPrice", 0)),
            }
            positions.append(position)
    return positions


def fetch_portfolio():
    reference_code = send_flex_request(TOKEN, QUERY_ID)
    print("Reference code:", reference_code)

    xml_text = wait_for_statement(TOKEN, reference_code, retries=12, delay_seconds=5)

    open_pos_df = extract_open_positions(xml_text)
    positions_list = positions_df_to_list(open_pos_df)
    
    total, cash, stock = extract_nav(xml_text)

    return {
        "total_value": total,
        "cash": cash,
        "stock": stock,
        "positions": positions_list,
    }


def get_saved_portfolio(db: Session):
    snapshot = (
        db.query(PortfolioSnapshot)
        .order_by(PortfolioSnapshot.updated_at.desc())
        .first()
    )

    positions = db.query(PortfolioPosition).all()

    if not snapshot:
        return {
            "total_value": 0,
            "cash": 0,
            "updated_at": None,
            "positions": [],
            "total_unrealized_gain": 0,
        }

    # When only saved snapshot (no quotes), unrealized gain cannot be reliably calculated
    return {
        "total_value": snapshot.total_value,
        "cash": snapshot.cash,
        "stock": snapshot.stock,
        "updated_at": snapshot.updated_at.isoformat(),
        "positions": [
            {
                "symbol": p.symbol,
                "shares": p.shares,
                "avg_cost": p.avg_cost,
            }
            for p in positions
        ],
        "total_unrealized_gain": None, # Not available in saved snapshot
    }

def refresh_portfolio(db: Session):
    fresh_data = fetch_portfolio()

    db.query(PortfolioPosition).delete()

    for pos in fresh_data["positions"]:
        db.add(
            PortfolioPosition(
                symbol=pos["symbol"],
                shares=pos["shares"],
                avg_cost=pos["avg_cost"],
            )
        )

    snapshot = PortfolioSnapshot(
        total_value=fresh_data["total_value"],
        cash=fresh_data["cash"],
        stock=fresh_data["stock"],
    )

    db.add(snapshot)
    db.commit()

    return get_saved_portfolio(db)

def get_live_portfolio(db: Session):
    saved = get_saved_portfolio(db)
    symbols = [p["symbol"] for p in saved["positions"]]
    prices = get_current_prices(symbols)

    live_positions = []
    live_stock_value = 0.0
    total_unrealized_gain = 0.0

    for p in saved["positions"]:
        current_price = prices.get(p["symbol"])
        market_value = current_price * p["shares"] if current_price is not None else None
        unrealized_gain = (
            (current_price - p["avg_cost"]) * p["shares"]
            if current_price is not None
            else None
        )

        if market_value is not None:
            live_stock_value += market_value

        if unrealized_gain is not None:
            total_unrealized_gain += unrealized_gain

        live_positions.append(
            {
                **p,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_gain": unrealized_gain,
            }
        )

    return {
        "total_value": saved["cash"] + live_stock_value,
        "cash": saved["cash"],
        "stock": live_stock_value,
        "updated_at": saved["updated_at"],
        "quote_updated_at": datetime.utcnow().isoformat(),
        "positions": live_positions,
        "total_unrealized_gain": total_unrealized_gain,
    }