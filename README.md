# 🧫 Bioprocess Data Analyzer

A robust, interactive web application built with Python and Streamlit, designed to process, visualize, and analyze bioprocess and fermentation data. 

This tool is specifically tailored for **recombinant protein production workflows** or metabolic engineering processes that utilize a standard three-phase operational strategy: an initial **Batch** phase, an **Uninduced Fed-batch** phase for biomass accumulation, and a final **Induced Fed-batch** phase for product expression.

## ⚠️ Important: Data Input Guidelines

For the application to parse your data correctly, the input files (`.xlsx`, `.csv`, or Google Sheets) must strictly follow these formatting rules:

### 1. Clean Data Tables Only
The application requires "clean" tabular data. 
* **No merged cells:** Ensure that headers and data points do not contain merged cells, as this breaks the Pandas dataframe structure.
* **Single row headers:** The row immediately preceding your data should contain the column names. 

### 2. Delimiting the Working Area
Raw data exported from bioreactor software (like BioCommand, Iris, or Eve) often includes dozens of metadata rows at the top before the actual data table begins. 
To handle this, use the **Data Configuration Assistant** in the app to explicitly bound your table:
* **Rows to skip:** Count from the top of your file down to the row *just before* your column headers.
* **Column Range:** Explicitly set the starting and ending columns (e.g., from `A` to `T`) to prevent the app from reading blank columns or aggregated data to the right of your main table.

<img width="1800" height="694" alt="Excel screenshot" src="https://github.com/user-attachments/assets/fff12c83-2189-4c39-a09f-d2b18c01b5e4" />
Example of a raw bioreactor export. To parse this file correctly in the app, the user must set "Header rows to be skipped" to 21 and the "Column range" from C to R.

### 3. Google Sheets Privacy Settings
If you choose to import data via a URL, the Google Sheet must be set to **"Anyone with the link can view"**. The application bypasses complex API authentication by directly exporting the sheet to a temporary Excel file, which is only possible if the document is completely public.


### 4. Time Column Requirements
All charts and kinetic calculations ($\mu$, $q_p$) are strictly plotted and computed as a function of fermentation time. 
* The column you select as the "Time column" during the initial setup must contain the **net elapsed time** (e.g., 0, 0.5, 1, 24 hours) since the start of the bioreactor run. 
* **Do not** use absolute clock time (e.g., "14:30:00") or date formats, as the mathematical engine and the X-axis scaling require continuous numerical values to perform regressions and chart plotting accurately.
---

## ✨ Key Features & Technical Details

### 1. Dynamic Import Engine
* **Local & Cloud Support:** Upload local files or paste public Google Sheets links directly.
* **Intelligent Parsing:** The backend uses a custom URL manipulation technique (`/export?format=xlsx`) to bypass the standard Google Sheets API constraints, ensuring a robust and error-free data ingestion process using native `pandas.read_excel`.
* **Out-of-bounds Protection:** The app dynamically slices the dataframe (`iloc`). If you specify an ending column (e.g., 'Z') that exceeds the actual data width, the application safely truncates the selection without crashing.

### 2. Advanced Graphical Visualization
* **Phase Shadowing:** The charts automatically shade the background to distinguish between distinct bioprocess phases:
  * **Batch (Grey):** Initial growth phase.
  * **Uninduced Fed-batch (Green):** Biomass accumulation phase.
  * **Induced Fed-batch (Purple):** Production phase triggered by an inducer (e.g., IPTG).
* **Smart Axis Markers:** Critical transition points (like the exact hour induction starts) are marked with **red numbers** on the X-axis to immediately highlight the biological shifts.
* **Normalized Multi-axis Charts:** Plots a primary variable (e.g., OD600) on the main Y-axis while simultaneously plotting multiple secondary variables (e.g., pH, feeding rate, temperature) on a secondary Y-axis, mathematically normalizing them to a 0-100% scale for visual correlation.

### 3. Real-Time Specific Rate Calculator
* Features an integrated tool to calculate the specific rate ($\mu$, $q_p$, $q_s$) based on the primary variable selected.
* **Interactive Boundaries:** Slide a dual-knob selector to isolate the exponential phase. Toggleable orange dashed lines appear on the chart to visually confirm the selected time window.
* **Mathematical Engine:** Performs a linear regression on the natural logarithm of the data ($\ln(y)$ vs $t$) using `numpy.polyfit`, instantly displaying the calculated rate in h⁻¹.

### 4. Print-Ready Reporting 
* This allows users to save the entire dashboard—including the interactive charts, the applied parameters, and the calculated kinetic metrics—as a high-quality, vector-based PDF report.

## 🚀 How to Run Locally

1. Clone this repository:
  ```bash
   git clone [https://github.com/your-username/fermentation-app.git](https://github.com/your-username/fermentation-app.git)
   ```

2. Install the required dependencies:
  ```bash
  pip install streamlit pandas numpy matplotlib
  ```

3. Run the application:
  ```bash
  streamlit run app.py
  ```

---

## 📬 Contact & Feedback

This project was developed by **Bautista Buralli**, a Biotechnology professional from the **National University of Rosario (UNR)**, Argentina. 

If you have any questions, find a bug, or would like to discuss potential collaborations in **Synthetic Biology** or **Bioprocess Engineering**, feel free to reach out!

* [LinkedIn](https://www.linkedin.com/in/bautistaburalli)
* [GitHub](https://github.com/burallib)

---
