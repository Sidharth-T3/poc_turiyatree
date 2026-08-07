"""Lead Automation — API Tester (Streamlit HTTP client).

Point it at any base URL (local docker or a deployed link) and exercise **every**
live endpoint. Makes real HTTP calls, exactly like n8n would.

Tabs → coverage:
  Capture       POST /api/lead-automation/lead
  Status writes #6 lead status · #1 dev contact-status · #8 GET task · #9 task status
  Logs          POST /log on lead / dev-lead / so
  Checks        #2 #4 #5 #7 #10 #12 (non-corporate / multi-location / do-not-assign)
  Fetch & SO    #3 enriched lead · #11 order (boundary) · #13 SO status
  Sidebar       GET /health
"""

import os

import requests
import streamlit as st
# from dotenv import load_dotenv

# load_dotenv()

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
        st.info("204 No Content")
        return
    try:
        st.json(resp.json())
    except ValueError:
        st.code(resp.text or "(empty body)")


if st.session_state.pop("_do_health", False):
    call("GET", "/health")

st.divider()

tab_capture, tab_status, tab_logs, tab_checks, tab_fetch = st.tabs(
    ["Capture", "Status writes", "Logs", "Checks", "Fetch & SO (3/11/13)"]
)

# ── Capture (POST /api/lead-automation/lead) ─────────────────────────────────
with tab_capture:
    st.caption("Store the info a user enters during a download into `lead_automation`.")
    with st.form("capture"):
        c1, c2, c3 = st.columns(3)
        email = c1.text_input("email *", "john@acmecorp.com")
        first_name = c2.text_input("first_name", "John")
        last_name = c3.text_input("last_name", "Smith")
        c4, c5, c6 = st.columns(3)
        company = c4.text_input("company", "Acme Corp")
        phone = c5.text_input("phone", "+1-408-555-0100")
        lead_source = c6.text_input("lead_source", "Web Download")
        c7, c8, c9 = st.columns(3)
        country = c7.text_input("country", "US")
        state = c8.text_input("state", "CA")
        city = c9.text_input("city", "San Jose")
        c10, c11, c12 = st.columns(3)
        designation = c10.text_input("designation", "Engineer")
        product_id = c11.text_input("product_id", "1024")
        product_name = c12.text_input("product_name", "See3CAM_CU81")
        c13, c14 = st.columns(2)
        psi = c13.text_input("psi", "See3CAM_CU81")
        download_id = c14.number_input("download_id", min_value=0, step=1, value=5001)
        description = st.text_input("description", "Downloaded datasheet")
        c15, c16 = st.columns(2)
        ip_address = c15.text_input("ip_address", "203.0.113.10")
        user_agent = c16.text_input("user_agent", "Mozilla/5.0")
        if st.form_submit_button("POST /api/lead-automation/lead"):
            body = {"email": email}
            for k, v in {
                "first_name": first_name, "last_name": last_name, "company": company,
                "phone": phone, "lead_source": lead_source, "country": country,
                "state": state, "city": city, "designation": designation,
                "product_id": product_id, "product_name": product_name, "psi": psi,
                "description": description, "ip_address": ip_address, "user_agent": user_agent,
            }.items():
                if v:
                    body[k] = v
            if download_id:
                body["download_id"] = int(download_id)
            call("POST", "/api/lead-automation/lead", body=body)

