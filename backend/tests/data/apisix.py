"""
APISix test data
"""

ROUTES = [
    {
        "id": "foo",
        "uri": "/foo",
        "plugins": {"key-auth": {}, "proxy-rewrite": {"uri": "/"}},
        "upstream": {"type": "roundrobin", "nodes": {"httpbin.org:80": 1}, "scheme": "http"},
    },
    {
        "id": "bar",
        "uri": "/bar",
        "plugins": {"key-auth": {}, "proxy-rewrite": {"uri": "/"}},
        "upstream": {"type": "roundrobin", "nodes": {"httpbin.org:80": 1}, "scheme": "http"},
    },
    {
        "id": "baz",
        "uri": "/baz",
        "plugins": {},
        "upstream": {"type": "roundrobin", "nodes": {"httpbin.org:80": 1}, "scheme": "http"},
    },
]
