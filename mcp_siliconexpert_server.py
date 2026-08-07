"""
Silicon Expert MCP Server - Full API Coverage

Author: Peter Valencic

Exposes all Silicon Expert Direct API endpoints as MCP tools for use in
Kiro or any MCP-compatible client.

Environment variables:
  SE_USERNAME - Silicon Expert API username/login
  SE_PASSWORD - Silicon Expert API key/password

API Services Implemented (47 tools):
  1.  Authentication Service         - authenticateUser
  2.  Part Search Service            - partsearch (keyword), listPartSearch (batch up to 50)
  3.  CPN Search Service             - CPNSearch (ACL Custom Part Number)
  4.  Part Detail Service            - partDetail (full component data by ComID)
  5.  Cross Reference Service        - xref (FFF alternates, pin-compatible, supplier recommended)
  6.  Parametric Search Service      - parametric/getSearchResult, parametric/getParametricSearchResult
  7.  Taxonomy Service               - parametric/getAllTaxonomy, parametric/getParametricFeatures
  8.  BOM Risk Analysis Service      - bomRiskAnalysis (lifecycle risk scoring)
  9.  Environmental/Compliance       - RoHS, REACH, Conflict Minerals, PFAS, IPC-1752 export
  10. Market Availability Service    - marketAvailability (distributor inventory/pricing)
  11. PCN/EOL Service                - pcn (Product Change Notifications by part/ComID/PCN number)
  12. Smart PCN Service              - showPCNS, smartpcn (ACL-scoped Smart PCNs)
  13. Obsolescence Forecast Service  - YTEOL (Years To End Of Life)
  14. Datasheet Service              - datasheetData (PDF/document links)
  15. Manufacturer Service           - manufacturers (search), supplierProfile (detail)
  16. Pricing Service                - pricingData, PriceBreaksData (price breaks by quantity)
  17. Package/Mounting Service       - packageData (physical package info)
  18. Supply Chain Risk Service      - SupplyChain/GEORisk, SupplyChain/Events (Platinum tier)
  19. ACL Management Service         - alert/listParts, alert/getUpdatesOfTheDay, alert/getUpdates
  20. Part Risk Assessment Service   - RiskData, ResilienceRating (lifecycle, multi-sourcing, inventory)

Reference:
  API Documentation: https://support.siliconexpert.com/hc/en-us/categories/27308956995469-SiliconExpert-Direct-API
  Base URL: https://api.siliconexpert.com/ProductAPI/search/
"""

import os
import json
import requests
from typing import Optional
from mcp.server.fastmcp import FastMCP

# =============================================================================
# CONFIGURATION
# =============================================================================
SE_BASE_URL = "https://api.siliconexpert.com/ProductAPI/search/"

mcp = FastMCP("SiliconExpert")

# Module-level session and auth state
_session = requests.Session()
_logged_in = False


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _ensure_login() -> tuple[bool, str]:
    """Authenticate with Silicon Expert if not already logged in."""
    global _logged_in
    if _logged_in:
        return True, "Already logged in."

    username = os.environ.get("SE_USERNAME", "")
    password = os.environ.get("SE_PASSWORD", "")
    if not username or not password:
        return False, "SE_USERNAME and SE_PASSWORD environment variables must be set."

    post_body = {"login": username, "apiKey": password}
    headers = {"Connection": "keep-alive"}

    try:
        res = _session.post(
            SE_BASE_URL + "authenticateUser",
            data=post_body,
            headers=headers,
            timeout=30,
        )
    except Exception as e:
        return False, f"Login request failed: {e}"

    if res.status_code != 200:
        return False, f"Login failed with status {res.status_code}: {res.text}"

    _logged_in = True
    return True, "Login successful."


def _api_get(endpoint: str, params: dict) -> dict:
    """Make authenticated GET request to SE API."""
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
        "Connection": "keep-alive",
    }
    try:
        res = _session.get(
            SE_BASE_URL + endpoint,
            params=params,
            headers=headers,
            timeout=60,
        )
    except Exception as e:
        return {"error": f"Request to {endpoint} failed: {e}"}

    if res.status_code != 200:
        return {"error": f"Status {res.status_code} from {endpoint}: {res.text[:500]}"}

    try:
        return res.json()
    except Exception:
        return {"error": f"Invalid JSON from {endpoint}", "raw": res.text[:500]}


def _api_post(endpoint: str, data: dict = None, json_body: dict = None) -> dict:
    """Make authenticated POST request to SE API."""
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
        "Connection": "keep-alive",
    }
    try:
        if json_body is not None:
            res = _session.post(
                SE_BASE_URL + endpoint,
                json=json_body,
                headers=headers,
                timeout=60,
            )
        else:
            res = _session.post(
                SE_BASE_URL + endpoint,
                data=data,
                headers=headers,
                timeout=60,
            )
    except Exception as e:
        return {"error": f"POST to {endpoint} failed: {e}"}

    if res.status_code != 200:
        return {"error": f"Status {res.status_code} from {endpoint}: {res.text[:500]}"}

    try:
        return res.json()
    except Exception:
        return {"error": f"Invalid JSON from {endpoint}", "raw": res.text[:500]}


def _login_guard() -> Optional[str]:
    """Returns error JSON string if login fails, None if OK."""
    success, msg = _ensure_login()
    if not success:
        return json.dumps({"error": msg})
    return None


# =============================================================================
# SERVICE 1: AUTHENTICATION
# =============================================================================

@mcp.tool()
def login() -> str:
    """
    Authenticate with the Silicon Expert API using configured credentials.
    Credentials are read from SE_USERNAME and SE_PASSWORD environment variables.
    Must be called before any other API calls (called automatically by other tools).
    """
    success, message = _ensure_login()
    return json.dumps({"success": success, "message": message})


# =============================================================================
# SERVICE 2: PART SEARCH
# =============================================================================

