# SiliconExpert MCP Server

[![GitHub stars](https://img.shields.io/github/stars/petervalencic/siliconexpert-mcp-server?style=social)](https://github.com/petervalencic/siliconexpert-mcp-server/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/petervalencic/siliconexpert-mcp-server?style=social)](https://github.com/petervalencic/siliconexpert-mcp-server/network/members)
[![GitHub contributors](https://img.shields.io/github/contributors/petervalencic/siliconexpert-mcp-server)](https://github.com/petervalencic/siliconexpert-mcp-server/graphs/contributors)
[![GitHub issues](https://img.shields.io/github/issues/petervalencic/siliconexpert-mcp-server)](https://github.com/petervalencic/siliconexpert-mcp-server/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/petervalencic/siliconexpert-mcp-server)](https://github.com/petervalencic/siliconexpert-mcp-server/pulls)
[![GitHub license](https://img.shields.io/github/license/petervalencic/siliconexpert-mcp-server)](https://github.com/petervalencic/siliconexpert-mcp-server/blob/main/LICENSE)
[![GitHub last commit](https://img.shields.io/github/last-commit/petervalencic/siliconexpert-mcp-server)](https://github.com/petervalencic/siliconexpert-mcp-server/commits/main)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

**Author:** Peter Valencic

A Model Context Protocol (MCP) server that provides full access to the [SiliconExpert](https://www.siliconexpert.com/) Direct API. This server exposes 47 tools covering all SiliconExpert API services, enabling AI assistants and MCP-compatible clients to search, analyze, and retrieve electronic component data.

---

## What is SiliconExpert?

[SiliconExpert](https://www.siliconexpert.com/) is the world's leading product lifecycle risk management platform for electronic and mechanical components. Their database contains data on over **1 billion components** including:

- **Lifecycle status** (Active, EOL, NRND, Obsolete)
- **Obsolescence forecasting** (YTEOL - Years To End Of Life)
- **Cross-references** (form-fit-function alternates from other manufacturers)
- **Parametric/technical specifications** (electrical, physical, thermal)
- **Environmental compliance** (RoHS, REACH, Conflict Minerals, PFAS)
- **Market availability** (distributor inventory, pricing, lead times)
- **Product Change Notifications** (PCNs, EOL notices)
- **Supply chain risk** (GeoRisk, events, single-source analysis)
- **Datasheets** and ECAD models
- **Resilience Rating** scoring

SiliconExpert is used by engineers, procurement teams, and supply chain professionals to manage component risk across PLM, ERP, and design tools.

- Website: https://www.siliconexpert.com/
- API Documentation: https://support.siliconexpert.com/hc/en-us/categories/27308956995469-SiliconExpert-Direct-API

---

## What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open standard that allows AI assistants to connect to external tools and data sources. This server implements the MCP standard so that any MCP-compatible client (such as Kiro, Claude Desktop, or custom agents) can interact with the SiliconExpert API through natural language.

---

## Installation

### Prerequisites

- Python 3.10 or higher
- A SiliconExpert API account (username and API key)

### 1. Clone or download this repository

```bash
git clone <repository-url>
cd siliconexpertmcp
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `mcp` - The Model Context Protocol Python SDK
- `requests` - HTTP client for API calls

### 3. Set environment variables

Set your SiliconExpert API credentials:

**Linux/macOS:**
```bash
export SE_USERNAME="your_api_username"
export SE_PASSWORD="your_api_key"
```

**Windows (Command Prompt):**
```cmd
set SE_USERNAME=your_api_username
set SE_PASSWORD=your_api_key
```

**Windows (PowerShell):**
```powershell
$env:SE_USERNAME = "your_api_username"
$env:SE_PASSWORD = "your_api_key"
```

---

## Running the Server

### Standalone (stdio transport)

```bash
python mcp_siliconexpert_server.py
```

The server communicates over stdin/stdout using the MCP protocol.

### With Kiro IDE

Add this to your `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "siliconexpert": {
      "command": "python",
      "args": ["c:/pythonProjects/siliconexpertmcp/mcp_siliconexpert_server.py"],
      "env": {
        "SE_USERNAME": "your_api_username",
        "SE_PASSWORD": "your_api_key"
      }
    }
  }
}
```

### With Claude Desktop

Add to your Claude Desktop MCP configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "siliconexpert": {
      "command": "python",
      "args": ["/path/to/mcp_siliconexpert_server.py"],
      "env": {
        "SE_USERNAME": "your_api_username",
        "SE_PASSWORD": "your_api_key"
      }
    }
  }
}
```

---

## Available Tools (47)

### Part Search
| Tool | Description |
|------|-------------|
| `login` | Authenticate with SiliconExpert API |
| `search_part` | Keyword search by part number, description, or manufacturer |
| `list_part_search` | Batch search up to 50 parts in one request |
| `search_part_by_manufacturer` | Search with manufacturer filter |
| `search_by_description` | Search by component description keywords |
| `search_cpn` | Search by ACL Custom Part Number (CPN) |

### Part Detail
| Tool | Description |
|------|-------------|
| `get_part_details_full` | Full component data by ComID |
| `get_part_details_batch` | Batch detail for multiple ComIDs |

### Cross Reference
| Tool | Description |
|------|-------------|
| `get_cross_references` | Find alternate parts (by ComID or part number) |
| `find_alternates_by_part_number` | Quick alternate search by MPN |

### Parametric Search
| Tool | Description |
|------|-------------|
| `parametric_search` | Search by technical criteria within a product line |
| `search_by_category` | Enhanced parametric search with multiplier support |
| `get_category_tree` | Get full taxonomy tree |
| `get_product_line_features` | Get available features and values for a product line |

### Compliance & Environmental
| Tool | Description |
|------|-------------|
| `get_compliance_data` | Full environmental compliance data |
| `get_rohs_status` | Quick RoHS status lookup |
| `get_reach_status` | REACH SVHC data |
| `get_conflict_minerals` | Conflict Minerals (3TG) data |
| `get_full_material_declaration` | Full Material Declaration |
| `get_ipc_export` | IPC-1752 XML export |

### Pricing & Availability
| Tool | Description |
|------|-------------|
| `get_pricing` | Price breaks at quantity levels |
| `get_market_availability` | Distributor inventory and stock |
| `get_distributor_pricing` | Distributor-specific pricing |
| `get_lead_time` | Manufacturing and distributor lead times |

### Lifecycle & Risk
| Tool | Description |
|------|-------------|
| `get_part_lifecycle` | Quick lifecycle status lookup |
| `get_yteol_forecast` | Years To End Of Life prediction |
| `get_part_risk` | Comprehensive risk assessment |
| `get_pcn_data` | Product Change Notifications |
| `bom_risk_analysis` | BOM-level risk scoring |

### Manufacturer
| Tool | Description |
|------|-------------|
| `search_manufacturer` | Search for manufacturers by name |
| `get_manufacturer_data` | Manufacturer/supplier profile |

### Supply Chain (Platinum)
| Tool | Description |
|------|-------------|
| `get_country_of_origin` | GeoRisk score and manufacturing sites |
| `get_supply_chain_events` | Supply chain disruption events |

### ACL & Alerts
| Tool | Description |
|------|-------------|
| `get_acl_parts` | Fetch ACL part list |
| `get_acl_daily_updates` | Last 24h data changes |
| `get_acl_updates` | Date-range data changes |
| `get_smart_pcn_list` | List Smart PCNs |
| `get_smart_pcn_content` | Download Smart PCN content |

### Other
| Tool | Description |
|------|-------------|
| `get_technical_specs` | Parametric specifications |
| `get_datasheets` | Datasheet URLs |
| `get_package_data` | Package and mounting info |
| `get_part_image` | Component images |
| `get_part_history` | Historical data changes |
| `get_export_control_data` | ECCN, HTS codes |
| `get_quality_data` | AEC-Q, MIL-STD qualifications |
| `get_multi_source_data` | Multi-sourcing information |
| `compare_parts` | Side-by-side part comparison |

---

## Usage Examples

### Example 1: Search for a part

Ask your AI assistant:
> "Search for BAV99 diode"

The assistant will call `search_part(part_number="BAV99")` and return matching components with lifecycle, RoHS status, manufacturer, and YEOL data.

### Example 2: Find alternates for an obsolete part

> "Find cross-references for BAV99 from ON Semiconductor, only active parts"

The assistant will call:
```
get_cross_references(part_number="BAV99", manufacturer="on semiconductor", part_status="Active")
```

### Example 3: BOM risk analysis

> "Analyze this BOM for lifecycle risk: LM358N, NE555P, LM7805CT, SN74HC00N"

The assistant will call `bom_risk_analysis(part_numbers="LM358N,NE555P,LM7805CT,SN74HC00N")` and return a risk summary with critical/high/medium/low counts.

### Example 4: Parametric search

> "Find MOSFETs with single power supply type and max supply voltage 3-4V"

The assistant will call:
```
parametric_search(
    product_line="MOSFETs",
    selected_filters='[{"fetName":"Power Supply Type","values":[{"value":"Single"}]},{"fetName":"Maximum Single Supply Voltage","values":[{"value":"3 to 4"}]}]'
)
```

### Example 5: Check compliance

> "Is part with ComID 35324203 RoHS compliant? Also check REACH status."

The assistant will call `get_rohs_status(com_id="35324203")` and `get_reach_status(com_id="35324203")`.

---

## Cross Type Reference

When using cross-reference tools, the `cross_type` field indicates compatibility level:

| Code | Meaning |
|------|---------|
| A | Pin-to-pin drop-in replacement with exact electrical features |
| A/Upgrade | Drop-in with better performance in key parameters |
| A/Downgrade | Drop-in but original has better performance |
| B | Pin-to-pin with minor electrical/package differences |
| C | Pin-to-pin with major electrical differences |
| D | Same functionality, different package/pinout |
| F | Same functionality (FPGA/CPLD) |
| S | Supplier recommended alternate |
| SF | Similar functionality with differences |

---

## API Quota Notes

- **Free (no quota):** `partsearch`, `listPartSearch`, `CPNSearch`, `manufacturers`, `supplierProfile`, `parametric/getAllTaxonomy`
- **Consumes quota:** `partDetail`, `xref`, `pcn`, `IPCExport`, parametric search results, `SupplyChain/*`
- **Platinum tier only:** `SupplyChain/GEORisk`, `SupplyChain/Events`

---

## License

This project is provided as-is for use with a valid SiliconExpert API subscription.

---

## Links

- SiliconExpert Platform: https://www.siliconexpert.com/
- SiliconExpert API Info: https://www.siliconexpert.com/products/api/
- API Documentation (requires login): https://support.siliconexpert.com/hc/en-us/categories/27308956995469-SiliconExpert-Direct-API
- MCP Protocol: https://modelcontextprotocol.io/
- MCP Python SDK: https://pypi.org/project/mcp/
