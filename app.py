import streamlit as st
import pandas as pd
import requests

# -------------------------
# 🔐 GitHub Token (Streamlit secrets)
headers = {}

try:
    TOKEN = st.secrets["GITHUB_TOKEN"]
    headers = {"Authorization": f"token {TOKEN}"}
except:
    headers = {}  # fallback

# -------------------------
# 📥 GitHub API
def get_commits(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    
    try:
        res = requests.get(url, headers=headers)

        if res.status_code != 200:
            st.error(f"GitHub Error: {res.json()}")
            return []

        data = res.json()

        if not isinstance(data, list):
            return []

        return data

    except Exception as e:
        st.error(f"Error: {e}")
        return []

# -------------------------
# 🧠 Processing
def process_commits(commits):
    data = []

    if not isinstance(commits, list):
        return pd.DataFrame()

    for c in commits[:15]:  # increased limit
        try:
            commit = c.get("commit", {})
            
            author = commit.get("author", {}).get("name", "Unknown")
            message = commit.get("message", "")
            date = commit.get("author", {}).get("date", "")

            data.append({
                "author": author,
                "message": message,
                "date": date,
                "impact": len(message)  # simple impact
            })
        except:
            continue

    return pd.DataFrame(data)

# -------------------------
# 🧠 ML Logic
def classify_commit(msg):
    msg = msg.lower()

    if "fix" in msg:
        return "Bug Fix"
    elif "add" in msg or "feature" in msg:
        return "Feature"
    elif "refactor" in msg:
        return "Refactor"
    else:
        return "Other"

# -------------------------
# 📊 Metrics
def bus_factor(df):
    counts = df["author"].value_counts(normalize=True)
    return (counts > 0.5).sum()

def imbalance(df):
    counts = df["author"].value_counts()
    return 0 if len(counts) <= 1 else counts.std()

def health_score(df):
    return max(0, min(100, 100 - imbalance(df)*10 + df["type"].nunique()*5))

# -------------------------
# 🤖 AI Summary (lightweight)
def generate_summary(text):
    text = text.lower()

    features = text.count("add")
    bugs = text.count("fix")
    refactor = text.count("refactor")

    return f"""
    📌 AI Summary

    - Features Added: {features}
    - Bugs Fixed: {bugs}
    - Refactoring Work: {refactor}

    Overall, the repository shows active development with continuous updates.
    """

# -------------------------
# 🎨 UI
st.title("🚀 GitHub Pulse Dashboard")

repo_url = st.text_input("Enter GitHub Repo URL")

if repo_url:
    repo_url = repo_url.strip().rstrip("/")

    parts = repo_url.split("/")

    if len(parts) < 2:
        st.error("Invalid GitHub URL ❌")
    else:
        owner = parts[-2]
        repo = parts[-1]

        st.write(f"🔍 Analyzing: {owner}/{repo}")

        commits = get_commits(owner, repo)

        if not commits:
            st.error("No data found ❌ (Check repo or API limit)")
        else:
            df = process_commits(commits)

            if len(df) == 0:
                st.error("No processed data ❌")
            else:
                df["type"] = df["message"].apply(classify_commit)
                df["date"] = pd.to_datetime(df["date"], errors="coerce")

                # 📊 Data
                st.subheader("📊 Commit Data")
                st.dataframe(df)

                # 📈 Charts
                st.subheader("📈 Contribution Breakdown")
                st.bar_chart(df["author"].value_counts())

                st.subheader("📊 Commit Types")
                st.bar_chart(df["type"].value_counts())

                # 📅 Timeline
                st.subheader("📅 Timeline")
                timeline = df.groupby(df["date"].dt.date).size()
                st.line_chart(timeline)

                # 🔥 Insights
                st.subheader("🔥 Insights")

                st.write("Top Contributor:", df["author"].value_counts().idxmax())
                st.write("Bus Factor:", bus_factor(df))
                st.write("Health Score:", round(health_score(df), 2))

                # 🤖 AI Summary
                st.subheader("🧠 AI Summary")

                if st.button("Generate Summary"):
                    text = " ".join(df["message"].tolist())
                    summary = generate_summary(text)
                    st.write(summary)