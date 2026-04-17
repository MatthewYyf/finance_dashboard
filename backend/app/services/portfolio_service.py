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


def get_portfolio_data():
    reference_code = send_flex_request(TOKEN, QUERY_ID)
    print("Reference code:", reference_code)

    xml_text = wait_for_statement(TOKEN, reference_code, retries=12, delay_seconds=5)

    open_pos_df = extract_open_positions(xml_text)
    positions_list = positions_df_to_list(open_pos_df)
    
    total, cash, stock = extract_nav(xml_text)

    return {
        "total_value": total,
        "daily_change": 1.24,
        "positions": positions_list,
    }