"""Biometric profile and simple vitals logging (Streamlit)."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from database import Database


def add_biometric_widgets_to_sidebar():
    if "user_id" not in st.session_state or st.session_state.user_id is None:
        return
    db = Database()
    if not db.is_connected():
        return
    profile = db.get_user_biometric_profile(st.session_state.user_id)
    st.sidebar.markdown("#### 💓 Biometrics")
    if profile:
        bmi = _bmi(profile["height_cm"], profile["weight_kg"])
        st.sidebar.caption(
            f"{profile['weight_kg']:.1f} kg · {profile['height_cm']:.0f} cm"
            + (f" · BMI {bmi:.1f}" if bmi else "")
        )
        if profile.get("resting_hr"):
            st.sidebar.caption(f"Resting HR ~ {int(profile['resting_hr'])} bpm")
    else:
        st.sidebar.caption("Complete your profile on the Biometric page.")


def biometric_profile_setup_page():
    st.title("💓 Biometric profile")
    st.caption("Save baseline metrics for recovery load and dashboard context.")

    if "user_id" not in st.session_state or st.session_state.user_id is None:
        st.warning("Please log in first.")
        return

    db = Database()
    if not db.is_connected():
        st.error("Database connection error.")
        return

    existing = db.get_user_biometric_profile(st.session_state.user_id)

    with st.form("biometric_profile_form"):
        height = st.number_input(
            "Height (cm)",
            min_value=50.0,
            max_value=260.0,
            value=float(existing["height_cm"]) if existing else 170.0,
            step=0.5,
        )
        weight = st.number_input(
            "Weight (kg)",
            min_value=20.0,
            max_value=400.0,
            value=float(existing["weight_kg"]) if existing else 70.0,
            step=0.1,
        )
        resting = st.number_input(
            "Resting heart rate (bpm, optional)",
            min_value=0,
            max_value=220,
            value=int(existing["resting_hr"] or 0) if existing else 0,
            step=1,
        )
        sex = st.selectbox(
            "Sex (optional)",
            ["", "female", "male", "other"],
            index=_sex_index(existing.get("sex") if existing else None),
        )
        submitted = st.form_submit_button("Save profile", use_container_width=True)

    if submitted:
        resting_hr = resting if resting > 0 else None
        sex_val = sex if sex else None
        if db.save_biometric_profile(
            st.session_state.user_id,
            height,
            weight,
            resting_hr,
            sex_val,
        ):
            st.success("Profile saved.")
            st.session_state.page = "biometric"
            st.rerun()
        else:
            st.error("Could not save profile.")


def biometric_dashboard_page():
    st.title("💓 Biometric dashboard")

    if "user_id" not in st.session_state or st.session_state.user_id is None:
        st.warning("Please log in first.")
        return

    db = Database()
    if not db.is_connected():
        st.error("Database connection error.")
        return

    profile = db.get_user_biometric_profile(st.session_state.user_id)
    if not profile:
        st.info("No profile yet — you will be redirected to setup.")
        return

    bmi = _bmi(profile["height_cm"], profile["weight_kg"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Height", f"{profile['height_cm']:.0f} cm")
    c2.metric("Weight", f"{profile['weight_kg']:.1f} kg")
    c3.metric("BMI", f"{bmi:.1f}" if bmi else "—")
    c4.metric(
        "Resting HR",
        f"{int(profile['resting_hr'])} bpm" if profile.get("resting_hr") else "—",
    )

    st.markdown("---")
    st.subheader("Log a check-in")

    with st.form("biometric_reading_form"):
        rw = st.number_input("Weight (kg, optional)", min_value=0.0, max_value=400.0, value=0.0, step=0.1)
        rh = st.number_input("Heart rate (bpm, optional)", min_value=0, max_value=220, value=0, step=1)
        rs = st.number_input("Sleep (hours, optional)", min_value=0.0, max_value=24.0, value=0.0, step=0.25)
        rn = st.text_input("Notes (optional)")
        add = st.form_submit_button("Add entry", use_container_width=True)

    if add:
        ok = db.add_biometric_reading(
            st.session_state.user_id,
            weight_kg=rw if rw > 0 else None,
            hr_bpm=rh if rh > 0 else None,
            sleep_hours=rs if rs > 0 else None,
            notes=rn.strip() or None,
        )
        if ok:
            st.success("Entry saved.")
            st.rerun()
        else:
            st.error("Could not save entry.")

    readings = db.get_biometric_readings(st.session_state.user_id, limit=120)
    st.markdown("---")
    st.subheader("History")
    if not readings:
        st.info("No check-ins yet. Add weight, HR, or sleep above.")
        return

    df = pd.DataFrame(readings)
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    df = df.sort_values("recorded_at")

    show = df[["recorded_at", "weight_kg", "hr_bpm", "sleep_hours", "notes"]].copy()
    st.dataframe(show.sort_values("recorded_at", ascending=False), use_container_width=True, hide_index=True)

    plot_df = df.dropna(subset=["weight_kg"], how="all")
    if plot_df["weight_kg"].notna().any():
        fig = px.line(
            plot_df,
            x="recorded_at",
            y="weight_kg",
            markers=True,
            title="Logged weight (kg)",
        )
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)


def _bmi(height_cm: float, weight_kg: float) -> float | None:
    if not height_cm or height_cm <= 0:
        return None
    h_m = height_cm / 100.0
    return weight_kg / (h_m * h_m)


def _sex_index(saved: str | None) -> int:
    opts = ["", "female", "male", "other"]
    if not saved:
        return 0
    try:
        return opts.index(saved)
    except ValueError:
        return 0
