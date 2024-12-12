from sqlalchemy import Column, Integer, String, JSON, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True, nullable=False)
    tenant_id = Column(String, index=True, nullable=True)
    method = Column(String, nullable=True)
    path = Column(String, nullable=True)
    query_params = Column(String, nullable=True)
    request_headers = Column(JSON, nullable=True)
    request_body = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    geolocation = Column(JSON, nullable=True)
    session_id = Column(String, nullable=True)
    response_status_code = Column(Integer, nullable=True)
    response_body = Column(JSON, nullable=True)
    response_headers = Column(JSON, nullable=True)
    duration = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False)

    def __repr__(self):
        return (
            f"<LogEntry id={self.id}, request_id={self.request_id}, method={self.method}, "
            f"path={self.path}, query_params={self.query_params}, "
            f"request_headers={self.request_headers}, request_body={self.request_body}, "
            f"ip_address={self.ip_address}, user_agent={self.user_agent}, "
            f"geolocation={self.geolocation}, session_id={self.session_id}, "
            f"response_status_code={self.response_status_code}, response_body={self.response_body}, "
            f"response_headers={self.response_headers}, duration={self.duration}, "
            f"timestamp={self.timestamp}>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "method": self.method,
            "path": self.path,
            "query_params": self.query_params,
            "request_headers": self.request_headers,
            "request_body": self.request_body,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "geolocation": self.geolocation,
            "session_id": self.session_id,
            "response_status_code": self.response_status_code,
            "response_body": self.response_body,
            "response_headers": self.response_headers,
            "duration": self.duration,
            "timestamp": self.timestamp,
        }
