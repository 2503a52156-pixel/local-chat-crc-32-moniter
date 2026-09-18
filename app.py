
import streamlit as st
import zlib
import pandas as pd
from datetime import datetime
from error_simulation import simulate_error

st.set_page_config(
    page_title="CRC Sentinel Pro",
    page_icon="🛡️",
    layout="wide"
)

# ---------------- SESSION STATE ----------------

if "history" not in st.session_state:
    st.session_state.history = []

if "reference_crc" not in st.session_state:
    st.session_state.reference_crc = ""

if "reference_data" not in st.session_state:
    st.session_state.reference_data = b""

if "reference_label" not in st.session_state:
    st.session_state.reference_label = ""

if "last_result" not in st.session_state:
    st.session_state.last_result = None


# ---------------- CRC-32 FUNCTION ----------------

def crc32(data: bytes) -> str:
    return f"{zlib.crc32(data) & 0xFFFFFFFF:08X}"


# ---------------- ERROR SIMULATION ----------------

def simulate_error(data: bytes, error_type: str) -> bytes:
    if not data:
        return data

    value = bytearray(data)

    if error_type == "Change character":
        value[0] ^= 1

    elif error_type == "Add data":
        value.extend(b" CORRUPTED")

    elif error_type == "Remove data":
        del value[-1]

    elif error_type == "Multiple changes":
        value[0] ^= 1

        if len(value) > 3:
            value[3] ^= 8

    return bytes(value)


# ---------------- CUSTOM CSS ----------------

