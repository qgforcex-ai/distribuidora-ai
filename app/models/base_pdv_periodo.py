from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database import Base


class BasePdvPeriodo(Base):
    __tablename__ = "base_pdv_periodos"
    __table_args__ = (
        UniqueConstraint(
            "periodo",
            "cliente_id",
            name="uk_base_pdv_periodo_cliente"
        ),
        Index("idx_base_pdv_periodo_rn", "periodo", "rn"),
        Index("idx_base_pdv_cliente_id", "cliente_id"),
        Index("idx_base_pdv_periodo", "periodo"),
    )

    id = Column(Integer, primary_key=True, index=True)
    periodo = Column(Date, nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    rn = Column(String(20), nullable=False)
    nome_fantasia = Column(String(150), nullable=True)
    cidade = Column(String(100), nullable=True)
    bairro = Column(String(150), nullable=True)
    status_cliente = Column(String(50), nullable=True)
    proxima_visita = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    cliente = relationship("Cliente", back_populates="base_pdv_periodos")
