from sqlalchemy import Column, Date, DateTime, Index, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class Importacao(Base):
    __tablename__ = "importacoes"
    __table_args__ = (
        Index("idx_importacoes_tipo_periodo", "tipo", "periodo"),
        Index("idx_importacoes_arquivo_hash", "arquivo_hash"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False)
    periodo = Column(Date, nullable=True)
    arquivo_nome = Column(String(255), nullable=True)
    arquivo_hash = Column(String(64), nullable=True)
    status = Column(String(30), nullable=True)
    linhas_lidas = Column(Integer, nullable=False, default=0, server_default="0")
    linhas_importadas = Column(Integer, nullable=False, default=0, server_default="0")
    erros = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    vendas = relationship("Venda", back_populates="importacao")
