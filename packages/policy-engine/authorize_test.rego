package avs.authorize_test

import future.keywords.if
import future.keywords.in
import data.avs.authorize

mock_roe := {
    "id": "test-roe",
    "test_categories": ["recon", "cve"],
    "starts_at": "2026-04-01T00:00:00Z",
    "ends_at":   "2026-07-01T00:00:00Z",
    "no_go_windows": [{"start": "02:00", "end": "04:00", "reason": "backup"}],
    "destructive_opt_ins": [{"asset": "10.0.0.5:443", "allow": true, "justification": "demo"}]
}

base_input := {
    "now": "2026-05-15T13:00:00Z",
    "tool_category": "recon",
    "action_destructive": false,
    "target": {"id": "10.0.0.1:80", "kind": "host", "cidr_in_scope": true, "cidr_excluded": false},
    "roe": mock_roe
}

# 1. happy path
test_allow_in_scope_recon if {
    authorize.allow with input as base_input
}

# 2. out of scope
test_deny_out_of_scope if {
    not authorize.allow with input as object.union(base_input, {"target": {"id":"x","cidr_in_scope":false,"cidr_excluded":false}})
}

# 3. excluded
test_deny_excluded if {
    not authorize.allow with input as object.union(base_input, {"target": {"id":"x","cidr_in_scope":true,"cidr_excluded":true}})
}

# 4. category not authorized
test_deny_category_not_authorized if {
    not authorize.allow with input as object.union(base_input, {"tool_category": "dos"})
}

# 5. destructive without opt-in
test_deny_destructive_without_optin if {
    not authorize.allow with input as object.union(base_input, {"action_destructive": true})
}

# 6. destructive WITH opt-in (asset matches)
test_allow_destructive_with_optin if {
    authorize.allow with input as object.union(base_input, {
        "action_destructive": true,
        "target": {"id": "10.0.0.5:443", "kind":"host", "cidr_in_scope": true, "cidr_excluded": false}
    })
}

# 7. before window
test_deny_before_window if {
    not authorize.allow with input as object.union(base_input, {"now": "2026-01-01T00:00:00Z"})
}

# 8. after window
test_deny_after_window if {
    not authorize.allow with input as object.union(base_input, {"now": "2027-01-01T00:00:00Z"})
}

# 9. in no-go window
test_deny_in_no_go_window if {
    not authorize.allow with input as object.union(base_input, {"now": "2026-05-15T03:00:00Z"})
}

# 10. cve allowed
test_allow_cve if {
    authorize.allow with input as object.union(base_input, {"tool_category": "cve"})
}

# 11. webapp not in roe categories
test_deny_webapp_not_in_categories if {
    not authorize.allow with input as object.union(base_input, {"tool_category": "webapp"})
}

# 12. destructive opt-in for different asset → still deny
test_deny_destructive_optin_for_other_asset if {
    not authorize.allow with input as object.union(base_input, {
        "action_destructive": true,
        "target": {"id": "10.0.0.99:22", "kind":"host", "cidr_in_scope": true, "cidr_excluded": false}
    })
}