# ── Status writes (endpoints 1, 6, 9) ────────────────────────────────────────
with tab_status:
    st.caption("Match rows by **download_id**. `status` is a boolean.")

    with st.expander("POST /api/lead-automation/status (endpoint 6)", expanded=True):
        with st.form("lead_status"):
            s1, s2 = st.columns(2)
            did6 = s1.number_input("downloadId", min_value=1, step=1, key="did6")
            done6 = s2.checkbox("status (true = processed/done)", value=True)
            s3, s4, s5 = st.columns(3)
            contact6 = s3.text_input("contactId (→ zoho_contact_id)", "")
            lead6 = s4.text_input("leadId (→ zoho_lead_id)", "")
            task6 = s5.text_input("taskId", "")
            if st.form_submit_button("Send"):
                body = {"downloadId": int(did6), "status": done6}
                for k, v in {"contactId": contact6, "leadId": lead6, "taskId": task6}.items():
                    if v:
                        body[k] = v
                call("POST", "/api/lead-automation/status", body=body)

    with st.expander("POST /api/dev-lead-automation/contact-status (endpoint 1)"):
        with st.form("dev_status"):
            d1, d2 = st.columns(2)
            did1 = d1.number_input("downloadId", min_value=1, step=1, key="did1")
            done1 = d2.checkbox("isAutomationDone", value=True)
            contact1 = st.text_input("contactId (→ zoho_contact_id)", "", key="c1")
            if st.form_submit_button("Send"):
                body = {"downloadId": int(did1), "isAutomationDone": done1}
                if contact1:
                    body["contactId"] = contact1
                call("POST", "/api/dev-lead-automation/contact-status", body=body)

    with st.expander("GET /api/task/{downloadId} (endpoint 8)"):
        did8 = st.number_input("downloadId", min_value=1, step=1, key="did8")
        if st.button("Send", key="btn_get_task"):
            call("GET", f"/api/task/{int(did8)}")

    with st.expander("POST /api/task/status (endpoint 9) — two flags"):
        with st.form("task_status"):
            t1, t2, t3 = st.columns(3)
            did9 = t1.number_input("downloadId", min_value=1, step=1, key="did9")
            mailopen9 = t2.checkbox("is_mailopen_done", value=True)
            download9 = t3.checkbox("is_download_done", value=False)
            if st.form_submit_button("Send"):
                call("POST", "/api/task/status", body={
                    "downloadId": int(did9),
                    "is_mailopen_done": mailopen9,
                    "is_download_done": download9,
                })

# ── Logs (write per-action rows to the log_* tables) ─────────────────────────
with tab_logs:
    st.caption("Write a per-action row to a `log_*_automation` table. `processed_at` is DB-set.")

    with st.expander("POST /api/lead-automation/log", expanded=True):
        with st.form("lead_log"):
            l1, l2 = st.columns(2)
            ldid = l1.number_input("download_id", min_value=0, step=1, key="ldid")
            lemail = l2.text_input("email", "john@acmecorp.com", key="lemail")
            l3, l4 = st.columns(2)
            latype = l3.text_input("action_type", "create_contact")
            lares = l4.text_input("action_result", "success")
            ldet = st.text_input("action_result_details", "")
            lzoho = st.text_input("zoho_record_id", "")
            if st.form_submit_button("Send"):
                body = {}
                for k, v in {"download_id": int(ldid) or None, "email": lemail,
                             "action_type": latype, "action_result": lares,
                             "action_result_details": ldet, "zoho_record_id": lzoho}.items():
                    if v:
                        body[k] = v
                call("POST", "/api/lead-automation/log", body=body)

    with st.expander("POST /api/dev-lead-automation/log"):
        with st.form("dev_log"):
            d1, d2 = st.columns(2)
            ddid = d1.number_input("download_id", min_value=0, step=1, key="ddid")
            demail = d2.text_input("email", "qa@devclient.com", key="demail")
            d3, d4 = st.columns(2)
            datype = d3.text_input("action_type", "create_contact")
            dares = d4.text_input("action_result", "success")
            ddet = st.text_input("action_result_details", "", key="ddet")
            if st.form_submit_button("Send"):
                body = {}
                for k, v in {"download_id": int(ddid) or None, "email": demail,
                             "action_type": datype, "action_result": dares,
                             "action_result_details": ddet}.items():
                    if v:
                        body[k] = v
                call("POST", "/api/dev-lead-automation/log", body=body)

    with st.expander("POST /api/so-automation/log"):
        with st.form("so_log"):
            so1, so2 = st.columns(2)
            sonum = so1.text_input("so_number", "SO-13564")
            soemail = so2.text_input("email", "dan.nguyen@noveldev.com", key="soemail")
            so3, so4 = st.columns(2)
            soatype = so3.text_input("action_type", "create_order")
            soares = so4.text_input("action_result", "success")
            sodet = st.text_input("action_result_details", "", key="sodet")
            if st.form_submit_button("Send"):
                body = {}
                for k, v in {"so_number": sonum, "email": soemail, "action_type": soatype,
                             "action_result": soares, "action_result_details": sodet}.items():
                    if v:
                        body[k] = v
                call("POST", "/api/so-automation/log", body=body)

