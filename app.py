import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

st.set_page_config(layout="centered")

def letter_to_number(letters):
    """Converts an Excel column letter (e.g: 'A', 'AA') into a number index (0-based)"""
    letters = letters.upper().strip()
    number = 0
    for letter in letters:
        number = number * 26 + (ord(letter) - ord('A') + 1)
    return number - 1 # Subtracts 1 in order to make it 0-index

def shadowing(ax, on, batch_time, induct_time, ferm_time):
    """Allows the user to shadow the different parts of the fermentation procedure in the selected charts"""
    if on:
        # Batch
        s1 = ax.axvspan(0, batch_time, color='gray', alpha=0.2, label="Batch")
        # Pre-induction fed-batch
        s2 = ax.axvspan(batch_time, induct_time, color='green', alpha=0.2, label="Uninduced Fed-batch")
        # Post-induction fed-batch  
        s3 = ax.axvspan(induct_time, ferm_time, color='purple', alpha=0.2, label="Induced Fed-batch")
    
        shades_legend = ax.legend(handles=[s1, s2, s3], labels=['Batch', 'Uninduced Fed-batch', 'Induced Fed-batch'], loc='center', bbox_to_anchor=(0.5, 1.15), ncol=3, fontsize=8)
        
        # Red ticks definition
        base_ticks = list(range(0, int(ferm_time) + 1, 4))
        red_ticks = [batch_time, induct_time]
        threshold = 2

        clean_ticks = []
        for i in base_ticks:
            close_to_limits = False
            for tick in red_ticks:
                if abs(i - tick) < threshold:
                    close_to_limits = True
            if not close_to_limits:
                clean_ticks.append(i)

        total_ticks = clean_ticks + red_ticks
        ax.set_xticks(total_ticks)

        plt.draw()
        for i in ax.get_xticklabels():
            try:
                val = float(i.get_text())
                if val in red_ticks:
                    i.set_color("red")
                else:
                    i.set_color("black")
            except:
                continue

                   
