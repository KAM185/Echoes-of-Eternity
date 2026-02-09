import streamlit as st
from PIL import Image
import io

from utils import (
    analyze_monument,
    enhance_image_for_display,
    draw_damage_overlay,
)

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Echoes of Eternity",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None

# -------------------------------------------------
# HERO
# -------------------------------------------------
st.title("Echoes of Eternity")
st.caption("When ancient stones finally speak.")

# -------------------------------------------------
# IMAGE UPLOAD
# -------------------------------------------------
uploaded = st.file_uploader(
    "Upload a monument image (JPG/PNG)",
    type=["jpg", "jpeg", "png"]
)

if uploaded:
    st.session_state.image_bytes = uploaded.read()

    original_image = Image.open(
        io.BytesIO(st.session_state.image_bytes)
    ).convert("RGB")

    enhance_toggle = st.toggle(
        "Enhance image for viewing (display only)",
        value=True
    )

    display_image = (
        enhance_image_for_display(original_image)
        if enhance_toggle
        else original_image
    )

    st.image(
        display_image,
        caption="Enhanced view" if enhance_toggle else "Original view",
        use_container_width=True,
    )

    if st.button("Awaken the Echo"):
        with st.spinner("Listening across centuries…"):
            st.session_state.analysis = analyze_monument(
                image_bytes=st.session_state.image_bytes,  # ORIGINAL ONLY
                api_key=st.secrets["GEMINI_API_KEY"],
            )

# -------------------------------------------------
# RESULTS
# -------------------------------------------------
res = st.session_state.analysis

if res:
    st.subheader("Monument Identification")
    ident = res["monument_identification"]
    st.write(f"**Name:** {ident['name']}")
    st.write(f"**Location:** {ident['city']}, {ident['country']}")
    st.write(f"**Confidence Score:** {ident['confidence_score']}")

    st.subheader("Architectural Analysis")
    arch = res["architectural_analysis"]
    st.write(f"**Style:** {arch['style']}")
    st.write(f"**Period / Dynasty:** {arch['period_or_dynasty']}")
    st.write("**Primary Materials:**", arch["primary_materials"])
    st.write("**Notable Features:**", arch["distinct_features_visible"])

    st.subheader("Historical Context")
    st.write(res["historical_facts"]["summary"])

    st.subheader("Visible Damage Assessment")
    damages = res["visible_damage_assessment"]

    if damages and damages[0]["damage_type"] != "no visible damage observed":
        overlay = draw_damage_overlay(original_image, damages)
        st.image(overlay, caption="Detected damage zones", use_container_width=True)
    else:
        st.info("No visible major damage detected.")

    st.subheader("Restoration Guidance")
    rest = res["restoration_guidance"]
    st.write(f"**Can be restored:** {rest['can_be_restored']}")
    st.write("**Recommended Methods:**", rest["recommended_methods"])
    st.write("**Preventive Measures:**", rest["preventive_measures"])

    story = res["first_person_narrative"]["story_from_monument_perspective"]
    if story:
        st.subheader("The Monument Speaks")
        st.write(story)

