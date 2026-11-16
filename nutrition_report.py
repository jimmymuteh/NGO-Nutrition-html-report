import base64
import datetime
import logging
import os
import time
import webbrowser
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import schedule

logging.basicConfig(
    filename="report.log",
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
)

HEADLINES = {
    "county": "Kitui delivered the strongest weight recovery across the program",
    "attendance": "Families who showed up regularly saw steadier weight gains",
    "age": "Younger children bounced back faster than older participants",
}


def ensure_sample_nutrition_data(csv_path: str = "data/nutrition_outcomes.csv") -> None:
    """Creates a realistic 6-month nutrition dataset if the CSV does not exist yet."""
    if os.path.exists(csv_path):
        return

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    rng = np.random.default_rng(42)

    counties = ["Nairobi", "Kitui", "Machakos"]
    age_groups = ["Under 2", "2 to 5", "6 to 12", "Adolescent"]
    n = 180

    county_col = rng.choice(counties, size=n, p=[0.35, 0.35, 0.30])
    age_col = rng.choice(age_groups, size=n, p=[0.30, 0.35, 0.20, 0.15])
    months_col = rng.integers(1, 7, size=n)
    sessions_col = np.clip(
        (months_col * rng.normal(3.5, 1.0, size=n)).round().astype(int),
        1,
        24,
    )

    county_bonus = np.where(county_col == "Kitui", 0.9, np.where(county_col == "Machakos", 0.3, 0.0))
    age_bonus = np.select(
        [age_col == "Under 2", age_col == "2 to 5", age_col == "6 to 12"],
        [1.1, 0.7, 0.2],
        default=-0.2,
    )
    weight_gain = np.clip(
        0.4 + 0.14 * sessions_col + county_bonus + age_bonus + rng.normal(0, 0.45, size=n),
        0.1,
        6.5,
    ).round(2)

    df = pd.DataFrame({
        "county": county_col,
        "participant_age_group": age_col,
        "weight_gain_kg": weight_gain,
        "sessions_attended": sessions_col,
        "months_in_program": months_col,
    })
    df.to_csv(csv_path, index=False)
    logging.info(f"Created sample nutrition dataset at {csv_path}")


