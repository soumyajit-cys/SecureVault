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
    ],
    "Auditor": [
        "audit:read",
        "audit:export",
    ],
}