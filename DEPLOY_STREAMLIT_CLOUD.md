# Deploy Ecuador V1 Dashboard (Streamlit Community Cloud)

This app is now self-contained for deployment from this folder.

## Included lightweight data
- `data/input/hs92_4digits.csv`
- `data/input/rankings.csv`
- `data/intermediate/complexity_ecu_2024.csv`
- `data/intermediate/opportunity_metrics_hs4_ecu.csv`

## Steps
1. Create a new GitHub repo (for example `ecuador-opportunities-v1`).
2. Upload the contents of this folder:
   - `app.py`
   - `pages/`
   - `data_utils.py`
   - `requirements.txt`
   - `data/` (only the files listed above)
3. Go to [Streamlit Community Cloud](https://share.streamlit.io/).
4. Click **New app** and connect your GitHub repo.
5. Set:
   - **Main file path**: `app.py`
   - **Branch**: your default branch (usually `main`)
6. Deploy.

## Notes
- This deployment avoids large raw input files, so it is suitable for GitHub + Streamlit Cloud.
- If you update calculations locally, regenerate and replace:
  - `data/intermediate/complexity_ecu_2024.csv`
  - `data/intermediate/opportunity_metrics_hs4_ecu.csv`