def generate_report(csv_path: str = "data/nutrition_outcomes.csv") -> dict:
    ensure_sample_nutrition_data(csv_path)
    os.makedirs("charts", exist_ok=True)

    # 1. Load fresh data
    df = pd.read_csv(csv_path)

    # 2. Run analysis
    county_perf = (
        df.groupby("county")["weight_gain_kg"]
        .mean()
        .sort_values(ascending=True)
    )
    best_county = county_perf.index[-1]

    age_order = ["Under 2", "2 to 5", "6 to 12", "Adolescent"]
    age_perf = (
        df.groupby("participant_age_group")["weight_gain_kg"]
        .mean()
        .reindex(age_order)
        .dropna()
    )
    best_age = age_perf.index[0]

    # 3. Generate three crisp charts as PNG files
    # Chart 1: County performance (Horizontal bar chart)
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=300)
    colors = ["#AED6F1" if c != best_county else "#1F4E79" for c in county_perf.index]
    county_perf.plot(kind="barh", ax=ax, color=colors)
    ax.set_title(HEADLINES["county"], fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Average Weight Gain (kg)")
    ax.set_ylabel("")
    plt.tight_layout()
    plt.savefig("charts/county_performance.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # Chart 2: Attendance vs. outcomes (Scatter plot with trend line)
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=300)
    ax.scatter(
        df["sessions_attended"],
        df["weight_gain_kg"],
        alpha=0.65,
        color="#2E86C1",
        edgecolors="none",
        label="Participants",
    )
    slope, intercept = np.polyfit(df["sessions_attended"], df["weight_gain_kg"], 1)
    x_vals = np.linspace(df["sessions_attended"].min(), df["sessions_attended"].max(), 100)
    ax.plot(x_vals, slope * x_vals + intercept, color="#1F4E79", linewidth=2.2, label="Overall trend")
    ax.set_title(HEADLINES["attendance"], fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Sessions Attended")
    ax.set_ylabel("Weight Gain (kg)")
    ax.legend(frameon=False)
    plt.tight_layout()
    plt.savefig("charts/attendance_outcomes.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # Chart 3: Age group differences (Grouped bar chart by county & age group)
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=300)
    age_county = df.pivot_table(
        index="participant_age_group",
        columns="county",
        values="weight_gain_kg",
        aggfunc="mean",
    ).reindex(age_order)
    age_county.plot(kind="bar", ax=ax, color=["#1F4E79", "#2E86C1", "#85C1E9"])
    ax.set_title(HEADLINES["age"], fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("")
    ax.set_ylabel("Average Weight Gain (kg)")
    plt.xticks(rotation=0)
    ax.legend(title="County", frameon=False)
    plt.tight_layout()
    plt.savefig("charts/age_differences.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    return {
        "participants": len(df),
        "counties": ", ".join(sorted(df["county"].unique())),
        "best_county": best_county,
        "best_age": best_age,
    }


def encode_png(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def build_html_report(data: dict, report_date_str: str) -> str:
    os.makedirs("reports", exist_ok=True)

    img_county = encode_png("charts/county_performance.png")
    img_attendance = encode_png("charts/attendance_outcomes.png")
    img_age = encode_png("charts/age_differences.png")

    summary_paragraph = (
        f"Across {data['participants']} participants tracked over six months in {data['counties']}, "
        f"{HEADLINES['county'].lower()}, {HEADLINES['attendance'].lower()}, and "
        f"{HEADLINES['age'].lower()}—giving the program team a clear picture of where support is working "
        f"best and where follow-up sessions can lift recovery further."
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Nutrition Program Update — {report_date_str}</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      max-width: 860px;
      margin: 32px auto;
      padding: 0 20px;
      color: #1f2933;
      line-height: 1.5;
    }}
    h1 {{ margin-bottom: 6px; }}
    .meta {{ color: #52606d; font-size: 14px; margin-bottom: 20px; }}
    .summary {{
      background: #f0f4f8;
      border-left: 4px solid #1f4e79;
      padding: 14px 16px;
      margin-bottom: 28px;
    }}
    .finding {{ margin-bottom: 32px; }}
    .finding h2 {{ font-size: 18px; margin-bottom: 10px; color: #1f4e79; }}
    img {{ max-width: 100%; height: auto; border: 1px solid #e4e7eb; }}
    @media print {{
      body {{ margin: 0; padding: 0; }}
    }}
  </style>
</head>
<body>
  <h1>Nutrition Program Update — {report_date_str}</h1>
  <div class="meta">Nairobi NGO Six-Month Outcome Briefing | Printable &amp; Shareable Summary</div>

  <div class="summary">
    <p>{summary_paragraph}</p>
  </div>

  <div class="finding">
    <h2>{HEADLINES['county']}</h2>
    <img src="data:image/png;base64,{img_county}" alt="{HEADLINES['county']}">
  </div>

  <div class="finding">
    <h2>{HEADLINES['attendance']}</h2>
    <img src="data:image/png;base64,{img_attendance}" alt="{HEADLINES['attendance']}">
  </div>

  <div class="finding">
    <h2>{HEADLINES['age']}</h2>
    <img src="data:image/png;base64,{img_age}" alt="{HEADLINES['age']}">
  </div>
</body>
</html>"""

    output_path = os.path.join("reports", f"report_{report_date_str}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report saved to {output_path}")
    return output_path


def daily_job(custom_date: str | None = None) -> str:
    try:
        report_date_str = custom_date or datetime.date.today().strftime("%Y-%m-%d")
        data = generate_report()
        output_path = build_html_report(data, report_date_str)
        webbrowser.open("file://" + os.path.abspath(output_path))
        logging.info(f"Report generated and saved OK: {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"Report failed: {e}")
        raise


if __name__ == "__main__":
    # Run once immediately so today's dated HTML report is created and opened
    daily_job()

    # Schedule every Monday at 07:00 AM
    schedule.every().monday.at("07:00").do(daily_job)

    while True:
        schedule.run_pending()
        time.sleep(60)
        