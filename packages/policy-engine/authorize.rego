package avs.authorize

import future.keywords.if
import future.keywords.in
import future.keywords.contains

# AVS authorization gate. Every MCP tool call evaluates this policy.
# References: 02-prd.md §5.1, 05-architecture.md ADR-3, build-spec §4.2.
#
# Default-deny. allow becomes true ONLY through the documented rules.

default allow := false

# ─────────────── Non-destructive path ───────────────
allow if {
    input.target.cidr_in_scope
    not input.target.cidr_excluded
    input.tool_category in input.roe.test_categories
    input.action_destructive == false
    time_in_window
    not in_no_go_window
}

# ─────────────── Destructive path: requires per-asset opt-in ───────────────
allow if {
    input.target.cidr_in_scope
    not input.target.cidr_excluded
    input.action_destructive == true
    time_in_window
    not in_no_go_window
    some i
    optin := input.roe.destructive_opt_ins[i]
    optin.asset == input.target.id
    optin.allow == true
}

# ─────────────── Helpers ───────────────
time_in_window if {
    input.now >= input.roe.starts_at
    input.now <= input.roe.ends_at
}

in_no_go_window if {
    some i
    win := input.roe.no_go_windows[i]
    hh := substring(input.now, 11, 5)   # "HH:MM"
    hh >= win.start
    hh <  win.end
}

# ─────────────── Structured deny reasons ───────────────
deny_reasons contains "target_out_of_scope" if {
    not input.target.cidr_in_scope
}

deny_reasons contains "target_excluded" if {
    input.target.cidr_excluded
}

deny_reasons contains sprintf("category_not_authorized:%s", [input.tool_category]) if {
    not input.tool_category in input.roe.test_categories
}

deny_reasons contains "destructive_without_optin" if {
    input.action_destructive == true
    not has_optin
}

deny_reasons contains "before_window" if {
    input.now < input.roe.starts_at
}

deny_reasons contains "after_window" if {
    input.now > input.roe.ends_at
}

deny_reasons contains "in_no_go_window" if {
    in_no_go_window
}

has_optin if {
    some i
    optin := input.roe.destructive_opt_ins[i]
    optin.asset == input.target.id
    optin.allow == true
}
