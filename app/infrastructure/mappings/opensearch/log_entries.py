def get_log_entries_mapping():
    return {
        "properties": {
            "duration": {"type": "float"},
            "geolocation": {"type": "geo_point"},
            "ip_address": {"type": "ip"},
            "method": {"type": "keyword", "ignore_above": 256},
            "nivel": {"type": "keyword", "ignore_above": 256},
            "path": {"type": "keyword", "ignore_above": 256},
            "query_params": {"type": "text"},
            "request_body": {"type": "object", "enabled": True},
            "request_headers": {
                "type": "object",
                "properties": {
                    "accept": {"type": "keyword", "ignore_above": 256},
                    "accept-encoding": {"type": "keyword", "ignore_above": 256},
                    "accept-language": {"type": "keyword", "ignore_above": 256},
                    "authorization": {"type": "keyword", "ignore_above": 256},
                    "connection": {"type": "keyword", "ignore_above": 256},
                    "host": {"type": "keyword", "ignore_above": 256},
                    "origin": {"type": "keyword", "ignore_above": 256},
                    "referer": {"type": "keyword", "ignore_above": 256},
                    "sec-ch-ua": {"type": "keyword", "ignore_above": 256},
                    "sec-ch-ua-mobile": {"type": "keyword", "ignore_above": 256},
                    "sec-ch-ua-platform": {"type": "keyword", "ignore_above": 256},
                    "sec-fetch-dest": {"type": "keyword", "ignore_above": 256},
                    "sec-fetch-mode": {"type": "keyword", "ignore_above": 256},
                    "sec-fetch-site": {"type": "keyword", "ignore_above": 256},
                    "user-agent": {"type": "keyword", "ignore_above": 256},
                    "x-tenant-id": {"type": "keyword", "ignore_above": 256},
                },
            },
            "request_id": {"type": "keyword", "ignore_above": 256},
            "response_body": {"type": "object", "enabled": True},
            "response_headers": {
                "type": "object",
                "properties": {
                    "content-length": {"type": "keyword", "ignore_above": 256},
                    "content-type": {"type": "keyword", "ignore_above": 256},
                },
            },
            "response_status_code": {"type": "integer"},
            "tenant_id": {"type": "keyword", "ignore_above": 256},
            "timestamp": {"type": "date"},
            "user_agent": {"type": "keyword", "ignore_above": 256},
        }
    }
