"""agent-gateway — Universal agent protocol gateway."""

from agent_gateway.config import GatewayConfig, RouteConfig
from agent_gateway.gateway import Gateway
from agent_gateway.translator import ProtocolTranslator
from agent_gateway.models import AgentRequest, AgentResponse

__version__ = "2.0.0"
__all__ = [
    "Gateway",
    "GatewayConfig",
    "RouteConfig",
    "ProtocolTranslator",
    "AgentRequest",
    "AgentResponse",
]
