"""
models.py — Enums, API schemas, and internal LLM schema.
"""

from enum import Enum

from pydantic import BaseModel, Field

# Taxonomy enums ───────────────────────────────────────────────────────────────


class Category(str, Enum):
    """Top-level support ticket category."""

    TRANSFERENCIAS_ENVIOS = "TRANSFERENCIAS_ENVIOS"
    CUENTA_PERFIL = "CUENTA_PERFIL"
    SEGURIDAD_FRAUDE = "SEGURIDAD_FRAUDE"
    TARJETA = "TARJETA"
    COBROS_COMISIONES = "COBROS_COMISIONES"
    APP_PLATAFORMA = "APP_PLATAFORMA"
    RECLAMO_QUEJA = "RECLAMO_QUEJA"
    PRODUCTO_INFO = "PRODUCTO_INFO"
    REEMBOLSO_DEVOLUCION = "REEMBOLSO_DEVOLUCION"
    DESCONOCIDO = "DESCONOCIDO"
    AGENTE = "AGENTE"


class Subcategory(str, Enum):
    """Second-level support ticket subcategory, grouped by parent category."""

    # TRANSFERENCIAS_ENVIOS
    ENVIO_PENDIENTE = "ENVIO_PENDIENTE"
    ENVIO_RECHAZADO = "ENVIO_RECHAZADO"
    ERROR_DATOS_DESTINO = "ERROR_DATOS_DESTINO"
    DINERO_NO_RECIBIDO = "DINERO_NO_RECIBIDO"
    DEVOLUCION_FONDOS = "DEVOLUCION_FONDOS"
    RUTA_NO_DISPONIBLE = "RUTA_NO_DISPONIBLE"
    # CUENTA_PERFIL
    BLOQUEO_CUENTA = "BLOQUEO_CUENTA"
    VERIFICACION_IDENTIDAD = "VERIFICACION_IDENTIDAD"
    CIERRE_CUENTA = "CIERRE_CUENTA"
    CAMBIO_DATOS_PERFIL = "CAMBIO_DATOS_PERFIL"
    CUENTA_BUSINESS = "CUENTA_BUSINESS"
    CUMPLIMIENTO_NORMATIVO = "CUMPLIMIENTO_NORMATIVO"
    # SEGURIDAD_FRAUDE
    ACCESO_NO_AUTORIZADO = "ACCESO_NO_AUTORIZADO"
    PHISHING_ESTAFA = "PHISHING_ESTAFA"
    CLONACION_TARJETA = "CLONACION_TARJETA"
    TRANSACCION_NO_RECONOCIDA = "TRANSACCION_NO_RECONOCIDA"
    ROBO_DISPOSITIVO = "ROBO_DISPOSITIVO"
    # TARJETA
    ENTREGA_TARJETA = "ENTREGA_TARJETA"
    TARJETA_DANADA = "TARJETA_DANADA"
    RECHAZO_TARJETA = "RECHAZO_TARJETA"
    REPOSICION_TARJETA = "REPOSICION_TARJETA"
    WALLET_DIGITAL = "WALLET_DIGITAL"
    # COBROS_COMISIONES
    COMISION_INESPERADA = "COMISION_INESPERADA"
    TIPO_CAMBIO = "TIPO_CAMBIO"
    COBRO_DUPLICADO = "COBRO_DUPLICADO"
    COBRO_SUSCRIPCION = "COBRO_SUSCRIPCION"
    AJUSTE_SALDO = "AJUSTE_SALDO"
    # APP_PLATAFORMA
    ERROR_TECNICO = "ERROR_TECNICO"
    IDIOMA_TRADUCCION = "IDIOMA_TRADUCCION"
    RENDIMIENTO_LENTO = "RENDIMIENTO_LENTO"
    FUNCION_NO_DISPONIBLE = "FUNCION_NO_DISPONIBLE"
    FALLA_CONEXION = "FALLA_CONEXION"
    # RECLAMO_QUEJA
    AMENAZA_REGULATORIA = "AMENAZA_REGULATORIA"
    MALA_ATENCION = "MALA_ATENCION"
    INCUMPLIMIENTO_PROMESA = "INCUMPLIMIENTO_PROMESA"
    PROTECCION_DATOS = "PROTECCION_DATOS"
    # PRODUCTO_INFO
    INFO_SERVICIOS = "INFO_SERVICIOS"
    COMPROBANTES_CERTIFICADOS = "COMPROBANTES_CERTIFICADOS"
    FUNCIONALIDAD_NUEVA = "FUNCIONALIDAD_NUEVA"
    CUENTA_MULTIMONEDA = "CUENTA_MULTIMONEDA"
    ALIANZAS_COMERCIALES = "ALIANZAS_COMERCIALES"
    # REEMBOLSO_DEVOLUCION
    DEVOLUCION_TRANSFERENCIA = "DEVOLUCION_TRANSFERENCIA"
    DESCONOCIMIENTO_CARGO = "DESCONOCIMIENTO_CARGO"
    REEMBOLSO_COMISION = "REEMBOLSO_COMISION"
    REEMBOLSO_PENDIENTE = "REEMBOLSO_PENDIENTE"
    # Fallback
    DESCONOCIDO = "DESCONOCIDO"
    AGENTE = "AGENTE"


class Sentiment(str, Enum):
    """User sentiment detected in the conversation."""

    POSITIVO = "POSITIVO"
    NEUTRAL = "NEUTRAL"
    NEGATIVO = "NEGATIVO"


class Urgency(str, Enum):
    """Urgency level of the support case."""

    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


# API schemas ──────────────────────────────────────────────────────────────────


class IncomingMessage(BaseModel):
    """Payload received by the ``/sofia/classify`` endpoint."""

    case_id: str = Field(examples=["CASE-001"])
    message_id: str = Field(examples=["MSG-001"])
    user_id: str = Field(examples=["USR-772"])
    direction: str = Field(pattern="^(INBOUND|OUTBOUND)$")
    text: str
    pais_usuario: str = Field(examples=["Chile"])
    channel: str = Field(default="No especificado", examples=["instagram", "gmail", "global66"])


class ClassifyResponse(BaseModel):
    """Response returned by the ``/sofia/classify`` endpoint."""

    case_id: str
    message_id: str
    decision: str  # keep_hearing | trigger_block
    category: str
    subcategory: str
    sentiment: str
    urgency: str
    confidence: float
    text: str  # suggested response when trigger_block, "" otherwise


# Internal LLM schema (tool_use) ───────────────────────────────────────────────


class AgentDecision(BaseModel):
    """
    Structured output returned by the LLM via the ``classify_case`` tool.

    Used as both the Pydantic validation model and the tool ``input_schema``
    passed to the Anthropic API.
    """

    category: Category
    subcategory: Subcategory
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence score.")
    sentiment: Sentiment
    urgency: Urgency
    is_fraud: bool = Field(
        description="True only when there is clear evidence of an active SEGURIDAD_FRAUDE incident."
    )
    suggested_response: str = Field(
        default="",
        description="Response to send to the user when is_fraud=True. Empty string otherwise.",
    )
    reasoning: str = Field(default="", description="One sentence explaining the classification.")
