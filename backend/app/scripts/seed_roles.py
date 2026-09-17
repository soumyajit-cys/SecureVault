ROLES = {
    "Admin": [
        "*",
    ],
    "User": [
        "file:encrypt",
        "file:decrypt",
        "file:upload",
        "file:download",
        "share:create",
        "share:revoke",
    ],
    "Auditor": [
        "audit:read",
        "audit:export",
    ],
}