# ── Checks ────────────────────────────────────────────────────────────────────
with tab_checks:
    st.caption("Backed by the real DevAdmin config tables. Use values that exist in the data.")

    with st.expander("GET /api/lead-automation/non-corporate-domains — full list", expanded=True):
        if st.button("Send", key="noncorp_list"):
            call("GET", "/api/lead-automation/non-corporate-domains")

    with st.expander("GET /api/lead-automation/multilocation-domain/{domain}"):
        d = st.text_input("domain", "samsung.com", key="ml_lead")
        if st.button("Send", key="btn_ml_lead"):
            call("GET", f"/api/lead-automation/multilocation-domain/{d}")

    with st.expander("GET /api/lead-automation/do-not-assign-country/{country}"):
        c = st.text_input("country", "Argentina", key="dna")
        if st.button("Send", key="btn_dna"):
            call("GET", f"/api/lead-automation/do-not-assign-country/{c}")

    with st.expander("GET /api/dev-lead-automation/non-corporate-domain/{domain}"):
        d = st.text_input("domain", "gmail.com", key="dev_nc")
        if st.button("Send", key="btn_dev_nc"):
            call("GET", f"/api/dev-lead-automation/non-corporate-domain/{d}")

    with st.expander("GET /api/so-automation/multilocation-domain/{domain}"):
        d = st.text_input("domain", "samsung.com", key="so_ml")
        if st.button("Send", key="btn_so_ml"):
            call("GET", f"/api/so-automation/multilocation-domain/{d}")

    with st.expander("GET /api/so-automation/non-corporate-domain/{domain}"):
        d = st.text_input("domain", "gmail.com", key="so_nc")
        if st.button("Send", key="btn_so_nc"):
            call("GET", f"/api/so-automation/non-corporate-domain/{d}")

# ── Fetch & SO (endpoints 3 / 11 / 13) ───────────────────────────────────────
with tab_fetch:
    st.caption("Enriched fetches (DevAdmin + econ boundary) and SO status. Needs the "
               "API's INTEGRATION_API_KEY set for product/order enrichment.")

    with st.expander("GET /api/lead-automation/download — enriched lead (endpoint 3)", expanded=True):
        c1, c2 = st.columns([2, 1])
        did3 = c1.number_input("download_id", min_value=0, step=1, key="did3")
        if c1.button("Get by id", key="btn_d3_id"):
            call("GET", f"/api/lead-automation/download/{int(did3)}")
        if c2.button("Get last", key="btn_d3_last"):
            call("GET", "/api/lead-automation/download")

    with st.expander("GET /api/so-automation/order — full order (endpoint 11)"):
        o1, o2 = st.columns([2, 1])
        oid = o1.number_input("orderId (display_id)", min_value=0, step=1, key="oid11")
        if o1.button("Get by id", key="btn_o11_id"):
            call("GET", f"/api/so-automation/order/{int(oid)}")
        if o2.button("Get last", key="btn_o11_last"):
            call("GET", "/api/so-automation/order")

    with st.expander("POST /api/so-automation/status (endpoint 13)"):
        with st.form("so_status"):
            s1, s2, s3 = st.columns(3)
            oid13 = s1.number_input("orderId", min_value=1, step=1, key="oid13")
            sonum13 = s2.text_input("soNumber", "SO-13564")
            done13 = s3.checkbox("status (done)", value=True)
            if st.form_submit_button("Send"):
                call("POST", "/api/so-automation/status", body={
                    "orderId": int(oid13), "soNumber": sonum13, "status": done13,
                })