@mcp.tool()
def search_part(
    part_number: str,
    manufacturer: str = "",
    description: str = "",
    lifecycle: str = "",
    rohs: str = "",
    product_line: str = "",
    sort: str = "",
    page_number: int = 1,
    page_size: int = 50,
    wildcard_single: str = "",
    wildcard_multi: str = "",
    mask_part_number: str = "",
) -> str:
    """
    Search for electronic components by keyword (part number, manufacturer, description).
    This is the primary SiliconExpert part search endpoint (partsearch).
    Does NOT consume API quota. Supports wildcards, sorting, and pagination.

    Args:
        part_number: Search keyword - part number or partial match. Use with wildcard params for pattern matching.
        manufacturer: Optional manufacturer filter (e.g. "Vishay", "TI").
        description: Optional description keyword search (e.g. "Diode Switching").
        lifecycle: Optional lifecycle filter (e.g. "Active", "EOL", "NRND").
        rohs: Optional EU RoHS status filter.
        product_line: Optional product line filter (PlName).
        sort: Sort fields, semicolon-separated (e.g. "part number:asc;manufacturer:desc"). Sortable: part number, manufacturer, RoHS, lifecycle.
        page_number: Page number for pagination (default 1).
        page_size: Results per page (default 50, max 250).
        wildcard_single: Character used as single-char wildcard in part_number (e.g. "?" to match b?v99).
        wildcard_multi: Character used as multi-char wildcard in part_number (e.g. "*" to match b*99).
        mask_part_number: Set to "yes" to search by mask part number (without mask mark %).
    """
    err = _login_guard()
    if err:
        return err

    params = {"fmt": "json"}

    if part_number:
        params["partNumber"] = part_number
    if description:
        params["description"] = description
    if manufacturer:
        params["mfr"] = manufacturer
    if lifecycle:
        params["Lifecycle"] = lifecycle
    if rohs:
        params["RoHS"] = rohs
    if product_line:
        params["PlName"] = product_line
    if sort:
        params["sort"] = sort
    if page_number > 1:
        params["pageNumber"] = str(page_number)
    if page_size != 50:
        params["pageSize"] = str(min(page_size, 250))
    if wildcard_single:
        params["wildcardSingle"] = wildcard_single
    if wildcard_multi:
        params["wildcardMulti"] = wildcard_multi
    if mask_part_number:
        params["MaskPartNumber"] = mask_part_number

    data = _api_get("partsearch", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        status = data.get("Status", {})
        total_items = data.get("TotalItems", "")
        results = data.get("Result", [])
        if isinstance(results, dict):
            results = [results]

        parts = []
        for p in results:
            parts.append({
                "com_id": p.get("ComID"),
                "part_number": p.get("PartNumber"),
                "manufacturer": p.get("Manufacturer"),
                "lifecycle": p.get("Lifecycle"),
                "description": p.get("Description", ""),
                "rohs": p.get("RoHS", ""),
                "rohs_version": p.get("RoHSVersion", ""),
                "match_rating": p.get("MatchRating", ""),
                "taxonomy_path": p.get("TaxonomyPath", ""),
                "datasheet": p.get("Datasheet", ""),
                "yeol": p.get("YEOL", ""),
                "resilience_rating": p.get("ResilienceRating"),
                "military_status": p.get("MilitaryStatus"),
                "mask_part": p.get("MaskPart", ""),
            })
        return json.dumps({
            "status": status,
            "total_items": total_items,
            "count": len(parts),
            "parts": parts,
        }, indent=2)
    except Exception:
        return json.dumps(data, indent=2)


@mcp.tool()
def list_part_search(
    part_numbers: str,
    mode: str = "exact",
    page_number: int = 1,
    page_size: int = 50,
    lifecycle: str = "",
    rohs: str = "",
    product_line: str = "",
) -> str:
    """
    Search up to 50 parts in a single request using listPartSearch endpoint.
    Supports exact or "begin with" matching mode.
    Each entry can optionally include a manufacturer name for precise matching.
    Does NOT consume API quota.

    Args:
        part_numbers: Parts to search. Format options:
            - Simple comma-separated: "bav99,NE555,LM7805"
            - With manufacturer (pipe-separated): "bav99|Vishay,bav99wt|Nexperia"
        mode: Search mode - "exact" (default) or "beginwith".
        page_number: Page number for pagination (default 1).
        page_size: Results per page (default 50, max 250).
        lifecycle: Optional lifecycle filter.
        rohs: Optional RoHS status filter.
        product_line: Optional product line filter.
    """
    err = _login_guard()
    if err:
        return err

    # Build the JSON array parameter
    entries = []
    for item in part_numbers.split(","):
        item = item.strip()
        if not item:
            continue
        if "|" in item:
            pn, mfr = item.split("|", 1)
            entries.append({"partNumber": pn.strip(), "manufacturer": mfr.strip()})
        else:
            entries.append({"partNumber": item})

    if not entries:
        return json.dumps({"error": "No part numbers provided."})
    if len(entries) > 50:
        return json.dumps({"error": "Maximum 50 parts per request."})

    params = {
        "partNumber": json.dumps(entries),
        "mode": mode,
        "fmt": "json",
        "pageNumber": str(page_number),
        "pageSize": str(min(page_size, 250)),
    }
    if lifecycle:
        params["Lifecycle"] = lifecycle
    if rohs:
        params["RoHS"] = rohs
    if product_line:
        params["PlName"] = product_line

    data = _api_get("listPartSearch", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    # Parse the nested response structure
    try:
        result = data.get("Result", {})
        # Result can be a single PartData or list of PartData
        if isinstance(result, dict) and "PartData" in result:
            result = [result]
        elif isinstance(result, list):
            pass
        else:
            # Wrap single PartData
            result = [{"PartData": result}] if result else []

        output = []
        for part_data_wrapper in (result if isinstance(result, list) else [result]):
            pd = part_data_wrapper.get("PartData", part_data_wrapper) if isinstance(part_data_wrapper, dict) else {}
            requested_part = pd.get("RequestedPart", "")
            requested_mfr = pd.get("RequestedManufacturer", "")
            part_list = pd.get("PartList", {}).get("PartDto", [])
            if isinstance(part_list, dict):
                part_list = [part_list]

            parts = []
            for p in part_list:
                parts.append({
                    "com_id": p.get("ComID"),
                    "part_number": p.get("PartNumber"),
                    "manufacturer": p.get("Manufacturer"),
                    "lifecycle": p.get("Lifecycle"),
                    "description": p.get("Description", ""),
                    "rohs": p.get("RoHS", ""),
                    "rohs_version": p.get("RoHSVersion", ""),
                    "match_rating": p.get("MatchRating", ""),
                    "match_rating_comment": p.get("MatchRatingComment"),
                    "taxonomy_path": p.get("TaxonomyPath", ""),
                    "datasheet": p.get("Datasheet", ""),
                    "yeol": p.get("YEOL", ""),
                    "resilience_rating": p.get("ResilienceRating"),
                    "military_status": p.get("MilitaryStatus"),
                    "mask_part": p.get("MaskPart", ""),
                    "alias_data": p.get("AliasData"),
                })

            output.append({
                "requested_part": requested_part,
                "requested_manufacturer": requested_mfr,
                "count": len(parts),
                "parts": parts,
            })

        return json.dumps({
            "status": data.get("Status", {}),
            "results": output,
        }, indent=2)
    except Exception:
        return json.dumps(data, indent=2)


@mcp.tool()
def search_part_by_manufacturer(part_number: str, manufacturer: str) -> str:
    """
    Search for a part by part number AND manufacturer name for precise matching.
    Uses the partsearch endpoint with the mfr filter parameter.

    Args:
        part_number: The manufacturer part number to search for.
        manufacturer: The manufacturer name filter.
    """
    err = _login_guard()
    if err:
        return err

    params = {
        "partNumber": part_number.strip(),
        "mfr": manufacturer.strip(),
        "fmt": "json",
    }

    data = _api_get("partsearch", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Result", [])
        if isinstance(results, dict):
            results = [results]

        exact_matches = []
        other_matches = []
        for item in results:
            if not isinstance(item, dict):
                continue
            entry = {
                "com_id": item.get("ComID"),
                "part_number": item.get("PartNumber"),
                "manufacturer": item.get("Manufacturer", ""),
                "lifecycle": item.get("Lifecycle"),
                "description": item.get("Description", ""),
                "rohs": item.get("RoHS", ""),
                "match_rating": item.get("MatchRating", ""),
                "taxonomy_path": item.get("TaxonomyPath", ""),
                "yeol": item.get("YEOL", ""),
            }
            if str(item.get("MatchRating", "")).strip() == "Exact":
                exact_matches.append(entry)
            else:
                other_matches.append(entry)

        return json.dumps({
            "status": data.get("Status", {}),
            "total_items": data.get("TotalItems", ""),
            "query": {"part_number": part_number, "manufacturer": manufacturer},
            "exact_matches": exact_matches,
            "other_matches": other_matches[:10],
            "total_results": len(results),
        }, indent=2)
    except Exception:
        return json.dumps(data, indent=2)


# =============================================================================
# SERVICE 3: PART DETAIL
# =============================================================================

@mcp.tool()
def search_cpn(cpns: str) -> str:
    """
    Search by ACL (Approved Component List) Custom Part Number (CPN).
    Returns all ACL parts associated with the specified CPN(s).

    Args:
        cpns: CPN(s) to search. Format options:
            - Simple: "myCPN1,myCPN2"
            - With MPN (pipe-separated): "myCPN|myMPN"
    """
    err = _login_guard()
    if err:
        return err

    entries = []
    for item in cpns.split(","):
        item = item.strip()
        if not item:
            continue
        if "|" in item:
            cpn, mpn = item.split("|", 1)
            entries.append({"cpn": cpn.strip(), "mpn": mpn.strip()})
        else:
            entries.append({"cpn": item})

    if not entries:
        return json.dumps({"error": "No CPNs provided."})

    params = {"cpns": json.dumps(entries), "fmt": "json"}
    data = _api_get("CPNSearch", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", [])
        if isinstance(results, dict):
            results = [results]
        parts = []
        for r in results:
            parts.append({
                "com_id": r.get("COM_ID"),
                "cpn": r.get("CPN"),
                "mpn": r.get("MPN"),
                "supplier": r.get("Supplier"),
            })
        return json.dumps({
            "status": data.get("Status", {}),
            "count": len(parts),
            "results": parts,
        }, indent=2)
    except Exception:
        return json.dumps(data, indent=2)


@mcp.tool()
def get_ipc_export(com_id: str = "", part_number: str = "", manufacturer: str = "", ipc_class: str = "") -> str:
    """
    Export IPC-1752 material declaration data (XML structured) for a component.
    Search by ComID or by part number + manufacturer.

    Args:
        com_id: SE ComID of the part.
        part_number: Part number (requires manufacturer if used).
        manufacturer: Manufacturer name (required if searching by part_number).
        ipc_class: IPC class filter - "a", "c", or "d". Empty returns all classes.
    """
    err = _login_guard()
    if err:
        return err

    params = {}
    if com_id:
        params["comId"] = com_id.strip()
    elif part_number and manufacturer:
        params["partNumber"] = part_number.strip()
        params["mfr"] = manufacturer.strip()
    else:
        return json.dumps({"error": "Provide com_id, or both part_number and manufacturer."})

    if ipc_class:
        params["class"] = ipc_class.strip()

    # IPC Export returns XML content directly
    headers = {"Connection": "keep-alive"}
    try:
        res = _session.get(SE_BASE_URL + "IPCExport", params=params, headers=headers, timeout=60)
        if res.status_code != 200:
            return json.dumps({"error": f"Status {res.status_code}: {res.text[:500]}"})
        # Return the IPC XML content
        return json.dumps({
            "com_id": com_id or "",
            "part_number": part_number or "",
            "format": "IPC-1752 XML",
            "content": res.text[:10000],  # Limit size for MCP response
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"IPC Export request failed: {e}"})


# =============================================================================
# SERVICE 4: PART DETAIL
# =============================================================================

@mcp.tool()
def get_part_details_full(com_id: str) -> str:
    """
    Get comprehensive part details from Silicon Expert by ComID.
    Returns ALL available data including pricing, specs, compliance, packaging,
    manufacturer info, lifecycle, datasheets, cross-references, and more.
    Use this when you need a complete picture of a component.

    Args:
        com_id: The Silicon Expert ComID (obtained from search_part or search_part_by_manufacturer).
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)
    return json.dumps(data, indent=2)


@mcp.tool()
def get_part_details_batch(com_ids: str) -> str:
    """
    Get full part details for multiple ComIDs in a single call.
    More efficient than calling get_part_details_full for each part individually.

    Args:
        com_ids: Comma-separated list of ComIDs (e.g. "12345,67890,11111").
    """
    err = _login_guard()
    if err:
        return err

    ids = ",".join([c.strip() for c in com_ids.split(",") if c.strip()])
    if not ids:
        return json.dumps({"error": "No ComIDs provided."})

    params = {"comIds": ids}
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)
    return json.dumps(data, indent=2)


# =============================================================================
# SERVICE 4: CROSS REFERENCE
# =============================================================================

@mcp.tool()
def get_cross_references(
    com_id: str = "",
    part_number: str = "",
    manufacturer: str = "",
    cross_type: str = "",
    cross_manufacturer: str = "",
    cross_rohs: str = "",
    part_status: str = "",
    best_cross_only: str = "false",
    page_number: int = 1,
    page_size: int = 50,
) -> str:
    """
    Get cross-reference (alternate) parts using the xref endpoint.
    Search by ComID (preferred for exact results) or by part number.
    Returns FFF equivalents from other manufacturers with cross type rating.

    Cross Types: A=exact drop-in, B=minor differences, C=major differences,
    D=same function different package, S=supplier recommended, SF=similar function.

    Args:
        com_id: SE ComID for exact cross lookup (preferred).
        part_number: Part number to find crosses for (uses keyword matching).
        manufacturer: Manufacturer name (used with part_number search).
        cross_type: Filter by cross type code (A, B, C, D, F, S, SF, A/Upgrade, etc.).
        cross_manufacturer: Filter crosses by manufacturer name.
        cross_rohs: Filter crosses by RoHS status.
        part_status: Filter crosses by lifecycle status.
        best_cross_only: "true" to return only the best cross per part. Default "false".
        page_number: Page number (default 1).
        page_size: Results per page (default 50, max 250).
    """
    err = _login_guard()
    if err:
        return err

    # Build the parts parameter
    if com_id:
        parts_param = [{"comId": int(c.strip())} for c in com_id.split(",") if c.strip()]
    elif part_number:
        entry = {"partNumber": part_number.strip()}
        if manufacturer:
            entry["manufacturer"] = manufacturer.strip()
        parts_param = [entry]
    else:
        return json.dumps({"error": "Provide either com_id or part_number."})

    params = {
        "parts": json.dumps(parts_param),
        "fmt": "json",
        "pageNumber": str(page_number),
        "pageSize": str(min(page_size, 250)),
    }
    if cross_type:
        params["crossType"] = cross_type
    if cross_manufacturer:
        params["crossmanufacturer"] = cross_manufacturer
    if cross_rohs:
        params["crossRohs"] = cross_rohs
    if part_status:
        params["partStatus"] = part_status
    if best_cross_only == "true":
        params["bestCrossOnly"] = "true"

    data = _api_get("xref", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    # Parse the response
    try:
        result = data.get("Result", {})
        cross_data_list = result.get("CrossData", [])
        if isinstance(cross_data_list, dict):
            cross_data_list = [cross_data_list]

        output = []
        for cd in cross_data_list:
            crosses_dto = cd.get("CrossDto", [])
            if isinstance(crosses_dto, dict):
                crosses_dto = [crosses_dto]

            crosses = []
            for x in crosses_dto:
                crosses.append({
                    "cross_com_id": x.get("CrossID"),
                    "cross_part_number": x.get("CrossPartNumber"),
                    "cross_manufacturer": x.get("CrossManufacturer"),
                    "cross_lifecycle": x.get("CrossLifecycle"),
                    "cross_description": x.get("CrossDescription"),
                    "cross_rohs": x.get("CrossRoHSStatus"),
                    "cross_datasheet": x.get("CrossDatasheet"),
                    "cross_pricing": x.get("CrossPricingData"),
                    "cross_type": x.get("Type"),
                    "comment": x.get("Comment"),
                    "form_fit_function": x.get("FormFitFunction"),
                    "replacement_source": x.get("ReplacementSource"),
                    "original_com_id": x.get("ComID"),
                    "original_part_number": x.get("PartNumber"),
                    "original_manufacturer": x.get("Manufacturer"),
                    "original_lifecycle": x.get("Lifecycle"),
                })

            output.append({
                "requested_part": cd.get("ReqPartNumber", ""),
                "requested_com_id": cd.get("ReqComId", ""),
                "requested_manufacturer": cd.get("ReqManufacturer", ""),
                "cross_count": cd.get("CrossCount", len(crosses)),
                "crosses": crosses,
            })

        return json.dumps({
            "status": data.get("Status", {}),
            "total_items": data.get("TotalItems", ""),
            "results": output,
        }, indent=2)
    except Exception:
        return json.dumps(data, indent=2)


@mcp.tool()
def find_alternates_by_part_number(part_number: str, manufacturer: str = "", cross_type: str = "", best_cross_only: str = "false") -> str:
    """
    Convenience tool: find alternate/replacement parts given a part number.
    Uses the xref endpoint directly with part number search.

    Args:
        part_number: The manufacturer part number to find alternates for.
        manufacturer: Optional manufacturer name for precise matching.
        cross_type: Optional cross type filter (A, B, C, D, S, SF).
        best_cross_only: "true" to return only best cross. Default "false".
    """
    err = _login_guard()
    if err:
        return err

    entry = {"partNumber": part_number.strip()}
    if manufacturer:
        entry["manufacturer"] = manufacturer.strip()

    params = {
        "parts": json.dumps([entry]),
        "fmt": "json",
        "pageSize": "50",
    }
    if cross_type:
        params["crossType"] = cross_type
    if best_cross_only == "true":
        params["bestCrossOnly"] = "true"

    data = _api_get("xref", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        result = data.get("Result", {})
        cross_data_list = result.get("CrossData", [])
        if isinstance(cross_data_list, dict):
            cross_data_list = [cross_data_list]

        output = []
        for cd in cross_data_list:
            crosses_dto = cd.get("CrossDto", [])
            if isinstance(crosses_dto, dict):
                crosses_dto = [crosses_dto]

            crosses = []
            for x in crosses_dto:
                crosses.append({
                    "cross_com_id": x.get("CrossID"),
                    "cross_part_number": x.get("CrossPartNumber"),
                    "cross_manufacturer": x.get("CrossManufacturer"),
                    "cross_lifecycle": x.get("CrossLifecycle"),
                    "cross_description": x.get("CrossDescription"),
                    "cross_rohs": x.get("CrossRoHSStatus"),
                    "cross_type": x.get("Type"),
                    "comment": x.get("Comment"),
                    "cross_pricing": x.get("CrossPricingData"),
                })

            output.append({
                "requested_part": cd.get("ReqPartNumber", part_number),
                "cross_count": cd.get("CrossCount", len(crosses)),
                "crosses": crosses,
            })

        return json.dumps({
            "status": data.get("Status", {}),
            "results": output,
        }, indent=2)
    except Exception:
        return json.dumps(data, indent=2)


# =============================================================================
# SERVICE 5: PARAMETRIC SEARCH
# =============================================================================

@mcp.tool()
def parametric_search(
    product_line: str,
    selected_filters: str = "",
    keyword: str = "",
    level: int = 3,
    page_number: int = 1,
    page_size: int = 50,
) -> str:
    """
    Search parts by technical/parametric criteria within a product line.
    Uses parametric/getSearchResult endpoint. For multiplier support use search_by_category.

    Filter examples:
      Single value: '[{"fetName":"Pin Count","values":[{"value":"7"}]}]'
      Range: '[{"fetName":"Maximum Output Current","values":[{"value":"40000 TO 50000"}]}]'
      Multiple values: '[{"fetName":"Typical Gate Charge @ Vgs","values":[{"value":"0.49"},{"value":"170"}]}]'
      Multiple features: '[{"fetName":"Power Supply Type","values":[{"value":"Single"}]},{"fetName":"Maximum Single Supply Voltage","values":[{"value":"3 to 4"}]}]'

    Args:
        product_line: Product line name or ID (e.g. "MOSFETs", "Laser Diodes", "Rectifiers").
        selected_filters: JSON array of filter objects (see examples above).
        keyword: Optional filter on part number, description, or manufacturer name.
        level: Taxonomy level - 1=main category, 2=sub category, 3=product line (default).
        page_number: Page number (default 1).
        page_size: Results per page (default 50, max 500).
    """
    err = _login_guard()
    if err:
        return err

    params = {
        "plName": product_line,
        "level": str(level),
        "fmt": "json",
        "pageNumber": str(page_number),
        "pageSize": str(min(page_size, 500)),
    }
    if selected_filters:
        params["selectedFilters"] = selected_filters
    if keyword:
        params["keyword"] = keyword

    data = _api_get("parametric/getSearchResult", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        result = data.get("Result", {})
        total_items = result.get("TotalItems", "")
        parts_list = result.get("PartsList", {}).get("Part", [])
        if isinstance(parts_list, dict):
            parts_list = [parts_list]

        parts = []
        for part in parts_list:
            features = part.get("Features", {}).get("Feature", [])
            if isinstance(features, dict):
                features = [features]
            feature_dict = {}
            for f in features:
                name = f.get("FeatureName", "")
                value = f.get("FeatureValue", "")
                unit = f.get("FeatureUnit", "")
                feature_dict[name] = f"{value} {unit}".strip() if unit else value
            parts.append(feature_dict)

        return json.dumps({
            "status": data.get("Status", {}),
            "total_items": total_items,
            "count": len(parts),
            "parts": parts,
        }, indent=2)
    except Exception:
        return json.dumps(data, indent=2)


@mcp.tool()
def get_product_line_features(
    product_line: str,
    selected_filters: str = "",
    keyword: str = "",
    level: int = 3,
) -> str:
    """
    Get all available parametric features and their possible values for a product line.
    Useful for discovering what filters are available before running parametric_search.
    Uses parametric/getParametricFeatures (enhanced, with multiplier support).

    Args:
        product_line: Product line name or ID (e.g. "MOSFETs", "Rectifiers").
        selected_filters: Optional JSON filters to narrow feature values.
        keyword: Optional keyword filter.
        level: Taxonomy level - 1=main category, 2=sub category, 3=product line (default).
    """
    err = _login_guard()
    if err:
        return err

    params = {
        "plName": product_line,
        "level": str(level),
        "fmt": "json",
    }
    if selected_filters:
        params["selectedFilters"] = selected_filters
    if keyword:
        params["keyword"] = keyword

    data = _api_get("parametric/getParametricFeatures", params)
    if "error" in data:
        # Fallback to basic features endpoint
        data = _api_get("parametric/getPlFeatures", params)
    if "error" in data:
        return json.dumps(data, indent=2)
    return json.dumps(data, indent=2)


# =============================================================================
# SERVICE 6: BOM MANAGEMENT / RISK ANALYSIS
# =============================================================================

@mcp.tool()
def bom_risk_analysis(part_numbers: str) -> str:
    """
    Analyze a Bill of Materials (BOM) for lifecycle risk, obsolescence,
    compliance issues, and supply chain risk. Accepts multiple part numbers.

    Args:
        part_numbers: Comma-separated list of part numbers to analyze as a BOM
                      (e.g. "LM358N,NE555P,LM7805CT,SN74HC00N").
    """
    err = _login_guard()
    if err:
        return err

    pn_list = [pn.strip() for pn in part_numbers.split(",") if pn.strip()]
    if not pn_list:
        return json.dumps({"error": "No part numbers provided."})

    # Try dedicated BOM endpoint
    bom_body = {"partNumbers": pn_list}
    data = _api_post("bomRiskAnalysis", json_body=bom_body)
    if "error" not in data:
        return json.dumps(data, indent=2)

    # Fallback: batch search using listPartSearch
    search_entries = [{"partNumber": pn} for pn in pn_list]
    params = {"partNumber": json.dumps(search_entries), "mode": "exact", "fmt": "json"}
    search_data = _api_get("listPartSearch", params)

    bom_results = []
    if "error" not in search_data:
        result = search_data.get("Result", {})
        # Handle response - could be single PartData or nested
        part_data = result.get("PartData", result) if isinstance(result, dict) else {}
        part_list = part_data.get("PartList", {}).get("PartDto", []) if isinstance(part_data, dict) else []
        if isinstance(part_list, dict):
            part_list = [part_list]

        found_parts = {}
        for p in part_list:
            pn_key = p.get("PartNumber", "").upper()
            if pn_key not in found_parts:
                found_parts[pn_key] = p

        for pn in pn_list:
            p = found_parts.get(pn.upper())
            if p:
                lifecycle = p.get("Lifecycle", "Unknown")
                risk = "low"
                if lifecycle in ["EOL", "Obsolete"]:
                    risk = "critical"
                elif lifecycle in ["NRND", "Not Recommended"]:
                    risk = "high"
                elif lifecycle in ["Last Time Buy", "LTB"]:
                    risk = "high"
                elif lifecycle == "Unknown":
                    risk = "medium"

                bom_results.append({
                    "part_number": p.get("PartNumber", pn),
                    "com_id": p.get("ComID"),
                    "manufacturer": p.get("Manufacturer"),
                    "lifecycle": lifecycle,
                    "rohs": p.get("RoHS", ""),
                    "yeol": p.get("YEOL", ""),
                    "resilience_rating": p.get("ResilienceRating"),
                    "risk_level": risk,
                    "status": "found",
                })
            else:
                bom_results.append({"part_number": pn, "status": "not_found", "risk_level": "unknown"})
    else:
        # Individual fallback search
        for pn in pn_list:
            params = {"partNumber": pn, "fmt": "json", "pageSize": "5"}
            sd = _api_get("partsearch", params)
            part_info = {"part_number": pn, "status": "not_found", "risk_level": "unknown"}
            try:
                parts = sd.get("Result", [])
                if isinstance(parts, dict):
                    parts = [parts]
                if parts:
                    p = parts[0]
                    lifecycle = p.get("Lifecycle", "Unknown")
                    risk = "low"
                    if lifecycle in ["EOL", "Obsolete"]:
                        risk = "critical"
                    elif lifecycle in ["NRND", "Not Recommended"]:
                        risk = "high"
                    elif lifecycle in ["Last Time Buy", "LTB"]:
                        risk = "high"
                    elif lifecycle == "Unknown":
                        risk = "medium"
                    part_info = {
                        "part_number": p.get("PartNumber", pn),
                        "com_id": p.get("ComID"),
                        "manufacturer": p.get("Manufacturer"),
                        "lifecycle": lifecycle,
                        "rohs": p.get("RoHS", ""),
                        "yeol": p.get("YEOL", ""),
                        "resilience_rating": p.get("ResilienceRating"),
                        "risk_level": risk,
                        "status": "found",
                    }
            except Exception:
                pass
            bom_results.append(part_info)

    # Summarize risk
    risk_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
    for item in bom_results:
        risk_summary[item.get("risk_level", "unknown")] += 1

    return json.dumps({
        "bom_size": len(pn_list),
        "parts_found": sum(1 for r in bom_results if r["status"] == "found"),
        "risk_summary": risk_summary,
        "parts": bom_results,
    }, indent=2)


# =============================================================================
# SERVICE 7: ENVIRONMENTAL / COMPLIANCE DATA
# =============================================================================

@mcp.tool()
def get_compliance_data(com_id: str) -> str:
    """
    Get environmental and regulatory compliance data for a component.
    Returns RoHS status, REACH SVHC compliance, Conflict Minerals (CMRT),
    China RoHS, Prop 65, PFAS status, and other regulatory data.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try dedicated compliance endpoint
    data = _api_get("environmentalData", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "compliance": data}, indent=2)

    # Fallback: extract from partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        compliance = {}
        for key in [
            "ComplianceData", "RoHSData", "REACHData", "ConflictMinerals",
            "EnvironmentalData", "ROHSStatus", "HazardousSubstances",
            "ChinaRoHS", "Prop65", "PFASStatus", "ELVCompliance",
        ]:
            if key in results and results[key]:
                compliance[key] = results[key]

        if compliance:
            return json.dumps({"com_id": com_id, "compliance": compliance}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


@mcp.tool()
def get_rohs_status(com_id: str) -> str:
    """
    Quick lookup of RoHS compliance status for a part.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        rohs = results.get("ROHSStatus", results.get("RoHSStatus", "Unknown"))
        return json.dumps({
            "com_id": com_id,
            "rohs_status": rohs,
            "part_number": results.get("PartNumber", ""),
            "manufacturer": results.get("ManufacturerName", ""),
        }, indent=2)
    except Exception:
        return json.dumps(data, indent=2)


@mcp.tool()
def get_reach_status(com_id: str) -> str:
    """
    Get REACH SVHC (Substances of Very High Concern) compliance data for a part.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}
    data = _api_get("reachData", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "reach_data": data}, indent=2)

    # Fallback: partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        reach = {}
        for key in ["REACHData", "REACHStatus", "SVHCList"]:
            if key in results and results[key]:
                reach[key] = results[key]
        if reach:
            return json.dumps({"com_id": com_id, "reach_data": reach}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


@mcp.tool()
def get_conflict_minerals(com_id: str) -> str:
    """
    Get Conflict Minerals (CMRT) data for a component.
    Shows presence of tin, tantalum, tungsten, gold (3TG) and sourcing info.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}
    data = _api_get("conflictMinerals", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "conflict_minerals": data}, indent=2)

    # Fallback: partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        cm = {}
        for key in ["ConflictMinerals", "CMRTData", "ConflictMineralStatus"]:
            if key in results and results[key]:
                cm[key] = results[key]
        if cm:
            return json.dumps({"com_id": com_id, "conflict_minerals": cm}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


# =============================================================================
# SERVICE 8: MARKET AVAILABILITY / INVENTORY
# =============================================================================

@mcp.tool()
def get_market_availability(com_id: str) -> str:
    """
    Get real-time market availability and distributor inventory data for a component.
    Returns stock levels from authorized distributors, lead times, MOQ,
    and distributor pricing.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try dedicated market availability endpoint
    data = _api_get("marketAvailability", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "market_availability": data}, indent=2)

    # Try inventory endpoint
    data = _api_get("inventoryData", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "inventory": data}, indent=2)

    # Fallback: extract from partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        inventory = {}
        for key in [
            "InventoryData", "MarketAvailability", "DistributorData",
            "StockData", "SupplyChainData", "DistributorInventory",
        ]:
            if key in results and results[key]:
                inventory[key] = results[key]
        if inventory:
            return json.dumps({"com_id": com_id, "market_availability": inventory}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


# =============================================================================
# SERVICE 9: PCN / EOL (PRODUCT CHANGE NOTIFICATIONS)
# =============================================================================

@mcp.tool()
def get_pcn_data(
    com_id: str = "",
    part_number: str = "",
    pcn_number: str = "",
    page_number: int = 1,
    page_size: int = 50,
) -> str:
    """
    Search Product Change Notifications (PCN) by ComID, part number, or PCN number.
    Returns manufacturer-released PCNs including type of change, affected parts,
    last buy/ship dates, and source documents.

    Args:
        com_id: SE ComID(s), comma-separated (e.g. "35829517" or "35829517,68510871").
        part_number: Part number(s), comma-separated (e.g. "bav99" or "bav99,bav99wt").
        pcn_number: Supplier PCN number to search for (e.g. "PCN17004A").
        page_number: Page number (default 1).
        page_size: Results per page (default 50, max 250).
    """
    err = _login_guard()
    if err:
        return err

    params = {
        "fmt": "json",
        "pageNumber": str(page_number),
        "pageSize": str(min(page_size, 250)),
    }

    if com_id:
        params["comIds"] = com_id.strip()
    elif part_number:
        params["partNumber"] = part_number.strip()
    elif pcn_number:
        params["pcns"] = json.dumps([{"pcnNum": pcn_number.strip()}])
    else:
        return json.dumps({"error": "Provide com_id, part_number, or pcn_number."})

    data = _api_get("pcn", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    # Parse PCN response
    try:
        result = data.get("Result", {})
        pcn_data = result.get("PCNData", result)
        if isinstance(pcn_data, dict):
            pcn_data = [pcn_data]

        output = []
        for pd in pcn_data:
            pcn_dtos = pd.get("PCNDto", [])
            if isinstance(pcn_dtos, dict):
                pcn_dtos = [pcn_dtos]

            pcns = []
            for p in pcn_dtos:
                pcns.append({
                    "pcn_number": p.get("PCNNumber"),
                    "manufacturer": p.get("Manufacturer"),
                    "description_of_change": p.get("DescriptionOfChange"),
                    "type_of_change": p.get("TypeOfChange"),
                    "affected_product": p.get("AffectedProductName"),
                    "source": p.get("Source"),
                    "notification_date": p.get("NotificationDate"),
                    "effective_date": p.get("EffectiveDate"),
                    "last_time_buy_date": p.get("LastTimeBuyDate"),
                    "last_ship_date": p.get("LastShipDate"),
                })

            output.append({
                "requested_part": pd.get("ReqPartNumber", ""),
                "requested_com_id": pd.get("ReqComId", ""),
                "pcn_count": len(pcns),
                "pcns": pcns,
            })

        return json.dumps({
            "status": data.get("Status", {}),
            "results": output,
        }, indent=2)
    except Exception:
        return json.dumps(data, indent=2)


# =============================================================================
# SERVICE 10: OBSOLESCENCE FORECAST (YTEOL)
# =============================================================================

@mcp.tool()
def get_yteol_forecast(com_id: str) -> str:
    """
    Get Years To End Of Life (YTEOL) obsolescence forecast for a component.
    Provides SiliconExpert's proprietary prediction of how many years until
    the part is expected to reach End Of Life status.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try dedicated YTEOL endpoint
    for endpoint in ["yteolData", "obsolescenceForecast", "lifecycleForecast"]:
        data = _api_get(endpoint, params)
        if "error" not in data:
            return json.dumps({"com_id": com_id, "endpoint": endpoint, "forecast": data}, indent=2)

    # Fallback: extract from partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        forecast = {}
        for key in [
            "YTEOLData", "YTEOL", "YearsToEOL", "ObsolescenceForecast",
            "LifecycleForecast", "LifecycleRiskScore",
        ]:
            if key in results and results[key]:
                forecast[key] = results[key]
        if forecast:
            return json.dumps({"com_id": com_id, "obsolescence_forecast": forecast}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


# =============================================================================
# SERVICE 11: DATASHEET
# =============================================================================

@mcp.tool()
def get_datasheets(com_id: str) -> str:
    """
    Get datasheet URLs and technical document links for a component.
    Returns links to manufacturer datasheets (PDF), application notes,
    reference designs, and errata documents.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try dedicated datasheet endpoint
    for endpoint in ["datasheetData", "documents", "datasheets"]:
        data = _api_get(endpoint, params)
        if "error" not in data:
            return json.dumps({"com_id": com_id, "endpoint": endpoint, "datasheets": data}, indent=2)

    # Fallback: extract from partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        docs = {}
        for key in [
            "DatasheetData", "DatasheetUrl", "Documents", "DocumentLinks",
            "ApplicationNotes", "ReferenceDesigns", "DatasheetHistory",
        ]:
            if key in results and results[key]:
                docs[key] = results[key]
        if docs:
            return json.dumps({"com_id": com_id, "datasheets": docs}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


# =============================================================================
# SERVICE 12: MANUFACTURER DATA
# =============================================================================

@mcp.tool()
def get_manufacturer_data(manufacturer_name: str = "", manufacturer_id: str = "") -> str:
    """
    Get manufacturer/supplier profile information including URL, phone, address,
    DUNS number, CAGE code, business type, HQ, total parts count, and acquisitions.
    Uses the supplierProfile endpoint.

    Args:
        manufacturer_name: Manufacturer/supplier name to look up.
        manufacturer_id: SE Manufacturer ID (alternative to name).
    """
    err = _login_guard()
    if err:
        return err

    params = {"fmt": "json"}
    if manufacturer_id:
        params["manufacturerId"] = manufacturer_id.strip()
    elif manufacturer_name:
        params["manufacturerName"] = manufacturer_name.strip()
    else:
        return json.dumps({"error": "Provide manufacturer_name or manufacturer_id."})

    data = _api_get("supplierProfile", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        result = data.get("Result", {})
        profile = result.get("SuppllierProfileData", result.get("SupplierProfileData", {}))
        return json.dumps({
            "status": data.get("Status", {}),
            "requested_name": result.get("ReqManName", ""),
            "requested_id": result.get("ReqManID", ""),
            "profile": profile,
        }, indent=2)
    except Exception:
        return json.dumps(data, indent=2)


@mcp.tool()
def search_manufacturer(manufacturer_name: str, page_number: int = 1, page_size: int = 100) -> str:
    """
    Search for a manufacturer/supplier by name.
    Returns matching manufacturer names and their SE IDs.
    Uses the manufacturers endpoint.

    Args:
        manufacturer_name: Manufacturer/supplier name to search for.
        page_number: Page number (default 1).
        page_size: Results per page (default 100, max 500).
    """
    err = _login_guard()
    if err:
        return err

    params = {
        "mfr": manufacturer_name.strip(),
        "fmt": "json",
        "pageNo": str(page_number),
        "pageSize": str(min(page_size, 500)),
    }

    data = _api_get("manufacturers", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        result = data.get("Result", {})
        mfr_dto = result.get("MfrDto", [])
        if isinstance(mfr_dto, dict):
            mfr_dto = [mfr_dto]
        manufacturers = []
        for m in mfr_dto:
            manufacturers.append({
                "manufacturer_name": m.get("ManufacturerName"),
                "manufacturer_id": m.get("ManufacturerID"),
            })
        return json.dumps({
            "status": data.get("Status", {}),
            "result_size": data.get("resultSize", len(manufacturers)),
            "manufacturers": manufacturers,
        }, indent=2)
    except Exception:
        return json.dumps(data, indent=2)


# =============================================================================
# SERVICE 13: CATEGORY / TAXONOMY
# =============================================================================

@mcp.tool()
def get_category_tree() -> str:
    """
    Get the full SiliconExpert product line taxonomy tree.
    Returns hierarchical categories: Type > MainCategory > SubCategory > ProductLine.
    Use this to discover valid product line names for parametric_search.
    Endpoint: parametric/getAllTaxonomy
    """
    err = _login_guard()
    if err:
        return err

    data = _api_get("parametric/getAllTaxonomy", {"fmt": "json"})
    if "error" in data:
        return json.dumps(data, indent=2)
    return json.dumps(data, indent=2)


@mcp.tool()
def search_by_category(
    product_line: str,
    level: int = 3,
    keyword: str = "",
    selected_filters: str = "",
    page_number: int = 1,
    page_size: int = 50,
) -> str:
    """
    Search parts by parametric/technical criteria within a product line.
    Uses parametric/getParametricSearchResult (enhanced, supports multipliers).

    Args:
        product_line: Product line name or ID (e.g. "MOSFETs", "Laser Diodes", "Rectifiers").
            Use level=1 for main category, level=2 for "Category@SubCategory" format.
        level: Taxonomy level - 1=main category, 2=sub category, 3=product line (default).
        keyword: Optional filter on part number, description, or manufacturer.
        selected_filters: JSON array of filters. Examples:
            '[{"fetName":"Maximum Output Current","values":[{"value":"40000 TO 50000","multiplier":"m"}]}]'
            '[{"fetName":"Power Supply Type","values":[{"value":"Single"}]}]'
        page_number: Page number (default 1).
        page_size: Results per page (default 50, max 500).
    """
    err = _login_guard()
    if err:
        return err

    params = {
        "plName": product_line,
        "level": str(level),
        "fmt": "json",
        "pageNumber": str(page_number),
        "pageSize": str(min(page_size, 500)),
    }
    if keyword:
        params["keyword"] = keyword
    if selected_filters:
        params["selectedFilters"] = selected_filters

    data = _api_get("parametric/getParametricSearchResult", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    # Parse the response
    try:
        result = data.get("Result", {})
        total_items = result.get("TotalItems", "")
        parts_list = result.get("PartsList", {}).get("Part", [])
        if isinstance(parts_list, dict):
            parts_list = [parts_list]

        parts = []
        for part in parts_list:
            features = part.get("Features", {}).get("Feature", [])
            if isinstance(features, dict):
                features = [features]
            feature_dict = {}
            for f in features:
                name = f.get("FeatureName", "")
                value = f.get("FeatureValue", "")
                unit = f.get("FeatureUnit", "")
                feature_dict[name] = f"{value} {unit}".strip() if unit else value
            parts.append(feature_dict)

        return json.dumps({
            "status": data.get("Status", {}),
            "total_items": total_items,
            "count": len(parts),
            "parts": parts,
        }, indent=2)
    except Exception:
        return json.dumps(data, indent=2)


# =============================================================================
# SERVICE 14: PRICING
# =============================================================================

@mcp.tool()
def get_pricing(com_id: str) -> str:
    """
    Get detailed pricing data for a component by ComID.
    Returns price breaks at various quantity levels (100, 1K, 10K),
    distributor-specific pricing, and minimum prices.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try dedicated pricing endpoint
    data = _api_get("pricingData", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "pricing": data}, indent=2)

    # Fallback: extract from partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data["Results"]["ResultDto"]
    except (KeyError, TypeError) as e:
        return json.dumps({"error": f"Unexpected response structure: {e}", "raw": str(data)[:500]})

    # Process PriceBreaksData
    prices_break = [-1.0, -1.0, -1.0]
    price_breaks_dto = None

    try:
        price_breaks_data = results["PriceBreaksData"]
        price_breaks_dto = price_breaks_data["PriceBreaksDto"]
    except (KeyError, TypeError):
        try:
            pricing_data = results["PricingData"]
            minimum_price = pricing_data["MinimumPrice"]
            if minimum_price:
                p = float(minimum_price)
                return json.dumps({
                    "com_id": com_id, "source": "MinimumPrice",
                    "price_100": p, "price_1k": p, "price_10k": p,
                }, indent=2)
        except (KeyError, TypeError, ValueError):
            pass
        return json.dumps({"error": "No pricing data available.", "com_id": com_id})

    if isinstance(price_breaks_dto, list):
        clean_data = [{**item, "PriceBreaK": int(item["PriceBreaK"])} for item in price_breaks_dto]
        sorted_data = sorted(clean_data, key=lambda x: x["PriceBreaK"])
    else:
        sorted_data = [{**price_breaks_dto, "PriceBreaK": int(price_breaks_dto["PriceBreaK"])}]

    price_100_flag = price_1000_flag = price_10000_flag = False

    for child in sorted_data:
        pb = child["PriceBreaK"]
        if (50 <= pb <= 100) or (not price_100_flag and 100 < pb < 500):
            prices_break[0] = float(child["MinPrice"]) if prices_break[0] < 0 else min(prices_break[0], float(child["MinPrice"]))
            price_100_flag = True
        if (500 <= pb <= 1000) or (not price_1000_flag and 1000 < pb <= 5000):
            prices_break[1] = float(child["MinPrice"]) if prices_break[1] < 0 else min(prices_break[1], float(child["MinPrice"]))
            price_1000_flag = True
        if (5000 <= pb <= 10000) or (not price_10000_flag and 10000 < pb <= 50000):
            prices_break[2] = float(child["MinPrice"]) if prices_break[2] < 0 else min(prices_break[2], float(child["MinPrice"]))
            price_10000_flag = True
        if pb > 50000:
            break

    # Fill missing price breaks with best available
    if price_100_flag and not price_1000_flag and not price_10000_flag:
        prices_break[1] = prices_break[0]
        prices_break[2] = prices_break[0]
    elif not price_100_flag and price_1000_flag and not price_10000_flag:
        prices_break[0] = prices_break[1]
        prices_break[2] = prices_break[1]
    elif not price_100_flag and not price_1000_flag and price_10000_flag:
        prices_break[0] = prices_break[2]
        prices_break[1] = prices_break[2]
    elif price_100_flag and price_1000_flag and not price_10000_flag:
        prices_break[1] = min(prices_break[0], prices_break[1])
        prices_break[2] = min(prices_break[0], prices_break[1])
    elif price_100_flag and not price_1000_flag and price_10000_flag:
        prices_break[2] = min(prices_break[0], prices_break[2])
        prices_break[1] = min(prices_break[0], prices_break[2])
    elif not price_100_flag and price_1000_flag and price_10000_flag:
        prices_break[2] = min(prices_break[1], prices_break[2])
        prices_break[0] = min(prices_break[1], prices_break[2])
    elif price_100_flag and price_1000_flag and price_10000_flag:
        prices_break[1] = min(prices_break[0], prices_break[1])
        prices_break[2] = min(prices_break[1], prices_break[2])

    return json.dumps({
        "com_id": com_id,
        "source": "PriceBreaks",
        "price_100": prices_break[0] if prices_break[0] >= 0 else None,
        "price_1k": prices_break[1] if prices_break[1] >= 0 else None,
        "price_10k": prices_break[2] if prices_break[2] >= 0 else None,
    }, indent=2)


# =============================================================================
# SERVICE 15: PACKAGE / MOUNTING DATA
# =============================================================================

@mcp.tool()
def get_package_data(com_id: str) -> str:
    """
    Get packaging, mounting, and physical specification data for a component.
    Returns package type, pin count, dimensions, weight, mounting style,
    moisture sensitivity level (MSL), and thermal data.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try dedicated package endpoint
    data = _api_get("packageData", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "package_data": data}, indent=2)

    # Fallback: extract from partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        package = {}
        for key in [
            "PackagingData", "PackageData", "MountingData", "PhysicalData",
            "PinCount", "PackageType", "MSLData", "ThermalData",
            "Dimensions", "Weight", "MountingStyle",
        ]:
            if key in results and results[key]:
                package[key] = results[key]
        if package:
            return json.dumps({"com_id": com_id, "package_data": package}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


# =============================================================================
# SERVICE 16: PART RISK ASSESSMENT
# =============================================================================

@mcp.tool()
def get_part_risk(com_id: str) -> str:
    """
    Get comprehensive risk assessment for a component including:
    - Obsolescence risk score
    - Single-source / multi-source risk
    - Lifecycle forecast
    - Supply chain risk indicators
    - Geographic risk (country of origin)
    - Regulatory risk

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try dedicated risk endpoints
    for endpoint in ["partRisk", "riskData", "obsolescenceRisk"]:
        data = _api_get(endpoint, params)
        if "error" not in data:
            return json.dumps({"com_id": com_id, "endpoint": endpoint, "risk": data}, indent=2)

    # Fallback: extract from partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        risk = {}
        for key in [
            "RiskData", "ObsolescenceRisk", "LifecycleForecast", "YearsToEOL",
            "SingleSourceRisk", "SupplyChainRisk", "MultiSourcingData",
            "YTEOL", "RiskScore", "GeoRisk",
        ]:
            if key in results and results[key]:
                risk[key] = results[key]
        if risk:
            return json.dumps({"com_id": com_id, "risk_assessment": risk}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


# =============================================================================
# ADDITIONAL TOOLS: LIFECYCLE & TECHNICAL SPECS
# =============================================================================

@mcp.tool()
def get_part_lifecycle(part_number: str, manufacturer: str = "") -> str:
    """
    Quick lookup of a part's lifecycle status (Active, EOL, NRND, LTB, etc.)
    and YEOL (Years to End Of Life) forecast.

    Args:
        part_number: The manufacturer part number.
        manufacturer: Optional manufacturer name for precise matching.
    """
    err = _login_guard()
    if err:
        return err

    params = {"partNumber": part_number.strip(), "fmt": "json", "pageSize": "10"}
    if manufacturer:
        params["mfr"] = manufacturer.strip()

    data = _api_get("partsearch", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    results = data.get("Result", [])
    if isinstance(results, dict):
        results = [results]

    lifecycles = []
    for item in results[:10]:
        if isinstance(item, dict):
            lifecycles.append({
                "part_number": item.get("PartNumber", ""),
                "manufacturer": item.get("Manufacturer", ""),
                "lifecycle": item.get("Lifecycle", "Unknown"),
                "yeol": item.get("YEOL", ""),
                "match_rating": item.get("MatchRating", ""),
                "com_id": item.get("ComID", ""),
                "rohs": item.get("RoHS", ""),
            })

    return json.dumps({
        "query": part_number,
        "results_count": len(lifecycles),
        "results": lifecycles,
    }, indent=2)


@mcp.tool()
def get_technical_specs(com_id: str) -> str:
    """
    Get technical/parametric specifications for a component.
    Returns electrical characteristics (voltage, current, power, frequency),
    physical dimensions, temperature ratings, and other parametric data.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try dedicated parametric/technical endpoints
    for endpoint in ["parametricData", "technicalSpecifications", "technicalData"]:
        data = _api_get(endpoint, params)
        if "error" not in data:
            return json.dumps({"com_id": com_id, "endpoint": endpoint, "specs": data}, indent=2)

    # Fallback: extract from partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        tech = {}
        for key in [
            "ParametricData", "TechnicalData", "ParametricDto",
            "TechnicalSpecifications", "ElectricalCharacteristics",
            "PhysicalDimensions", "ThermalCharacteristics",
        ]:
            if key in results and results[key]:
                tech[key] = results[key]
        if tech:
            return json.dumps({"com_id": com_id, "technical_specs": tech}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


# =============================================================================
# ADDITIONAL TOOLS: MULTI-SOURCE & COUNTRY OF ORIGIN
# =============================================================================

@mcp.tool()
def get_multi_source_data(com_id: str) -> str:
    """
    Get multi-sourcing information for a component.
    Shows how many manufacturers produce this part or equivalents,
    helping assess single-source risk.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try dedicated multi-source endpoint
    data = _api_get("multiSourceData", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "multi_source": data}, indent=2)

    # Fallback: combine cross-reference + part detail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        ms = {}
        for key in ["MultiSourcingData", "CrossReferenceData", "AlternateManufacturers"]:
            if key in results and results[key]:
                ms[key] = results[key]
        if ms:
            return json.dumps({"com_id": com_id, "multi_source": ms}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


@mcp.tool()
def get_country_of_origin(com_ids: str) -> str:
    """
    Get GeoRisk score, country of origin, and manufacturing site information.
    Returns front-end/back-end manufacturing sites with risk grading.
    Uses POST to SupplyChain/GEORisk endpoint (Platinum tier).

    Args:
        com_ids: Comma-separated ComIDs (e.g. "17686077,17227066").
    """
    err = _login_guard()
    if err:
        return err

    id_list = [int(c.strip()) for c in com_ids.split(",") if c.strip()]
    if not id_list:
        return json.dumps({"error": "No ComIDs provided."})

    # POST to SupplyChain/GEORisk
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
        "Connection": "keep-alive",
    }
    try:
        res = _session.post(
            "https://api.siliconexpert.com/ProductAPI/SupplyChain/GEORisk",
            json={"COMIDs": id_list},
            headers=headers,
            timeout=60,
        )
        if res.status_code != 200:
            return json.dumps({"error": f"Status {res.status_code}: {res.text[:500]}"})
        data = res.json()
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({"error": f"GeoRisk request failed: {e}"})


@mcp.tool()
def get_supply_chain_events(com_ids: str) -> str:
    """
    Get supply chain events impacting components (floods, earthquakes, pandemics, etc.).
    Returns event timelines with impact status and threat levels.
    Uses POST to SupplyChain/Events endpoint (Platinum tier).

    Args:
        com_ids: Comma-separated ComIDs (e.g. "17686077,17227066").
    """
    err = _login_guard()
    if err:
        return err

    id_list = [int(c.strip()) for c in com_ids.split(",") if c.strip()]
    if not id_list:
        return json.dumps({"error": "No ComIDs provided."})

    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
        "Connection": "keep-alive",
    }
    try:
        res = _session.post(
            "https://api.siliconexpert.com/ProductAPI/SupplyChain/Events",
            json={"COMIDs": id_list},
            headers=headers,
            timeout=60,
        )
        if res.status_code != 200:
            return json.dumps({"error": f"Status {res.status_code}: {res.text[:500]}"})
        data = res.json()
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Events request failed: {e}"})


# =============================================================================
# ADDITIONAL TOOLS: EXPORT CONTROL & QUALITY
# =============================================================================

@mcp.tool()
def get_export_control_data(com_id: str) -> str:
    """
    Get export control classification data for a component.
    Returns ECCN (Export Control Classification Number), HTS codes,
    Schedule B codes, and ITAR status where available.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try dedicated export control endpoint
    data = _api_get("exportControlData", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "export_control": data}, indent=2)

    # Fallback: partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        ec = {}
        for key in ["ExportControlData", "ECCN", "HTSCode", "ScheduleB", "ITARStatus"]:
            if key in results and results[key]:
                ec[key] = results[key]
        if ec:
            return json.dumps({"com_id": com_id, "export_control": ec}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


@mcp.tool()
def get_quality_data(com_id: str) -> str:
    """
    Get quality and reliability data for a component.
    Returns qualification standards (AEC-Q100/Q200, MIL-STD),
    failure rate data, MTBF, and quality certifications.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try dedicated quality endpoint
    data = _api_get("qualityData", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "quality": data}, indent=2)

    # Fallback: partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        quality = {}
        for key in [
            "QualityData", "QualificationStandards", "AECQualification",
            "MilitaryQualification", "FailureRate", "MTBF", "ReliabilityData",
        ]:
            if key in results and results[key]:
                quality[key] = results[key]
        if quality:
            return json.dumps({"com_id": com_id, "quality": quality}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


# =============================================================================
# ADDITIONAL TOOLS: PART COMPARISON & DESCRIPTION SEARCH
# =============================================================================

@mcp.tool()
def compare_parts(com_ids: str) -> str:
    """
    Compare multiple parts side-by-side by fetching full details for each.
    Useful for evaluating alternatives during component selection.

    Args:
        com_ids: Comma-separated ComIDs to compare (e.g. "12345,67890,11111").
    """
    err = _login_guard()
    if err:
        return err

    ids = [c.strip() for c in com_ids.split(",") if c.strip()]
    if len(ids) < 2:
        return json.dumps({"error": "Provide at least 2 ComIDs to compare."})

    comparison = []
    for cid in ids:
        params = {"comIds": cid}
        data = _api_get("partDetail", params)
        if "error" not in data:
            try:
                result = data.get("Results", {}).get("ResultDto", {})
                comparison.append({
                    "com_id": cid,
                    "part_number": result.get("PartNumber", ""),
                    "manufacturer": result.get("ManufacturerName", ""),
                    "lifecycle": result.get("Lifecycle", ""),
                    "rohs": result.get("ROHSStatus", ""),
                    "description": result.get("Description", ""),
                    "package": result.get("PackageType", result.get("PackagingData", "")),
                    "full_data": result,
                })
            except Exception:
                comparison.append({"com_id": cid, "data": data})
        else:
            comparison.append({"com_id": cid, "error": data.get("error")})

    return json.dumps({"comparison_count": len(comparison), "parts": comparison}, indent=2)


@mcp.tool()
def search_by_description(description: str, part_number: str = "", operation: str = "OR") -> str:
    """
    Search for parts using a text description or keyword.
    Uses the partsearch endpoint with the description parameter.
    Can combine with part_number for combined search.

    Args:
        description: Free-text description keyword (e.g. "Diode Switching", "100uF capacitor").
        part_number: Optional part number to combine with description search.
        operation: Logical operation when combining part_number and description ("OR" or "AND"). Default "OR".
    """
    err = _login_guard()
    if err:
        return err

    params = {"fmt": "json", "description": description}
    if part_number:
        params["partNumber"] = part_number
    if operation:
        params["operation"] = operation

    data = _api_get("partsearch", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Result", [])
        if isinstance(results, dict):
            results = [results]
        parts = []
        for p in results[:50]:
            parts.append({
                "com_id": p.get("ComID"),
                "part_number": p.get("PartNumber"),
                "manufacturer": p.get("Manufacturer"),
                "lifecycle": p.get("Lifecycle"),
                "description": p.get("Description", ""),
                "rohs": p.get("RoHS", ""),
                "taxonomy_path": p.get("TaxonomyPath", ""),
                "yeol": p.get("YEOL", ""),
            })
        return json.dumps({
            "status": data.get("Status", {}),
            "total_items": data.get("TotalItems", ""),
            "query": description,
            "count": len(parts),
            "parts": parts,
        }, indent=2)
    except Exception:
        return json.dumps(data, indent=2)


# =============================================================================
# ADDITIONAL TOOLS: PART IMAGE & FULL MATERIAL DECLARATION
# =============================================================================

@mcp.tool()
def get_part_image(com_id: str) -> str:
    """
    Get image URL(s) for a component (package photo, pinout diagram).

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try image endpoint
    data = _api_get("partImage", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "images": data}, indent=2)

    # Fallback: partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        images = {}
        for key in ["ImageUrl", "PartImage", "PackageImage", "PinoutImage"]:
            if key in results and results[key]:
                images[key] = results[key]
        if images:
            return json.dumps({"com_id": com_id, "images": images}, indent=2)
    except Exception:
        pass

    return json.dumps({"com_id": com_id, "message": "No image data available."}, indent=2)


@mcp.tool()
def get_full_material_declaration(com_id: str) -> str:
    """
    Get Full Material Declaration (FMD) / material composition data for a component.
    Lists all materials and substances used in manufacturing the component,
    including weight percentages where available.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try FMD endpoint
    for endpoint in ["fmdData", "materialDeclaration", "fullMaterialDeclaration"]:
        data = _api_get(endpoint, params)
        if "error" not in data:
            return json.dumps({"com_id": com_id, "fmd": data}, indent=2)

    # Fallback: partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        fmd = {}
        for key in ["FMDData", "MaterialDeclaration", "MaterialComposition", "SubstanceList"]:
            if key in results and results[key]:
                fmd[key] = results[key]
        if fmd:
            return json.dumps({"com_id": com_id, "fmd": fmd}, indent=2)
    except Exception:
        pass

    return json.dumps({"com_id": com_id, "message": "FMD data not available for this part."}, indent=2)


# =============================================================================
# ADDITIONAL TOOLS: DISTRIBUTOR SEARCH & LEAD TIME
# =============================================================================

@mcp.tool()
def get_distributor_pricing(com_id: str, distributor: str = "") -> str:
    """
    Get distributor-specific pricing and stock data for a component.
    Optionally filter to a specific distributor.

    Args:
        com_id: The Silicon Expert ComID of the part.
        distributor: Optional distributor name to filter (e.g. "Digi-Key", "Mouser", "Arrow").
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}
    if distributor:
        params["distributor"] = distributor

    # Try distributor endpoint
    data = _api_get("distributorPricing", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "distributor_pricing": data}, indent=2)

    # Fallback: marketAvailability
    data = _api_get("marketAvailability", params)
    if "error" not in data:
        # Filter by distributor if specified
        if distributor:
            try:
                filtered = [
                    item for item in data.get("Results", data.get("Result", []))
                    if isinstance(item, dict) and distributor.lower() in str(item.get("DistributorName", "")).lower()
                ]
                return json.dumps({"com_id": com_id, "distributor": distributor, "data": filtered}, indent=2)
            except Exception:
                pass
        return json.dumps({"com_id": com_id, "distributor_pricing": data}, indent=2)

    # Final fallback: partDetail
    data = _api_get("partDetail", params)
    return json.dumps(data, indent=2)


@mcp.tool()
def get_lead_time(com_id: str) -> str:
    """
    Get manufacturing and distributor lead time data for a component.
    Returns factory lead time and distributor-reported lead times.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try lead time endpoint
    data = _api_get("leadTimeData", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "lead_time": data}, indent=2)

    # Fallback: marketAvailability often includes lead time
    data = _api_get("marketAvailability", params)
    if "error" not in data:
        return json.dumps({"com_id": com_id, "market_data_with_lead_time": data}, indent=2)

    # Fallback: partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        lt = {}
        for key in ["LeadTimeData", "FactoryLeadTime", "DistributorLeadTime"]:
            if key in results and results[key]:
                lt[key] = results[key]
        if lt:
            return json.dumps({"com_id": com_id, "lead_time": lt}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


# =============================================================================
# ADDITIONAL TOOLS: PART HISTORY & ALERTS
# =============================================================================

@mcp.tool()
def get_part_history(com_id: str) -> str:
    """
    Get historical data for a component including past lifecycle changes,
    price history, and availability trends over time.

    Args:
        com_id: The Silicon Expert ComID of the part.
    """
    err = _login_guard()
    if err:
        return err

    params = {"comIds": com_id}

    # Try history endpoint
    for endpoint in ["partHistory", "priceHistory", "lifecycleHistory"]:
        data = _api_get(endpoint, params)
        if "error" not in data:
            return json.dumps({"com_id": com_id, "endpoint": endpoint, "history": data}, indent=2)

    # Fallback: partDetail
    data = _api_get("partDetail", params)
    if "error" in data:
        return json.dumps(data, indent=2)

    try:
        results = data.get("Results", {}).get("ResultDto", {})
        history = {}
        for key in ["PartHistory", "PriceHistory", "LifecycleHistory", "AvailabilityHistory"]:
            if key in results and results[key]:
                history[key] = results[key]
        if history:
            return json.dumps({"com_id": com_id, "history": history}, indent=2)
    except Exception:
        pass

    return json.dumps(data, indent=2)


@mcp.tool()
def get_acl_parts(cpn: str = "", mpn: str = "", manufacturer: str = "", com_id: str = "", page_number: int = 1, page_size: int = 100) -> str:
    """
    Fetch the API ACL (Approved Component List) part list.
    Can filter by CPN, MPN, manufacturer, or ComID.
    Endpoint: alert/listParts

    Args:
        cpn: Optional filter by CPN number.
        mpn: Optional filter by manufacturer part number.
        manufacturer: Optional filter by manufacturer name.
        com_id: Optional filter by SE ComID.
        page_number: Page number (default 1).
        page_size: Results per page (default 100, max 500).
    """
    err = _login_guard()
    if err:
        return err

    params = {
        "fmt": "json",
        "pageNo": str(page_number),
        "perPage": str(min(page_size, 500)),
    }
    if cpn:
        params["cpn"] = cpn
    if mpn:
        params["mpn"] = mpn
    if manufacturer:
        params["man"] = manufacturer
    if com_id:
        params["comId"] = com_id

    data = _api_get("alert/listParts", params)
    if "error" in data:
        return json.dumps(data, indent=2)
    return json.dumps(data, indent=2)


@mcp.tool()
def get_acl_daily_updates(alert_types: str = "") -> str:
    """
    Get ACL parts data updates from the last 24 hours.
    Returns lifecycle changes, PCNs, RoHS updates, REACH changes, datasheets,
    supplier acquisitions, GIDEP alerts, and chemical data changes.
    Endpoint: alert/getUpdatesOfTheDay

    Args:
        alert_types: Comma-separated alert types to filter (default all). Options:
            gidep, lifecycle, pcn, datasheet, supplieracquisition, rohs, reach, chemical, rohsexemption, reachversion
    """
    err = _login_guard()
    if err:
        return err

    params = {"fmt": "json"}
    if alert_types:
        params["alertTypes"] = alert_types.strip()

    data = _api_get("alert/getUpdatesOfTheDay", params)
    if "error" in data:
        return json.dumps(data, indent=2)
    return json.dumps(data, indent=2)


@mcp.tool()
def get_acl_updates(from_date: str, to_date: str, alert_types: str = "", page_number: int = 1) -> str:
    """
    Get ACL parts data updates for a specific date range (max last 30 days).
    Returns lifecycle changes, PCNs, RoHS, REACH, datasheets, acquisitions, etc.
    Endpoint: alert/getUpdates

    Args:
        from_date: Start date in MM/dd/yyyy format (e.g. "06/20/2024").
        to_date: End date in MM/dd/yyyy format (e.g. "07/17/2024").
        alert_types: Comma-separated alert types (default all). Options:
            gidep, lifecycle, pcn, datasheet, supplieracquisition, rohs, reach, chemical, rohsexemption, reachversion
        page_number: Page number (default 1).
    """
    err = _login_guard()
    if err:
        return err

    params = {
        "fromDate": from_date,
        "toDate": to_date,
        "fmt": "json",
        "pageNo": str(page_number),
    }
    if alert_types:
        params["alertTypes"] = alert_types.strip()

    data = _api_get("alert/getUpdates", params)
    if "error" in data:
        return json.dumps(data, indent=2)
    return json.dumps(data, indent=2)


@mcp.tool()
def get_smart_pcn_list(from_date: str, to_date: str, page_number: int = 1, page_size: int = 50) -> str:
    """
    Get list of Smart PCNs based on ACL parts within a date range.
    Returns PCN IDs, number of affected parts, effective dates, and notification dates.
    Endpoint: showPCNS

    Args:
        from_date: Start date in MM/dd/yyyy format.
        to_date: End date in MM/dd/yyyy format.
        page_number: Page number (default 1).
        page_size: Results per page (default 50, max 250).
    """
    err = _login_guard()
    if err:
        return err

    params = {
        "fromDate": from_date,
        "toDate": to_date,
        "fmt": "json",
        "pageNumber": str(page_number),
        "pageSize": str(min(page_size, 250)),
    }

    data = _api_get("showPCNS", params)
    if "error" in data:
        return json.dumps(data, indent=2)
    return json.dumps(data, indent=2)


@mcp.tool()
def get_smart_pcn_content(pcn_id: str = "", from_date: str = "", to_date: str = "") -> str:
    """
    Fetch the content of a Smart PCN file. Returns as attachment/file.
    Search by PCN ID or date range.
    Endpoint: smartpcn

    Args:
        pcn_id: Smart PCN ID (from get_smart_pcn_list).
        from_date: Alternative: start date in MM/dd/yyyy format.
        to_date: Alternative: end date in MM/dd/yyyy format.
    """
    err = _login_guard()
    if err:
        return err

    params = {"fmt": "json"}
    if pcn_id:
        params["pcnID"] = pcn_id
    elif from_date and to_date:
        params["fromDate"] = from_date
        params["toDate"] = to_date
    else:
        return json.dumps({"error": "Provide pcn_id, or both from_date and to_date."})

    data = _api_get("smartpcn", params)
    if "error" in data:
        return json.dumps(data, indent=2)
    return json.dumps(data, indent=2)


# =============================================================================
# ENTRYPOINT
# =============================================================================
if __name__ == "__main__":
    mcp.run()