def main_body_function(df, ferm_name):
    """Core logic for data processing and visualization of fermentation runs.
    
    This function handles:
    1. Data preview and time column selection.
    2. Input for fermentation phase transitions (Batch, Fed-batch, Induction).
    3. Generation of combined charts with normalized secondary axes.
    4. Generation of individual parameter charts.
    5. Real-time kinetic calculations (specific growth/production rates) via 
       logarithmic regression.
    6. PDF report generation triggers.

    Args:
        df (pd.DataFrame): The cleaned fermentation dataset.
        ferm_name (str): Unique identifier for the run (used for widget keys)."""
    
    # Shows the first 5 rows of the dataset
    st.subheader("Data preview", )
    rows_num = st.number_input("Select number of rows to be displayed", min_value=0, value=5, step=1)
    st.dataframe(df.head(rows_num))
    
    # Definition of the time column
    time_col = st.selectbox("**Select time column**", df.columns, key=f"time_{ferm_name}")
    df[time_col] = pd.to_numeric(df[time_col], errors="coerce")
    st.write("---")

    # Graph shadowing request
    st.subheader("Graph shadowing")
    st.write("Adjust the shadowing background of graphs indicating the different parts of the fermentation process")
    c1, c2, c3 = st.columns(3)
    with c1:
        batch_time = st.number_input("Time until batch ends (h):", min_value=0.0, value=12.0, step=0.5, key=f"batch_time_{ferm_name}")
    with c2:
        induct_time = st.number_input("Time until induction starts (h):", min_value=batch_time + 1, value=24.0, step=0.5, key=f"induct_time_{ferm_name}")
    with c3:
        ferm_time = st.number_input("Time until fermentation ends (h):", min_value=induct_time + 1, value=48.0, step=0.5, key=f"ferm_time_{ferm_name}")
    
    if induct_time <= batch_time or ferm_time <= batch_time or ferm_time <= induct_time:
        st.error("Please review the entered time values to ensure chronological order.")
        
    on = st.toggle("Highlight fermentation phases", key=f"on_{ferm_name}")
    st.write("---")

    # Chart selection
    st.subheader("Select charts to display")
    space1, comb_col, unique_col, space2 = st.columns([1, 1.5, 1.5, 0.5])
    with comb_col:
        combined_graphic = st.checkbox("3-axis graphic with normalized parameters", key=f"checkb1_{ferm_name}")
    with unique_col:
        unique_graphics = st.checkbox("Individual charts", key=f"checkb2_{ferm_name}")

    # Definition of combined (3-axis) graphic
    if combined_graphic:
        # Primary Y-axis selection
        main_y_col = st.selectbox("Select primary Y-axis parameter (typically OD)", df.columns, key=f"main_y_{ferm_name}")

        # Drop NaNs or strings from the selected columns
        df[main_y_col] = pd.to_numeric(df[main_y_col], errors="coerce")
        df = df.dropna(axis=0, how='any', subset=[time_col, main_y_col])
        
        if df.empty:
            st.warning("Please select valid numeric columns for Time and the primary parameter.")
            return

        # Base plot (e.g., OD vs Time)
        fig, ax = plt.subplots(figsize=(8,4))
        ax.plot(df[time_col], df[main_y_col], color='black', label=main_y_col)
        ax.set_xlabel('Time (h)')
        ax.set_ylabel(main_y_col)

        shadowing(ax, on, batch_time, induct_time, ferm_time)
           
        # Widget to select secondary variables for normalization
        other_cols = [column for column in df.columns if column not in [time_col, main_y_col]]
        selected_cols = st.multiselect('Select secondary parameters to plot (normalized on a 0-100% scale)', other_cols, key=f"othercols_{ferm_name}")
        
        ax = plt.gca()
        
        # Shadowing label
        handles_1, labels_1 = ax.get_legend_handles_labels()
        handles_shades = []
        labels_shades = []
        handles_ax = []
        labels_ax = []

        for handle, label in zip(handles_1, labels_1):
            if "Batch" in label or "Fed-batch" in label:
                handles_shades.append(handle)
                labels_shades.append(label)
            else:
                handles_ax.append(handle)
                labels_ax.append(label)

        if selected_cols:
            # Normalize secondary variables to 0-100%
            variables_to_normalize = selected_cols

            for variable in variables_to_normalize:
                normalized_variable = (df[variable] - df[variable].min()) / (df[variable].max() - df[variable].min()) * 100
                df[f"{variable} (norm)"] = normalized_variable

            ax2 = plt.twinx()
            for variable in variables_to_normalize:
                ax2.plot(df[time_col], df[f"{variable} (norm)"], label=variable)
                
            ax2.set_ylabel("Normalized values (0-100%)")
            ax2.set_ylim(-5, 105)

            # Combined legend at the bottom
            handles_2, labels_2 = ax2.get_legend_handles_labels()
            ax2.legend(handles_ax + handles_2, labels_ax + labels_2, loc='center', bbox_to_anchor=(0.5, -0.3), ncol=3, fontsize=8)
        
        else:
            if on:
                shades_legend = ax.legend(handles_shades, labels_shades, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=3, fontsize=8)
            
        xlimslider = st.slider("X-axis limits", 0.0, ferm_time, value=(0.0, ferm_time), key=f"xlimslider_{ferm_name}")
        plt.xlim(xlimslider[0], xlimslider[1])

        plt.tight_layout()
        place_for_graphic = st.empty()

        # Specific rate calculator
        rate_calc_exp = st.expander(f"Calculate specific rate for {main_y_col}")
        rate_calc_exp.write("This section is intended for the calculation of the specific growth rate, but it can also be useful for calculating the specific production rate or a metabolite of interest or the specific consumption rate of a substrate")
        with rate_calc_exp:
            mu_time_values = st.slider("Select time interval for exponential phase", 0.0, ferm_time, value=(0.0, ferm_time), key=f"xlimslider3_{ferm_name}")
            
            show_lines = st.toggle(f"Enable graphic representation", key=f"act_lines_{ferm_name}")
            if show_lines:
                ax.axvline(x=mu_time_values[0], color='orange', linestyle='--', linewidth=2)
                ax.axvline(x=mu_time_values[1], color='orange', linestyle='--', linewidth=2)
                
            df_mu = df[(df[time_col] >= mu_time_values[0]) & (df[time_col] <= mu_time_values[1])].copy()
            df_mu = df_mu[df_mu[main_y_col] > 0]
                
            if len(df_mu) > 1:
                x_axis_mu = df_mu[time_col]
                y_axis_mu = np.log(df_mu[main_y_col])
                ec_coef = np.polyfit(x_axis_mu, y_axis_mu, 1)
                mu = ec_coef[0]

                st.metric(label=f'Specific rate ({main_y_col})', value=f'{mu:.4f} h⁻¹')
            else:
                st.warning('The selected interval must contain at least two points greater than 0.')
    
        place_for_graphic.pyplot(fig)

    # Definition of unique graphics:
    if unique_graphics:
        unique_graphics_cols = [column for column in df.columns if column != time_col]
        unique_graphic_selected_cols = st.multiselect("Select individual variables to plot", unique_graphics_cols, key=f"uniqueg_cols_{ferm_name}")
        xlimslider = st.slider("X-axis limits", 0.0, ferm_time, value=(0.0, ferm_time), key=f"xlimslider2_{ferm_name}")
        
        for column in unique_graphic_selected_cols:
            df[column] = pd.to_numeric(df[column], errors="coerce")
            fig, ax_ind = plt.subplots(figsize=(8,4))
            ax_ind.plot(df[time_col], df[column], label=column)
            shadowing(ax_ind, on, batch_time, induct_time, ferm_time)

            ax_ind.set_title(f"{column} Evolution")
            ax_ind.set_xlabel("Time (h)")
            ax_ind.set_ylabel(column)
            ax_ind.set_xlim(xlimslider[0], xlimslider[1])

            st.pyplot(fig)
    
    # Web to pdf button
    st.write("---")
    st.markdown("""
        <div style="text-align: center; margin-top: 20px;">
            <p style="font-size: 12px; color: gray; margin-top: 8px;">
                Tip: If you want to save the results, just hit Ctrl + P, select 'Save as PDF' and check 'Background graphics' for better results :)
            </p>
        </div>
    """, unsafe_allow_html=True)

