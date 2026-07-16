"""Lead Automation — API Tester (Streamlit HTTP client).

Point it at any base URL (local docker or a deployed link) and exercise every
Phase-1 endpoint. This does NOT touch the database directly — it makes real HTTP
calls, exactly like n8n would, and shows the status code + JSON response.
"""

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="API Tester", page_icon="🧪", layout="wide")
st.title("🧪 Lead Automation — API Tester")

# ── Connection settings ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Connection")
    base_url = st.text_input(
        "Base URL",
        value=os.getenv("API_BASE_URL", "http://localhost:8000"),
        help="Local docker → http://localhost:8000 · Deployed → your https link",
    ).rstrip("/")
    api_key = st.text_input("X-API-Key (optional)", value=os.getenv("API_KEY", ""), type="password")
    timeout = st.number_input("Timeout (s)", min_value=1, max_value=120, value=30)
    st.caption("Health check:")
    if st.button("Ping /health", use_container_width=True):
        st.session_state["_do_health"] = True


def headers() -> dict:
    return {"X-API-Key": api_key} if api_key else {}


def call(method: str, path: str, *, params: dict | None = None, body: dict | None = None) -> None:
    """Make the request and render status + body."""
    url = f"{base_url}{path}"
    st.caption(f"`{method} {url}`" + (f"  ·  params={params}" if params else ""))
    try:
        resp = requests.request(
            method, url, params=params, json=body, headers=headers(), timeout=timeout
        )
    except Exception as e:
        st.error(f"Request failed: {e}")
        return

    line = f"{method} → {resp.status_code} {resp.reason}"
    (st.success if resp.status_code < 300 else st.error)(line)

    if resp.status_code == 204 or not resp.content:
        st.info("204 No Content — nothing to process (missing / done / duplicate / abandoned).")
        return
    try:
        st.json(resp.json())
    except ValueError:
        st.code(resp.text or "(empty body)")


if st.session_state.pop("_do_health", False):
    call("GET", "/health")

st.divider()

tab_lead, tab_dev, tab_admin, tab_internal = st.tabs(
    ["Lead Automation", "Dev Lead Automation", "Admin / Seed", "Internal (config / queues / profiles)"]
)

# ── Lead Automation (endpoints 3–7 + capture + claim) ────────────────────────
with tab_lead:
    with st.expander("POST /api/lead-automation/download — capture a submission", expanded=True):
        with st.form("capture"):
            c1, c2, c3 = st.columns(3)
            email = c1.text_input("email", "john@acmecorp.com")
            product_name = c2.text_input("product_name", "See3CAM_CU81")
            downloaded_from = c3.selectbox("downloaded_from", ["main", "dev"])
            c4, c5, c6 = st.columns(3)
            company_name = c4.text_input("company_name", "Acme Corp")
            last_name = c5.text_input("last_name", "Smith")
            lead_source = c6.text_input("lead_source", "Web Download")
            c7, c8, c9 = st.columns(3)
            country = c7.text_input("country", "US")
            state = c8.text_input("state", "CA")
            send_newsletter = c9.checkbox("send_newsletter", value=True)
            dt = st.text_input("downloaded_date_time (ISO)", "2026-07-10T10:00:00Z")
            if st.form_submit_button("Send"):
                call("POST", "/api/lead-automation/download", body={
                    "email": email, "product_name": product_name,
                    "downloaded_from": downloaded_from, "company_name": company_name,
                    "last_name": last_name, "lead_source": lead_source,
                    "country": country, "state": state,
                    "send_newsletter": send_newsletter, "downloaded_date_time": dt,
                })

    with st.expander("GET /api/lead-automation/download/{downloadId} — enriched fetch by id (endpoint 3)"):
        did = st.number_input("downloadId", min_value=1, step=1, key="get_by_id")
        if st.button("Send", key="btn_get_by_id"):
            call("GET", f"/api/lead-automation/download/{int(did)}")

    with st.expander("GET /api/lead-automation/claim — poll oldest pending (internal)"):
        df = st.selectbox("downloaded_from", ["main", "dev"], key="claim_from")
        if st.button("Send", key="btn_claim"):
            call("GET", "/api/lead-automation/claim", params={"downloaded_from": df})

    with st.expander("POST /api/lead-automation/status — main-path idempotency write (endpoint 6)"):
        with st.form("lead_status"):
            s1, s2 = st.columns(2)
            sid = s1.number_input("downloadId", min_value=1, step=1, key="status_id")
            done = s2.checkbox("status (true = automation done)", value=True)
            s3, s4, s5 = st.columns(3)
            contact_id = s3.text_input("contactId", "")
            lead_id = s4.text_input("leadId", "")
            task_id = s5.text_input("taskId", "")
            if st.form_submit_button("Send"):
                body = {"downloadId": int(sid), "status": done}
                if contact_id:
                    body["contactId"] = contact_id
                if lead_id:
                    body["leadId"] = lead_id
                if task_id:
                    body["taskId"] = task_id
                call("POST", "/api/lead-automation/status", body=body)

    with st.expander("GET /api/lead-automation/non-corporate-domains — list (endpoint 4)"):
        if st.button("Send", key="btn_noncorp_list"):
            call("GET", "/api/lead-automation/non-corporate-domains")

    with st.expander("GET /api/lead-automation/multilocation-domain/{domain} (endpoint 5)"):
        dom = st.text_input("domain", "acmecorp.com", key="ml_domain")
        if st.button("Send", key="btn_ml"):
            call("GET", f"/api/lead-automation/multilocation-domain/{dom}")

    with st.expander("GET /api/lead-automation/do-not-assign-country/{country} (endpoint 7)"):
        ctry = st.text_input("country", "USA", key="dna_country")
        if st.button("Send", key="btn_dna"):
            call("GET", f"/api/lead-automation/do-not-assign-country/{ctry}")

