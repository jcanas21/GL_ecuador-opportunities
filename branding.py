from __future__ import annotations

import base64
import html
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
GROWTH_LAB_LOGO = ASSETS / "growth_lab_logo_black.png"
ECUADOR_FLAG = ASSETS / "bandera_ecuador.svg"


@st.cache_data(show_spinner=False)
def _image_to_data_uri(path: str) -> str:
    raw = Path(path).read_bytes()
    ext = Path(path).suffix.lower()
    mime = "image/png"
    if ext == ".svg":
        mime = "image/svg+xml"
    elif ext in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif ext == ".webp":
        mime = "image/webp"
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def inject_branding_css() -> None:
    st.markdown(
        """
<style>
.gl-header {
  padding: 0.4rem 0 1.35rem 0;
  margin: 0 0 1.6rem 0;
  border-bottom: 1px solid rgba(15, 23, 42, 0.12);
}
.gl-header-grid {
  display: grid;
  grid-template-columns: 150px minmax(0, 1fr) 240px;
  align-items: center;
  column-gap: 1.75rem;
}
.gl-flag-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
}
.gl-flag-wrap img {
  width: 120px;
  max-width: 100%;
  border-radius: 14px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
  background: #ffffff;
}
.gl-title-wrap h1 {
  margin: 0;
  font-size: 3.15rem;
  line-height: 1.05;
  font-weight: 700;
  color: #2f3241;
  letter-spacing: -0.03em;
}
.gl-title-wrap p {
  margin: 0.9rem 0 0 0;
  font-size: 1.02rem;
  line-height: 1.55;
  color: #6b7280;
}
.gl-logo-wrap {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}
.gl-logo-wrap img {
  width: 200px;
  max-width: 100%;
}
@media (max-width: 900px) {
  .gl-header-grid {
    grid-template-columns: 1fr;
    row-gap: 1rem;
  }
  .gl-flag-wrap,
  .gl-logo-wrap {
    justify-content: flex-start;
  }
  .gl-title-wrap h1 {
    font-size: 2.4rem;
  }
  .gl-logo-wrap img {
    width: 180px;
  }
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_dashboard_header(title: str, subtitle: str) -> None:
    inject_branding_css()
    logo_src = _image_to_data_uri(str(GROWTH_LAB_LOGO))
    flag_src = _image_to_data_uri(str(ECUADOR_FLAG))
    st.markdown(
        f"""
<div class="gl-header">
  <div class="gl-header-grid">
    <div class="gl-flag-wrap">
      <img src="{flag_src}" alt="Bandera del Ecuador" />
    </div>
    <div class="gl-title-wrap">
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(subtitle)}</p>
    </div>
    <div class="gl-logo-wrap">
      <img src="{logo_src}" alt="Growth Lab" />
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
