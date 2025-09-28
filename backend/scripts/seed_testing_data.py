"""
Seed database from Testing_datas.md JSON blocks.

Usage in container:
  python -m scripts.seed_testing_data
"""

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import text
from app.core.database import SessionLocal, Base, engine
from app.models import (
    Organization,
    Supplier,
    Contract,
    ContractParty,
    ContractTerm,
    ContractClause,
)

# In backend container, backend is mounted at /app, Testing_datas.md is at /app/Testing_datas.md
TESTING_MD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Testing_datas.md")
TESTING_MD_PATH = os.path.abspath(TESTING_MD_PATH)


def extract_json_blocks(markdown_text: str) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    for match in re.finditer(r"```json\n([\s\S]*?)\n```", markdown_text):
        payload = match.group(1)
        try:
            blocks.append(json.loads(payload))
        except Exception:
            pass
    return blocks


def ensure_organization(db, org_id: int):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        org = Organization(id=org_id, name=f"Org {org_id}")
        db.add(org)
        db.commit()
        db.refresh(org)
    return org


def upsert_supplier(db, data: Dict[str, Any]) -> Supplier:
    supplier_id = data.get("id")
    supplier = None
    if supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        supplier = db.query(Supplier).filter(Supplier.name == data["name"]).first()
    if not supplier:
        supplier = Supplier(**{k: v for k, v in data.items() if hasattr(Supplier, k)})
        db.add(supplier)
    else:
        for k, v in data.items():
            if hasattr(Supplier, k) and v is not None:
                setattr(supplier, k, v)
    db.commit()
    db.refresh(supplier)
    return supplier




def upsert_contract(db, data: Dict[str, Any]) -> Contract:
    contract_id = data.get("id")
    contract = None
    if contract_id:
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        contract = Contract(**{k: v for k, v in data.items() if hasattr(Contract, k)})
        db.add(contract)
    else:
        for k, v in data.items():
            if hasattr(Contract, k) and v is not None:
                setattr(contract, k, v)
    db.commit()
    db.refresh(contract)
    return contract


def create_contract_party(db, data: Dict[str, Any], contract_id: int):
    cp = ContractParty(
        contract_id=contract_id,
        role=data.get("role"),
        name=data.get("name"),
        is_internal=bool(data.get("is_internal")),
        supplier_id=data.get("supplier_id"),
    )
    db.add(cp)
    db.commit()
    return cp


def create_contract_terms(db, data: Dict[str, Any], contract_id: int):
    ct = ContractTerm(
        contract_id=contract_id,
        payment_terms=data.get("payment_terms"),
        penalties=data.get("penalties"),
        service_levels=data.get("service_levels"),
        liability_cap=data.get("liability_cap"),
        termination=data.get("termination"),
    )
    db.add(ct)
    db.commit()
    return ct


def _get_table_columns(db, table_name: str) -> List[str]:
    result = db.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :t
            """
        ),
        {"t": table_name},
    )
    return [row[0] for row in result.fetchall()]


def create_clause(db, data: Dict[str, Any], contract_id: int) -> ContractClause:
    columns = _get_table_columns(db, "contract_clauses")
    # If legacy schema exists (clause_type, risk_level, clause_text), insert accordingly
    if "clause_type" in columns:
        # Legacy schema references documents.id; skip clause seeding to avoid FK mismatch
        return ContractClause(id=data.get("id"), contract_id=contract_id)
    # Otherwise use the new normalized schema
    cc = ContractClause(
        id=data.get("id"),
        contract_id=contract_id,
        type=data.get("type"),
        risk_flag=data.get("risk_flag"),
        text_excerpt=data.get("text_excerpt"),
        clause_metadata=data.get("metadata"),
    )
    db.add(cc)
    db.commit()
    db.refresh(cc)
    return cc




def _parse_dt(s: Any):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None



def main():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    with open(TESTING_MD_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = extract_json_blocks(content)
    if not blocks:
        print("No JSON blocks found in Testing_datas.md")
        return

    db = SessionLocal()
    try:
        for block in blocks:
            if "suppliers" in block:
                supplier_data = block["suppliers"]
                ensure_organization(db, supplier_data.get("organization_id", 1))
                supplier = upsert_supplier(db, supplier_data)

            if "contracts" in block:
                contract_data = block["contracts"]
                ensure_organization(db, contract_data.get("organization_id", 1))
                contract = upsert_contract(db, contract_data)
                for p in block.get("contract_parties", []) or []:
                    create_contract_party(db, p, contract.id)
                terms = block.get("contract_terms")
                if isinstance(terms, dict):
                    create_contract_terms(db, terms, contract.id)
                for cl in block.get("contract_clauses", []) or []:
                    create_clause(db, cl, contract.id)
        print("Seeding completed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