st.markdown("""
<style>
.main {
    background: #0b1120;
}

.block-container {
    padding-top: 2rem;
}

.metric-card {
    padding: 18px;
    border-radius: 14px;
    background: #151f35;
    border: 1px solid #263552;
}

.result-valid {
    padding: 22px;
    border-radius: 14px;
    background: #123d2c;
    color: #8affbd;
    font-size: 28px;
    font-weight: 700;
    text-align: center;
}

.result-bad {
    padding: 22px;
    border-radius: 14px;
    background: #4a1d2a;
    color: #ff9eae;
    font-size: 28px;
    font-weight: 700;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)


# ---------------- HEADER ----------------

st.title("🛡️ LOCAL CHAT MESSAGE CRC MONITOR")
st.caption("Python-based CRC-32 Message, File, Packet and Record Integrity Monitor")


# ---------------- SIDEBAR ----------------

with st.sidebar:

    st.header("⚙️ Workspace")

    source_type = st.radio(
        "Select input type",
        ["Message", "File", "Packet", "Record"]
    )

    error_type = st.selectbox(
        "Error simulation",
        [
            "No error",
            "Change character",
            "Add data",
            "Remove data",
            "Multiple changes"
        ]
    )

    st.divider()

    st.info(
        "CRC-32 detects accidental data changes by comparing "
        "reference and current checksums."
    )

    if st.button("🧹 Clear history", use_container_width=True):
        st.session_state.history = []
        st.success("History cleared.")


# ---------------- LAYOUT ----------------

left, right = st.columns([1.35, 1])


# ---------------- INPUT WORKSPACE ----------------

with left:

    st.subheader("📥 Input Workspace")

    original_data = b""
    input_name = source_type

    # MESSAGE INPUT
    if source_type == "Message":

        message = st.text_area(
            "Enter chat message",
            "Hello World",
            height=180
        )

        original_data = message.encode("utf-8")
        input_name = "Chat Message"

    # FILE INPUT
    elif source_type == "File":

        uploaded = st.file_uploader(
            "Upload a file",
            type=None
        )

        if uploaded:

            original_data = uploaded.getvalue()
            input_name = uploaded.name

            st.write(f"**File:** {uploaded.name}")
            st.write(f"**Size:** {len(original_data):,} bytes")

        else:
            st.warning("Please upload a file.")

    # PACKET INPUT
    elif source_type == "Packet":

        st.write("### 📦 Packet Details")

        packet_id = st.text_input(
            "Packet ID",
            "PKT-001"
        )

        packet_header = st.text_input(
            "Packet Header",
            "LOCAL-CHAT"
        )

        packet_payload = st.text_area(
            "Packet Payload",
            "Hello packet data",
            height=140
        )

        packet_text = (
            f"Packet ID: {packet_id}\n"
            f"Header: {packet_header}\n"
            f"Payload: {packet_payload}"
        )

        original_data = packet_text.encode("utf-8")
        input_name = f"Packet {packet_id}"

    # RECORD INPUT
    elif source_type == "Record":

        st.write("### 🧾 Record Details")

        record_id = st.text_input(
            "Record ID",
            "REC-001"
        )

        sender = st.text_input(
            "Sender",
            "User-A"
        )

        receiver = st.text_input(
            "Receiver",
            "User-B"
        )

        record_message = st.text_area(
            "Record Message",
            "Local chat record",
            height=140
        )

        record_text = (
            f"Record ID: {record_id}\n"
            f"Sender: {sender}\n"
            f"Receiver: {receiver}\n"
            f"Message: {record_message}"
        )

        original_data = record_text.encode("utf-8")
        input_name = f"Record {record_id}"

    st.write(f"**Input Type:** {source_type}")
    st.write(f"**Input Size:** {len(original_data):,} bytes")

    st.divider()

    c1, c2 = st.columns(2)

    # GENERATE REFERENCE CRC
    with c1:

        if st.button(
            "🔐 Generate Reference CRC",
            use_container_width=True
        ):

            if not original_data:

                st.error("Please provide input first.")

            else:

                st.session_state.reference_data = original_data
                st.session_state.reference_crc = crc32(original_data)
                st.session_state.reference_label = input_name
                st.session_state.last_result = None

                st.success("Reference CRC stored successfully.")

    # VERIFY CURRENT INPUT
    with c2:

        if st.button(
            "🧪 Verify Current Input",
            use_container_width=True
        ):

            if not original_data:

                st.error("Please provide input before verification.")

            elif not st.session_state.reference_crc:

                st.error("Generate a reference CRC first.")

            else:

                current_data = simulate_error(
                    original_data,
                    error_type
                )

                current_crc = crc32(current_data)

                valid = (
                    current_crc == st.session_state.reference_crc
                )

                result = "VALID" if valid else "CORRUPTED"

                st.session_state.history.append({

                    "Time": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                    "Input Type": source_type,

                    "Input": input_name,

                    "Simulation": error_type,

                    "Reference CRC": st.session_state.reference_crc,

                    "Current CRC": current_crc,

                    "Result": result,

                    "Bytes": len(current_data)

                })

                st.session_state.last_result = (
                    current_crc,
                    valid,
                    current_data
                )

                if valid:
                    st.success("Verification completed: VALID")

                else:
                    st.warning("Verification completed: CORRUPTED")


# ---------------- CRC ANALYSIS ----------------

with right:

    st.subheader("📊 CRC Analysis")

    reference = (
        st.session_state.reference_crc
        or "--------"
    )

    current = "--------"
    valid = None

    if st.session_state.last_result:

        current, valid, _ = st.session_state.last_result

    st.markdown(
        f"""
        <div class="metric-card">
            <b>Reference CRC-32</b>
            <h2>{reference}</h2>
            <small>{st.session_state.reference_label}</small>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    st.markdown(
        f"""
        <div class="metric-card">
            <b>Current CRC-32</b>
            <h2>{current}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    if valid is True:

        st.markdown(
            '<div class="result-valid">✅ VALID</div>',
            unsafe_allow_html=True
        )

    elif valid is False:

        st.markdown(
            '<div class="result-bad">⚠️ CORRUPTED</div>',
            unsafe_allow_html=True
        )

    else:

        st.info("Run verification to see the result.")


# ---------------- DATA PREVIEW ----------------

if st.session_state.last_result:

    _, _, current_data = st.session_state.last_result

    with st.expander("🔎 Reference and Current Data Preview"):

        st.write("Reference data:")

        st.code(
            st.session_state.reference_data[:500]
        )

        st.write("Current data:")

        st.code(
            current_data[:500]
        )


# ---------------- STATISTICS ----------------

st.divider()

st.subheader("📈 Dashboard Statistics")

records = st.session_state.history

valid_count = sum(
    x["Result"] == "VALID"
    for x in records
)

corrupt_count = sum(
    x["Result"] == "CORRUPTED"
    for x in records
)

m1, m2, m3, m4 = st.columns(4)

m1.metric("Total Tests", len(records))
m2.metric("Valid", valid_count)
m3.metric("Corrupted", corrupt_count)
m4.metric("Algorithm", "CRC-32")


# ---------------- HISTORY AND CSV REPORT ----------------

st.subheader("🧾 Verification History")

if records:

    df = pd.DataFrame(records)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    csv_data = df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "⬇️ Download CSV Report",
        csv_data,
        "crc_verification_report.csv",
        "text/csv"
    )

else:

    st.info("No verification records yet.")