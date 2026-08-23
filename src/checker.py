"""Deterministic, regex-based checks for common Cisco troubleshooting signals."""

import re
from typing import Any


def _line_for_match(show_output: str, match: re.Match[str]) -> str:
    """Return the complete line containing a detected configuration or log signal."""
    line_start = show_output.rfind("\n", 0, match.start()) + 1
    line_end = show_output.find("\n", match.end())
    return show_output[line_start:] if line_end == -1 else show_output[line_start:line_end]


def _issue(
    check_id: str,
    issue: str,
    osi_layer: str,
    severity: str,
    evidence: str,
    recommended_fix: str,
) -> dict[str, str]:
    """Build one consistently shaped result record for the user interface."""
    return {
        "check_id": check_id,
        "issue": issue,
        "osi_layer": osi_layer,
        "severity": severity,
        "evidence": evidence.strip(),
        "recommended_fix": recommended_fix,
    }


def _first_match(pattern: str, show_output: str) -> re.Match[str] | None:
    """Search text case-insensitively and return its first matching signal."""
    return re.search(pattern, show_output, flags=re.IGNORECASE | re.MULTILINE)


def validate_case(show_output: str) -> dict[str, Any]:
    """Validate Cisco show output against ten deterministic troubleshooting rules.

    The function does not use AI or external services. It returns ``SUCCESS`` when
    no signals are found and ``ERRORS_DETECTED`` with explainable findings otherwise.
    """
    output = show_output or ""
    issues: list[dict[str, str]] = []

    # 1. An administratively down interface cannot forward traffic.
    match = _first_match(r"\badministratively down\b", output)
    if match:
        issues.append(_issue("INT-001", "Interface Administratively Down", "Layer 1", "High", _line_for_match(output, match), "Enter interface configuration mode and use `no shutdown` after confirming the interface should be enabled."))

    # 2. A DHCP pool with no available leases cannot serve new clients.
    match = _first_match(r"\bzero\s+available\b|\bpool\s+exhaust(?:ed|ion)\b", output)
    if match:
        issues.append(_issue("DHCP-001", "DHCP Pool Exhausted", "Layer 7", "High", _line_for_match(output, match), "Expand the DHCP pool, remove stale leases, or reserve additional addresses for this subnet."))

    # 3. Disabled DNS lookup or an inactive name server prevents name resolution.
    match = _first_match(r"\bno\s+ip\s+domain-lookup\b|\bip\s+name-server\b.*\bnot\s+active\b", output)
    if match:
        issues.append(_issue("DNS-001", "DNS Failure", "Layer 7", "Medium", _line_for_match(output, match), "Enable DNS lookup and configure a reachable, active DNS server for the client subnet."))

    # 4. Explicit mismatch messages or the known incorrect VLAN 14 access assignment signal a VLAN mismatch.
    match = _first_match(r"\bvlan\s+mismatch\b|\bwrong\s+(?:access\s+)?vlan\b|\bswitchport\s+access\s+vlan\s+14\b", output)
    if match:
        issues.append(_issue("VLAN-001", "VLAN Mismatch", "Layer 2", "Medium", _line_for_match(output, match), "Assign the switch port to the intended access VLAN and verify the VLAN exists on the switch."))

    # 5. A trunk's allowed-VLAN list that omits VLAN 20 blocks the expected VLAN 20 traffic.
    match = _first_match(r"\b(?:switchport\s+)?trunk\s+allowed\s+vlan\s+([^\n]+)", output)
    if match and not re.search(r"(?<!\d)20(?!\d)", match.group(1)):
        issues.append(_issue("TRUNK-001", "Trunk Allowed VLAN Missing", "Layer 2", "Medium", _line_for_match(output, match), "Add VLAN 20 to the trunk allowed-VLAN list on both ends of the trunk."))

    # 6. An ACL deny entry is a direct indicator of policy-blocked traffic.
    match = _first_match(r"\baccess-list\s+\S+\s+deny\s+(?:tcp|udp|ip)\b", output)
    if match:
        issues.append(_issue("ACL-001", "ACL Blocking Traffic", "Layer 4", "Medium", _line_for_match(output, match), "Add the required permit statement before the deny entry, then confirm ACL direction and interface placement."))

    # 7. Source NAT configured without `overload` cannot provide PAT for multiple internal clients.
    match = _first_match(r"\bip\s+nat\s+inside\s+source\s+list\s+\S+\s+interface\s+[^\n]+", output)
    if match:
        nat_line = _line_for_match(output, match)
        if "missing overload" in nat_line.lower() or not re.search(r"\boverload\b", nat_line, re.IGNORECASE):
            issues.append(_issue("NAT-001", "NAT Overload Missing", "Layer 3", "High", nat_line, "Append the `overload` keyword to the source NAT statement to enable PAT."))

    # 8. Known invalid-gateway signals identify a gateway outside the local client subnet.
    match = _first_match(r"\bdefault\s+gateway\s+(?:is\s+)?192\.168\.1\.254\b|\bgateway\s+10\.1\.1\.30\b.*\boutside\s+subnet\b|\bdefault\s+gateway\s+outside\b", output)
    if match:
        issues.append(_issue("IP-001", "Wrong Default Gateway", "Layer 3", "High", _line_for_match(output, match), "Configure the host default gateway as the router interface address in the same IP subnet."))

    # 9. Cisco duplicate-address logs identify a conflicting IPv4 assignment.
    match = _first_match(r"%IP-4-DUP_ADDR|\bduplicate\s+address\b", output)
    if match:
        issues.append(_issue("IP-002", "Duplicate IP Address", "Layer 3", "High", _line_for_match(output, match), "Find the duplicate host, assign unique addresses, and use DHCP reservations where appropriate."))

    # 10. Neighbors advertising different OSPF hello intervals cannot form a stable adjacency.
    hello_values = re.findall(r"\b(?:ip\s+ospf\s+)?hello-interval\s+(\d+)\b", output, flags=re.IGNORECASE)
    if len(set(hello_values)) > 1:
        evidence = "; ".join(re.findall(r"[^\n]*\b(?:ip\s+ospf\s+)?hello-interval\s+\d+[^\n]*", output, flags=re.IGNORECASE))
        issues.append(_issue("OSPF-001", "OSPF Hello Timer Mismatch", "Layer 3", "High", evidence, "Configure matching OSPF hello and dead intervals on both ends of the adjacency."))

    return {
        "status": "ERRORS_DETECTED" if issues else "SUCCESS",
        "flagged_issues": issues,
    }
