from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime


# ======================================================
# Helper Functions
# ======================================================

def clean_text(text):
    """
    Remove extra spaces and non-breaking spaces.
    """
    if text is None:
        return ""

    return text.replace("\xa0", " ").strip()


def to_number(text):
    """
    Convert a string into int/float where possible.
    Returns None for blank or NA values.
    """

    text = clean_text(text)

    text = (
        text.replace("₹", "")
            .replace(",", "")
            .replace("%", "")
            .replace("Cr", "")
            .strip()
    )

    if text == "":
        return None

    if text.upper() == "NA":
        return None

    try:
        if "." in text:
            return float(text)

        return int(text)

    except Exception:
        return text


def extract_yoy(td):
    """
    Preserve sign of YoY percentage.

    Examples
    --------
    ⇡ 10%  -> 10
    ⇣ 7%   -> -7
    """

    span = td.find("span", class_="change")

    if span is None:
        return None

    txt = clean_text(span.get_text())

    match = re.search(r"(\d+(\.\d+)?)", txt)

    if match is None:
        return None

    value = float(match.group(1))

    if "⇣" in txt:
        value *= -1

    if value.is_integer():
        return int(value)

    return value


# ======================================================
# Main Parser
# ======================================================

def parse_html(html_file):
    """
    Parse Screener Latest Quarterly Results HTML.

    Parameters
    ----------
    html_file
        Uploaded HTML file (Streamlit UploadedFile)
        or an opened HTML file.

    Returns
    -------
    pandas.DataFrame
    """

    soup = BeautifulSoup(html_file, "lxml")

    company_headers = soup.select(
        "div.flex-row.flex-space-between.flex-align-center"
    )

    if len(company_headers) == 0:
        raise ValueError(
            "This doesn't appear to be a valid Screener "
            "'Latest Quarterly Results' HTML page."
        )

    extraction_datetime = datetime.now()

    extraction_date = extraction_datetime.strftime("%Y-%m-%d")

    extraction_time = extraction_datetime.strftime("%H:%M:%S")

    records = []

    # ==================================================
    # Loop through each company
    # ==================================================

    for header in company_headers:

        try:

            # ------------------------------------------
            # Company Name
            # ------------------------------------------

            company = header.select_one(
                "span.hover-link"
            ).get_text(strip=True)

            # ------------------------------------------
            # Metadata
            # ------------------------------------------

            price = None
            market_cap = None
            pe = None

            for span in header.select("span.sub"):

                label = span.get_text(
                    " ",
                    strip=True
                )

                strong = span.find(
                    "span",
                    class_="strong"
                )

                if strong is None:
                    continue

                if label.startswith("Price"):

                    price = to_number(
                        strong.text
                    )

                elif label.startswith("M.Cap"):

                    market_cap = to_number(
                        strong.text
                    )

                elif label.startswith("PE"):

                    pe = to_number(
                        strong.text
                    )

            # ------------------------------------------
            # Quarterly Table
            # ------------------------------------------

            table = header.find_next("table")

            if table is None:
                continue

            headers = table.select("thead th")

            if len(headers) < 5:
                continue

            latest_q = clean_text(headers[2].text)
            previous_q = clean_text(headers[3].text)
            oldest_q = clean_text(headers[4].text)

            rows = table.select("tbody tr")

            for row in rows:

                cols = row.find_all("td")

                if len(cols) < 5:
                    continue

                metric = clean_text(cols[0].text)

                yoy = extract_yoy(cols[1])

                latest = to_number(
                    cols[2].get_text(" ", strip=True)
                )

                previous = to_number(
                    cols[3].get_text(" ", strip=True)
                )

                oldest = to_number(
                    cols[4].get_text(" ", strip=True)
                )

                records.append({

                    "Company Name": company,

                    "Market Cap (₹ Cr)": market_cap,

                    "Price (₹)": price,

                    "P/E Ratio": pe,

                    "Financial Metric": metric,

                    oldest_q: oldest,

                    previous_q: previous,

                    latest_q: latest,

                    "YOY Growth (%)": yoy,

                    "Extraction Date": extraction_date,

                    "Extraction Time": extraction_time

                })

        except Exception as e:

            print(f"Skipping company: {e}")

            continue
            # ==================================================
    # Create DataFrame
    # ==================================================

    if len(records) == 0:
        raise ValueError(
            "No financial records could be extracted from the HTML file."
        )

    df = pd.DataFrame(records)

    # ==================================================
    # Arrange Quarter Columns Chronologically
    # ==================================================

    quarter_pattern = r"^[A-Za-z]{3}\s\d{4}$"

    quarter_cols = [
        col for col in df.columns
        if re.match(quarter_pattern, col)
    ]

    quarter_cols = sorted(
        quarter_cols,
        key=lambda x: pd.to_datetime(
            x,
            format="%b %Y"
        )
    )

    # ==================================================
    # Final Column Order
    # ==================================================

    final_columns = [
        "Company Name",
        "Market Cap (₹ Cr)",
        "Price (₹)",
        "P/E Ratio",
        "Financial Metric",
    ]

    final_columns.extend(quarter_cols)

    final_columns.extend([
        "YOY Growth (%)",
        "Extraction Date",
        "Extraction Time"
    ])

    df = df[final_columns]

    # ==================================================
    # Convert Numeric Columns
    # ==================================================

    numeric_columns = [
        "Market Cap (₹ Cr)",
        "Price (₹)",
        "P/E Ratio",
        "YOY Growth (%)"
    ] + quarter_cols

    for col in numeric_columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # ==================================================
    # Sort Data
    # ==================================================

    df = df.sort_values(
        by=[
            "Company Name",
            "Financial Metric"
        ]
    ).reset_index(drop=True)

    return df