# ── Dev Lead Automation (endpoints 1–2) ──────────────────────────────────────
with tab_dev:
    with st.expander("POST /api/dev-lead-automation/contact-status (endpoint 1)", expanded=True):
        with st.form("dev_contact_status"):
            d1, d2 = st.columns(2)
            dsid = d1.number_input("downloadId", min_value=1, step=1, key="dev_status_id")
            dev_done = d2.checkbox("isAutomationDone", value=True)
            dev_contact = st.text_input("contactId", "")
            if st.form_submit_button("Send"):
                body = {"downloadId": int(dsid), "isAutomationDone": dev_done}
                if dev_contact:
                    body["contactId"] = dev_contact
                call("POST", "/api/dev-lead-automation/contact-status", body=body)

    with st.expander("GET /api/dev-lead-automation/non-corporate-domain/{domain} (endpoint 2)"):
        dev_dom = st.text_input("domain", "gmail.com", key="dev_domain")
        if st.button("Send", key="btn_dev_dom"):
            call("GET", f"/api/dev-lead-automation/non-corporate-domain/{dev_dom}")

# ── Admin / Seed (reference tables) ──────────────────────────────────────────
with tab_admin:
    st.caption(
        "Seed / update / delete reference tables via `/v1/admin/{resource}`. "
        "POST upserts on the natural key (idempotent). ⚠ unauthenticated — dev only."
    )
    resource = st.selectbox(
        "resource", ["product-mapper", "geo-state", "geo-country", "config-list"]
    )

    _SAMPLES = {
        "product-mapper": '[\n  {"econ_product_name": "See3CAM_CU81", "product_name": "See3CAM_CU81", "business_unit": "USB"}\n]',
        "geo-state": '[\n  {"abbreviation": "CA", "name": "California", "lead_owner_id": "38660000..."}\n]',
        "geo-country": '[\n  {"two_letter_iso_code": "IN", "name": "India", "lead_owner_id": "38660000..."}\n]',
        "config-list": '[\n  {"list_name": "non_corporate_domains", "value": "gmail.com"},\n  {"list_name": "unqualified_products", "value": "denebola"}\n]',
    }

    with st.expander(f"GET /v1/admin/{resource} — list all", expanded=True):
        if st.button("Send", key="btn_admin_list"):
            call("GET", f"/v1/admin/{resource}")

    with st.expander(f"POST /v1/admin/{resource} — bulk upsert (seed)"):
        body_text = st.text_area("JSON array of rows", _SAMPLES[resource], height=140, key="admin_body")
        if st.button("Send", key="btn_admin_post"):
            import json
            try:
                parsed = json.loads(body_text)
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
            else:
                call("POST", f"/v1/admin/{resource}", body=parsed)

    with st.expander(f"PUT /v1/admin/{resource}/{{id}} — update one"):
        pu1, pu2 = st.columns([1, 3])
        put_id = pu1.number_input("id", min_value=1, step=1, key="admin_put_id")
        put_body = pu2.text_area("fields to update (JSON object)", '{"business_unit": "NVIDIA"}', key="admin_put_body")
        if st.button("Send", key="btn_admin_put"):
            import json
            try:
                parsed = json.loads(put_body)
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
            else:
                call("PUT", f"/v1/admin/{resource}/{int(put_id)}", body=parsed)

    with st.expander(f"DELETE /v1/admin/{resource} — single or bulk"):
        d1, d2 = st.columns(2)
        del_one = d1.number_input("delete single id", min_value=0, step=1, key="admin_del_one")
        if d1.button("Delete one", key="btn_admin_del_one"):
            call("DELETE", f"/v1/admin/{resource}/{int(del_one)}")
        del_ids = d2.text_input("bulk ids (comma-separated)", "", key="admin_del_ids")
        if d2.button("Bulk delete", key="btn_admin_del_bulk"):
            ids = [int(x) for x in del_ids.split(",") if x.strip().isdigit()]
            call("DELETE", f"/v1/admin/{resource}", body={"ids": ids})