# App initialization
if "loaded_data" not in st.session_state:
    st.session_state.loaded_data = False

col_title, col_btn = st.columns([4, 1])
with col_title:
    st.title("Graphical visualization of fermentation parameters")
with col_btn:
    st.write("")    
    st.link_button("💬 Feedback & Suggestions", "https://www.linkedin.com/in/bautistaburalli")

# Data import
if not st.session_state.loaded_data:
    st.subheader("Data import")

    app_title = st.text_input("Please enter the fermentation title (optional):", placeholder="Tip: Don't forget to include specific details like the date, employed strain, produced protein, etc.")
    method = st.radio("How would you like to import the data?", ["Upload a local Excel file", "Paste a **public** Google Sheets link"])

    raw_data = None
    if method == "Upload a local Excel file":
        file = st.file_uploader("Drag your file here", type=["xlsx", "csv"])
        if file and st.button("Import data"):
            raw_data = file
            st.session_state.title = app_title if app_title else "Fermentation analysis"
            st.session_state.raw_data = raw_data
            st.session_state.method = method

            if file.name.endswith(".xlsx"):
                xls = pd.ExcelFile(file)
                st.session_state.sheet_names = xls.sheet_names
            else:
                st.session_state.sheet_names = ["CSV"]
            
            st.session_state.loaded_data = True
            st.rerun()
        
    else:
        link = st.text_input("Paste the Google Sheets link (It must have **public** access)")
        if link:
            try:
                sheet_id = link.split("/d/")[1].split("/")[0]
                export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
           
                xls = pd.ExcelFile(export_url)
                st.session_state.sheet_names = xls.sheet_names

                raw_data = link
                st.session_state.title = app_title if app_title else "Fermentation analysis"
                st.session_state.raw_data = raw_data
                st.session_state.method = method
                st.session_state.loaded_data = True
                st.rerun()
            
            except Exception as e:
                st.error("⚠️ We couldn't read the file. Please make sure the Google Sheets link has 'public' access.")
                st.info("🐞 If the problem persists, please contact me on LinkedIn or GitHub and let me know what steps you took so I can look into it!")

# Configuration and visualization
if st.session_state.loaded_data:
    st.header(f"{st.session_state.title}")

    if st.button("Start again / Change data"):
      st.session_state.loaded_data = False
      if "df_general" in st.session_state:
          del st.session_state.df_general
      st.rerun()

    st.write("---")
    st.subheader("Data configuration assistant")

    with st.form("config_assistant_form"):
        col1, col2 = st.columns(2)
        with col1:
            excel_sheet = None
            if st.session_state.method == "Upload a local Excel file" and st.session_state.raw_data.name.endswith(".csv"):
                st.info("CSV file detected. No requirement of working sheet selection.")
            else:
                excel_sheet = st.selectbox("Select working sheet", st.session_state.sheet_names)
        
        with col2:
            skiping_rows = st.number_input("Header rows to be skipped:", min_value=0, step=1, help="Count from the first one to the last row that does not contain the data header", placeholder="e.g. 20")
            st.write("Column range")
            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                starting_col_str = st.text_input("Starting column", placeholder="e.g. B")
            with sub_col2:
                ending_col_str = st.text_input("Ending column", placeholder='e.g. T', help="Limit to avoid reading combined cells to the right")

        submit_config = st.form_submit_button("Apply configuration")
    
    st.write("---")

    if submit_config:
        try:
            starting_idx = letter_to_number(starting_col_str)
            ending_idx = letter_to_number(ending_col_str) + 1

            if st.session_state.method == "Upload a local Excel file":
                st.session_state.raw_data.seek(0)
                if st.session_state.raw_data.name.endswith(".csv"):
                    df = pd.read_csv(st.session_state.raw_data, skiprows=int(skiping_rows))
                else:
                    df = pd.read_excel(st.session_state.raw_data, sheet_name=excel_sheet, skiprows=int(skiping_rows))
            else:
                sheet_id = st.session_state.raw_data.split("/d/")[1].split("/")[0]
                export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
                
                df = pd.read_excel(export_url, sheet_name=excel_sheet, skiprows=int(skiping_rows))
            

            df = df.iloc[:, starting_idx:ending_idx]            
            st.session_state.df_general = df

        except Exception as e:
            st.error("⚠️ An error occurred while processing your data. Please check your configuration (working sheet name, skipped rows, columns).")
            st.info("🐞 Did you find a bug? Please contact me on LinkedIn or GitHub with a brief description of the steps you took so I can fix it!")

if "df_general" in st.session_state:
    main_body_function(st.session_state.df_general, "General")