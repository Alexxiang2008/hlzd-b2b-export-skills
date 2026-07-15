"""hlzd-cold-outreach shared library.

- 5 类 buyer-type 模板路由
- 多语种变量替换
- 跟进序列生成器（Day 7 / Day 14）
- 字数检查 + variable substitution
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s :: %(message)s"


def get_logger(name: str = "hlzd-cold-outreach") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(stream=sys.stderr)
        h.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(h)
        logger.setLevel(os.getenv("HLZD_LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


# ================================================================
# 错误归类
# ================================================================

class OutreachError(Exception):
    def __init__(self, message: str, *, source: str = "hlzd-cold-outreach",
                 recoverable: bool = True):
        super().__init__(message)
        self.source = source
        self.recoverable = recoverable


class InvalidBuyerRecord(OutreachError):
    def __init__(self, message: str):
        super().__init__(message, source="schema", recoverable=False)


class UnsupportedLanguage(OutreachError):
    def __init__(self, lang: str):
        super().__init__(f"unsupported language: {lang!r}", source="i18n",
                          recoverable=False)


# ================================================================
# Variable substitution
# ================================================================

VARIABLE_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def fill_template(text: str, variables: Dict[str, Any]) -> str:
    """Replace {{var}} with str(variables[var]); unknown var → leave placeholder."""
    def _sub(m):
        key = m.group(1)
        if key in variables and variables[key] is not None and variables[key] != "":
            return str(variables[key])
        return m.group(0)  # leave as {{key}}
    return VARIABLE_RE.sub(_sub, text)


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def is_within_word_limit(text: str, min_words: int = 50, max_words: int = 150) -> bool:
    n = word_count(text)
    return min_words <= n <= max_words


# ================================================================
# 模板库（5 类 buyer type × 2 种语言）
# ================================================================

TEMPLATES: Dict[str, Dict[str, Dict[str, str]]] = {
    # 键层级：customer_type -> language -> {subject, opening, value_prop, cta, signature}
    "Manufacturer": {
        "en": {
            "subject": "Reliable supply partner for {{product_category}} - {{sender_company}}",
            "opening": "Dear {{contact_name}},\n\nWe noted {{recipient_company}}'s strong focus on manufacturing in {{sector}}, and the importance of supplier reliability for your {{product_category}} sourcing.",
            "value_prop": "We are {{sender_company}}, a {expertise_year}-year manufacturer of {{product_category}} with monthly capacity of {{capacity}}. Our {{cert_count}} certifications include {{key_cert}}.",
            "cta": "If relevant, would you consider a 15-minute call to explore if our product specs and lead time fit your sourcing plan?",
            "signature": "Best regards,\n{{sender_name}}\n{{sender_title}} | {{sender_company}}\n{{sender_email}} | {{sender_phone}}",
        },
        "es": {
            "subject": "Socio confiable para {{product_category}} - {{sender_company}}",
            "opening": "Estimado/a {{contact_name}},\n\nHemos observado el enfoque de {{recipient_company}} en manufactura de {{sector}}, y la importancia de un proveedor estable para su cadena de {{product_category}}.",
            "value_prop": "Somos {{sender_company}}, fabricantes con {expertise_year} años en {{product_category}} con capacidad mensual de {{capacity}}. Contamos con {{cert_count}} certificaciones incluyendo {{key_cert}}.",
            "cta": "Si fuese de su interés, le propongo una llamada de 15 minutos para verificar si nuestras especificaciones y plazos se ajustan a su plan de compras.",
            "signature": "Cordialmente,\n{{sender_name}}\n{{sender_title}} | {{sender_company}}\n{{sender_email}} | {{sender_phone}}",
        },
    },
    "EPC": {
        "en": {
            "subject": "EPC partner for {{project_name}} - {{product_category}} supply",
            "opening": "Dear {{contact_name}},\n\nWe understand {{recipient_company}} is executing {{project_name}}, where {{product_category}} procurement is on the critical path.",
            "value_prop": "{{sender_company}} has supported [past project references] EPC-grade requirements with documented traceability, MTC, and prior-package performance.",
            "cta": "Could we schedule a 20-minute call this week to align on packaging, document set, and incoterms?",
            "signature": "Best regards,\n{{sender_name}}\n{{sender_title}} | {{sender_company}}\n{{sender_email}} | {{sender_phone}}",
        },
        "es": {
            "subject": "Socio EPC para {{project_name}} - suministro de {{product_category}}",
            "opening": "Estimado/a {{contact_name}},\n\nEntendemos que {{recipient_company}} ejecuta {{project_name}}, donde la adquisicion de {{product_category}} esta en ruta critica.",
            "value_prop": "{{sender_company}} ha respaldado proyectos EPC con trazabilidad documentada, MTC, y desempeno de lotes previos.",
            "cta": "Podriamos agendar una llamada de 20 minutos esta semana para alinear empaque, documentacion e incoterms?",
            "signature": "Cordialmente,\n{{sender_name}}\n{{sender_title}} | {{sender_company}}\n{{sender_email}} | {{sender_phone}}",
        },
    },
    "Distributor": {
        "en": {
            "subject": "Distribution opportunity - {{product_category}} for {{recipient_region}}",
            "opening": "Dear {{contact_name}},\n\nWe are expanding our {{recipient_region}} channel and noticed your portfolio aligns with {{product_category}}.",
            "value_prop": "{{sender_company}} offers distributor-friendly MOQ of {{min_moq}}, distributor pricing tier of {{distributor_margin}}% off MSRP, and protected territories upon request.",
            "cta": "Would you be open to a brief call to review distributor terms, target margin, and lead-time commitments?",
            "signature": "Best regards,\n{{sender_name}}\n{{sender_title}} | {{sender_company}}\n{{sender_email}} | {{sender_phone}}",
        },
        "es": {
            "subject": "Oportunidad de distribucion - {{product_category}} en {{recipient_region}}",
            "opening": "Estimado/a {{contact_name}},\n\nEstamos expandiendo nuestro canal en {{recipient_region}} y notamos que su portafolio se alinea con {{product_category}}.",
            "value_prop": "{{sender_company}} ofrece MOQ para distribuidores de {{min_moq}}, margen distribuidor de {{distributor_margin}}% sobre MSRP, y territorios protegidos a solicitud.",
            "cta": "Estaria abierto/a a una breve llamada para revisar terminos de distribucion, margen objetivo y plazos de entrega?",
            "signature": "Cordialmente,\n{{sender_name}}\n{{sender_title}} | {{sender_company}}\n{{sender_email}} | {{sender_phone}}",
        },
    },
    "OEM": {
        "en": {
            "subject": "OEM partnership inquiry - {{product_category}} private-label",
            "opening": "Dear {{contact_name}},\n\nWe have supported several OEM / private-label programs on {{product_category}} for similar-sized partners in {{sector}}.",
            "value_prop": "{{sender_company}} offers label-design flexibility, batch-level QC, and traceable documentation. Our minimum annual commitment is {{annual_commit}}.",
            "cta": "Would a discovery call to discuss your brand-defining specs and lead-time flexibility be useful next week?",
            "signature": "Best regards,\n{{sender_name}}\n{{sender_title}} | {{sender_company}}\n{{sender_email}} | {{sender_phone}}",
        },
        "es": {
            "subject": "Consulta de alianza OEM - {{product_category}} marca privada",
            "opening": "Estimado/a {{contact_name}},\n\nHemos respaldado varios programas OEM / marca privada de {{product_category}} para socios similares en {{sector}}.",
            "value_prop": "{{sender_company}} ofrece flexibilidad de diseno de etiqueta, QC a nivel de lote, y documentacion trazable. Nuestro compromiso minimo anual es {{annual_commit}}.",
            "cta": "Seria util la proxima semana una llamada para discutir sus especificaciones y flexibilidad de plazos?",
            "signature": "Cordialmente,\n{{sender_name}}\n{{sender_title}} | {{sender_company}}\n{{sender_email}} | {{sender_phone}}",
        },
    },
    "End User": {
        "en": {
            "subject": "{{product_category}} direct from manufacturer - cost-saving opportunity",
            "opening": "Dear {{contact_name}},\n\nWe understand {{recipient_company}} operates {{sector}} and is looking for direct factory supply rather than multi-tier distribution.",
            "value_prop": "{{sender_company}} supplies directly from our factory, cutting one to two layers of distribution and passing savings of approximately {{savings_pct}}% per shipment.",
            "cta": "May I send a one-pager comparing landed-cost math versus your current supplier?",
            "signature": "Best regards,\n{{sender_name}}\n{{sender_title}} | {{sender_company}}\n{{sender_email}} | {{sender_phone}}",
        },
        "es": {
            "subject": "{{product_category}} directo del fabricante - oportunidad de ahorro",
            "opening": "Estimado/a {{contact_name}},\n\nEntendemos que {{recipient_company}} opera {{sector}} y busca suministro directo de fabrica en lugar de distribucion multi-nivel.",
            "value_prop": "{{sender_company}} suministra directamente desde fabrica, eliminando uno a dos niveles de distribucion y trasladando ahorros de aproximadamente {{savings_pct}}% por envio.",
            "cta": "Puedo enviarle un comparativo de costo puesto en destino versus su proveedor actual?",
            "signature": "Cordialmente,\n{{sender_name}}\n{{sender_title}} | {{sender_company}}\n{{sender_email}} | {{sender_phone}}",
        },
    },
    "Trader": {
        "en": {
            "subject": "Quick quote request - {{product_category}} (FOB {{fob_port}})",
            "opening": "Dear {{contact_name}},\n\nWe noted your active trading of {{product_category}}. {{sender_company}} has FOB availability from {{fob_port}} with frequent shipment windows.",
            "value_prop": "We can quote tiered pricing on {{product_category}} at FOB {{fob_port}}. Our typical lead time is {{lead_time}}, payment terms 30/70 T/T or LC at sight.",
            "cta": "If you have a buyer with an active RFQ, please forward specs and target price; we will respond within 24 hours.",
            "signature": "Best regards,\n{{sender_name}}\n{{sender_title}} | {{sender_company}}\n{{sender_email}} | {{sender_phone}}",
        },
        "es": {
            "subject": "Solicitud de cotizacion - {{product_category}} (FOB {{fob_port}})",
            "opening": "Estimado/a {{contact_name}},\n\nHemos notado su actividad comercial en {{product_category}}. {{sender_company}} tiene disponibilidad FOB desde {{fob_port}} con ventanas de embarque frecuentes.",
            "value_prop": "Podemos cotizar precios escalonados en {{product_category}} en FOB {{fob_port}}. Nuestro plazo tipico es {{lead_time}}, pago 30/70 T/T o LC a la vista.",
            "cta": "Si tiene un comprador con RFQ activo, favor enviar especificaciones y precio objetivo; responderemos en 24 horas.",
            "signature": "Cordialmente,\n{{sender_name}}\n{{sender_title}} | {{sender_company}}\n{{sender_email}} | {{sender_phone}}",
        },
    },
}


SUPPORTED_LANGUAGES = ("en", "es")
SUPPORTED_CUSTOMER_TYPES = tuple(TEMPLATES.keys())


def select_template(customer_type: str, language: str = "en") -> Dict[str, str]:
    """取模板 Dict，customer_type 不支持则 fallback Manufacturer + warning."""
    if language not in SUPPORTED_LANGUAGES:
        raise UnsupportedLanguage(language)
    ctype = customer_type if customer_type in TEMPLATES else "Manufacturer"
    ttype = TEMPLATES[ctype]
    return ttype.get(language, ttype["en"])


def render_email(buyer: Dict[str, Any], product_context: Dict[str, Any],
                  customer_type: str = "Manufacturer",
                  language: str = "en") -> Dict[str, Any]:
    """Render subject + body from template + variables.

    variables 优先级：product_context > buyer-derived fields > defaults
    """
    variables = _merge_variables(buyer, product_context)
    template = select_template(customer_type, language)

    subject = fill_template(template["subject"], variables)
    body_parts = [
        fill_template(template["opening"], variables),
        fill_template(template["value_prop"], variables),
        fill_template(template["cta"], variables),
        fill_template(template["signature"], variables),
    ]
    body = "\n\n".join(body_parts)

    return {
        "$schema": "hlzd/cold-outreach/v1",
        "to": {
            "company": buyer.get("importer_name", buyer.get("company_name", "")),
            "contact": buyer.get("contact_person", buyer.get("contact_name", "")),
            "country": buyer.get("country", ""),
        },
        "language": language,
        "customer_type_used": customer_type if customer_type in TEMPLATES else "Manufacturer",
        "subject": subject,
        "body": body,
        "word_count": word_count(body),
        "within_word_limit": is_within_word_limit(body),
        "missing_variables": _missing_variables(template, variables),
    }


def _merge_variables(buyer: Dict[str, Any], product_context: Dict[str, Any]) -> Dict[str, Any]:
    """从 buyer + product_context 合并出所有 {{var}} 可填值。"""
    merged = {}

    # Sender 默认（可由 product_context 覆盖）
    sender_defaults = {
        "sender_company": "HLZD",
        "sender_name": "Sales Team",
        "sender_title": "International Sales Manager",
        "sender_email": "sales@hlzd.example.com",
        "sender_phone": "+86 138 0000 0000",
        "expertise_year": "12",
        "cert_count": "8",
        "key_cert": "ISO 9001 + CE",
        "capacity": "1500 tons",
        "min_moq": "1x20GP",
        "distributor_margin": "25",
        "annual_commit": "USD 200K",
        "savings_pct": "15",
        "fob_port": "Shanghai / Ningbo",
        "lead_time": "30-45 days",
    }
    merged.update(sender_defaults)

    # 产品信息
    for k, v in product_context.items():
        if isinstance(v, dict):
            merged.update(v)
        else:
            merged[k] = v

    # Buyer-derived：recipient_company / recipient_region / sector / project
    merged["recipient_company"] = buyer.get("importer_name", buyer.get("company_name", ""))
    merged["recipient_region"] = buyer.get("country", "your market")
    # sector / project 缺省：留空 → 模板有 fallback 文字
    if "sector" not in merged or merged.get("sector") in (None, ""):
        merged["sector"] = "your sector"
    if "project_name" not in merged or merged.get("project_name") in (None, ""):
        merged["project_name"] = "your project"
    if "contact_name" not in merged or merged.get("contact_name") in (None, ""):
        merged["contact_name"] = buyer.get("contact_person", "Procurement Team")

    # product_category 可由 product 推导
    if "product_category" not in merged or merged.get("product_category") in (None, ""):
        merged["product_category"] = product_context.get("product", "industrial equipment")

    return merged


def _missing_variables(template: Dict[str, str], variables: Dict[str, Any]) -> List[str]:
    """返回模板里出现但未在 variables 中实际提供的 {{var}}。"""
    text = " ".join(template.values())
    placeholders = set(VARIABLE_RE.findall(text))
    return sorted(p for p in placeholders
                  if p not in variables or variables[p] in (None, ""))


# ================================================================
# Followup sequences
# ================================================================

FOLLOWUP_TEMPLATES: Dict[str, Dict[str, Dict[str, str]]] = {
    "day_7": {
        "en": {
            "subject": "Re: {{subject_root}}",
            "body": "Dear {{contact_name}},\n\nFollowing up on my note last week regarding {{product_category}} for {{recipient_company}}. If a brief discussion would help, I can adjust to your timezone this week.\n\nBest,\n{{sender_name}}",
        },
        "es": {
            "subject": "Re: {{subject_root}}",
            "body": "Estimado/a {{contact_name}},\n\nDando seguimiento a mi nota de la semana pasada sobre {{product_category}} para {{recipient_company}}. Si una breve conversacion ayudase, puedo ajustarme a su zona horaria esta semana.\n\nCordialmente,\n{{sender_name}}",
        },
    },
    "day_14": {
        "en": {
            "subject": "Closing the loop - {{product_category}} inquiry",
            "body": "Dear {{contact_name}},\n\nClosing the loop on my notes about {{product_category}}. If now isn't the right time, I'll mark this in our records and reach out again in a quarter.\n\nBest,\n{{sender_name}}",
        },
        "es": {
            "subject": "Cerrando el hilo - consulta de {{product_category}}",
            "body": "Estimado/a {{contact_name}},\n\nCierro el hilo sobre mis notas de {{product_category}}. Si no es buen momento, lo registramos y contactamos nuevamente en un trimestre.\n\nCordialmente,\n{{sender_name}}",
        },
    },
}


def render_followup_sequence(initial_email: Dict[str, Any],
                                language: str = "en") -> List[Dict[str, Any]]:
    """基于首发邮件生成 Day 7 / Day 14 跟进序列。"""
    subject_root = initial_email.get("subject", "")
    variables = {
        "subject_root": re.sub(r"^Re:\s*", "", subject_root),
        "contact_name": initial_email.get("to", {}).get("contact", "Procurement Team"),
        "recipient_company": initial_email.get("to", {}).get("company", ""),
        "product_category": variables.get("product_category", "industrial equipment")
                              if "variables" in dir() else "industrial equipment",
        "sender_name": "Sales Team",
    }
    # 简化：product_category 若 initial_email 含需要回传
    if "product_category" in initial_email:
        variables["product_category"] = initial_email["product_category"]
    if "sender_name" in initial_email:
        variables["sender_name"] = initial_email["sender_name"]

    seq = []
    for day_key in ("day_7", "day_14"):
        tpl = FOLLOWUP_TEMPLATES[day_key].get(language, FOLLOWUP_TEMPLATES[day_key]["en"])
        subj = fill_template(tpl["subject"], variables)
        body = fill_template(tpl["body"], variables)
        seq.append({
            "day": int(day_key.split("_")[1]),
            "subject": subj,
            "body": body,
            "word_count": word_count(body),
        })
    return seq


# ================================================================
# Pipeline main
# ================================================================

def generate_for_buyers(
    buyers: List[Dict[str, Any]],
    product_context: Dict[str, Any],
    *,
    default_customer_type: str = "Manufacturer",
    default_language: str = "en",
    include_followups: bool = True,
) -> Dict[str, Any]:
    """对一组 buyer（diligence 输出）批量生成邮件草稿。"""
    out_emails: List[Dict[str, Any]] = []
    errors: List[str] = []

    for buyer in buyers:
        ctype = buyer.get("customer_type") or default_customer_type
        lang = buyer.get("language") or default_language
        try:
            email = render_email(buyer, product_context,
                                 customer_type=ctype, language=lang)
            entry: Dict[str, Any] = {"email": email}
            if include_followups:
                entry["followup_sequence"] = render_followup_sequence(email, language=lang)
            entry["recommendation_next_step"] = (
                buyer.get("recommendation", {}).get("next_skill") or "(manual send)"
            )
            out_emails.append(entry)
        except (OutreachError, Exception) as exc:
            errors.append(f"buyer={buyer.get('importer_name', '?')}: {exc}")

    return {
        "$schema": "hlzd/cold-outreach/v1-batch",
        "product_context": product_context,
        "default_customer_type": default_customer_type,
        "default_language": default_language,
        "generated": len(out_emails),
        "failed": len(errors),
        "emails": out_emails,
        "errors": errors,
    }