# ── Internal endpoints ────────────────────────────────────────────────────────
with tab_internal:
    with st.expander("GET /v1/config/{list_name}"):
        lst = st.selectbox(
            "list_name",
            ["non_corporate_domains", "unqualified_products", "multi_location_domains",
             "do_not_assign_countries", "geography_owner_map"],
        )
        if st.button("Send", key="btn_config"):
            call("GET", f"/v1/config/{lst}")

    with st.expander("POST /v1/fallback — record a failure (R-N8N-06)"):
        with st.form("fallback"):
            f1, f2 = st.columns(2)
            f_did = f1.number_input("download_id", min_value=0, step=1, key="fb_id")
            f_node = f2.text_input("node_name", "Zoho: Create Contact")
            f_err = st.text_input("error_message", "503 Service Unavailable")
            if st.form_submit_button("Send"):
                call("POST", "/v1/fallback", body={
                    "download_id": int(f_did) or None,
                    "node_name": f_node, "error_message": f_err,
                })

    with st.expander("POST /v1/qualification-queue — human review (R-N8N-13)"):
        with st.form("qual"):
            q1, q2 = st.columns(2)
            q_did = q1.number_input("download_id", min_value=0, step=1, key="q_id")
            q_reason = q2.text_input("reason", "non_corporate_email")
            q_data = st.text_input("lead_data_json", '{"email":"john@gmail.com"}')
            if st.form_submit_button("Send"):
                call("POST", "/v1/qualification-queue", body={
                    "download_id": int(q_did) or None,
                    "reason": q_reason, "lead_data_json": q_data,
                })

    with st.expander("GET / PUT /v1/profiles/{type}/{id} — profile cache"):
        p1, p2 = st.columns(2)
        p_type = p1.text_input("profile_type", "user", key="p_type")
        p_id = p2.text_input("profile_id", "42", key="p_id")
        p_data = st.text_area("data_json (for PUT)", '{"first_name":"John"}')
        b1, b2 = st.columns(2)
        if b1.button("GET", key="btn_prof_get"):
            call("GET", f"/v1/profiles/{p_type}/{p_id}")
        if b2.button("PUT", key="btn_prof_put"):
            call("PUT", f"/v1/profiles/{p_type}/{p_id}", body={"data_json": p_data})
