import streamlit as st
import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, FactorRange, HoverTool
from bokeh.palettes import Category10, Spectral6
import numpy as np

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="Dashboard Kepuasan Penumpang")

# --- Data Loading and Preprocessing ---
@st.cache_data
def load_data():
    df = pd.read_csv('train.csv')
    df = df.dropna(subset=['Arrival Delay in Minutes'])
    df = df.drop_duplicates()
    df = df.drop(columns=['Unnamed: 0', 'id'])
    df.rename(columns={'satisfaction': 'Satisfaction'}, inplace=True)
    df['Satisfaction'] = df['Satisfaction'].replace({'neutral or dissatisfied': 'dissatisfied'})
    df['Satisfaction_encoded'] = df['Satisfaction'].apply(lambda x: 1 if x == 'satisfied' else 0)
    return df

df = load_data()

# --- Streamlit App Header ---
st.title("Dashboard Interaktif Kepuasan Penumpang Maskapai")

st.markdown("""
Aplikasi ini memungkinkan anda untuk melihat faktor-faktor yang mempengaruhi kepuasan penumpang maskapai penerbangan secara interaktif.
Gunakan slider dan dropdown menu di sidebar untuk memfilter dan memvisualisasikan data.
""")

st.sidebar.header("Pengaturan Filter Data")

# Filter 1: Rentang Usia
min_age, max_age = int(df['Age'].min()), int(df['Age'].max())
age_range = st.sidebar.slider(
    "Pilih Rentang Usia",
    min_value=min_age,
    max_value=max_age,
    value=(min_age, max_age)
)

# Filter 2: Kelas Penerbangan
flight_classes_options = ['All'] + sorted(df['Class'].unique().tolist())
selected_class = st.sidebar.selectbox("Pilih Kelas Penerbangan", flight_classes_options)

# Filter 3: Tipe Perjalanan
travel_type_options = ['All'] + sorted(df['Type of Travel'].unique().tolist())
selected_travel_type = st.sidebar.selectbox("Pilih Tipe Perjalanan", travel_type_options)

filtered_df = df[(df['Age'] >= age_range[0]) & (df['Age'] <= age_range[1])].copy()

if selected_class != 'All':
    filtered_df = filtered_df[filtered_df['Class'] == selected_class].copy()

if selected_travel_type != 'All':
    filtered_df = filtered_df[filtered_df['Type of Travel'] == selected_travel_type].copy()

if filtered_df.empty:
    st.warning("Tidak ada data yang tersedia untuk kombinasi filter yang dipilih. Silakan sesuaikan filter Anda.")
    st.stop()

# --- Interactive Plot 1: Age Distribution by Satisfaction (Histogram with Slider) ---
st.header("Distribusi Usia Penumpang Berdasarkan Kepuasan")
st.write("Distribusi usia penumpang berdasarkan tingkat kepuasan, disesuaikan dengan filter yang dipilih.")

satisfied_ages = filtered_df[filtered_df['Satisfaction_encoded'] == 1]['Age']
dissatisfied_ages = filtered_df[filtered_df['Satisfaction_encoded'] == 0]['Age']

common_min_age = filtered_df['Age'].min()
common_max_age = filtered_df['Age'].max()
if common_min_age == common_max_age:
    common_bins = np.array([common_min_age, common_min_age + 1]) 
else:
    common_bins = np.linspace(common_min_age, common_max_age, 21) 

hist_satisfied, edges = np.histogram(satisfied_ages, bins=common_bins)
hist_dissatisfied, edges = np.histogram(dissatisfied_ages, bins=common_bins)

source_age = ColumnDataSource(data={
    'left': edges[:-1],
    'right': edges[1:],
    'satisfied_count': hist_satisfied,
    'dissatisfied_count': hist_dissatisfied
})

p_age = figure(height=400, width=700, title="Distribusi Usia Penumpang",
               x_axis_label="Usia", y_axis_label="Frekuensi",
               tools="pan,wheel_zoom,box_zoom,reset,save")

p_age.quad(top='satisfied_count', bottom=0, left='left', right='right',
           source=source_age, legend_label="Puas", color=Category10[10][0], alpha=0.7)

p_age.quad(top='dissatisfied_count', bottom=0, left='left', right='right',
           source=source_age, legend_label="Tidak Puas", color='red', alpha=0.7)


p_age.x_range.range_padding = 0.05
p_age.y_range.start = 0
p_age.legend.location = "top_right"
p_age.legend.click_policy="hide"

st.bokeh_chart(p_age, use_container_width=True)

st.markdown("---")

# --- Interactive Plot 2: Satisfaction by Filtered Class (Bar Chart) ---
st.header("Kepuasan Penumpang Berdasarkan Filter Pilihan")
st.write("Lihat persentase kepuasan dan ketidakpuasan untuk kombinasi filter yang dipilih.")

satisfaction_counts_class_filtered = filtered_df['Satisfaction'].value_counts().reindex(['dissatisfied', 'satisfied'], fill_value=0)
total_passengers_filtered = satisfaction_counts_class_filtered.sum()

if total_passengers_filtered > 0:
    satisfaction_percentages_class_filtered = (satisfaction_counts_class_filtered / total_passengers_filtered) * 100
else:
    satisfaction_percentages_class_filtered = pd.Series({'dissatisfied': 0, 'satisfied': 0})

data_class_filtered = {
    'satisfaction_level': satisfaction_percentages_class_filtered.index.tolist(),
    'percentages': satisfaction_percentages_class_filtered.values.tolist(),
    'counts': satisfaction_counts_class_filtered.values.tolist(),
    'colors': ['red' if s == 'dissatisfied' else Category10[10][0] for s in satisfaction_percentages_class_filtered.index.tolist()]
}
source_class_filtered = ColumnDataSource(data=data_class_filtered)

p_class_filtered = figure(x_range=FactorRange(factors=satisfaction_percentages_class_filtered.index.tolist()),
                          height=400, width=700,
                          title=f"Kepuasan: Kelas '{selected_class}', Tipe Perjalanan '{selected_travel_type}'",
                          x_axis_label="Tingkat Kepuasan", y_axis_label="Persentase (%)",
                          tools="pan,wheel_zoom,box_zoom,reset,save")

p_class_filtered.vbar(x='satisfaction_level', top='percentages', width=0.5,
                      source=source_class_filtered, legend_field='satisfaction_level',
                      line_color='white', fill_color='colors')

p_class_filtered.x_range.range_padding = 0.1
p_class_filtered.y_range.start = 0
p_class_filtered.legend.location = "top_left"
p_class_filtered.legend.click_policy="hide"

hover_class_filtered = HoverTool()
hover_class_filtered.tooltips = [
    ("Tingkat Kepuasan", "@satisfaction_level"),
    ("Jumlah", "@counts"),
    ("Persentase", "@percentages{0.1f}%")
]
p_class_filtered.add_tools(hover_class_filtered)

st.bokeh_chart(p_class_filtered, use_container_width=True)

st.markdown("---")

# --- Interactive Plot 3: Correlation of Service Features with Satisfaction (Bar Plot with Dynamic Filtering) ---
st.header("Korelasi Fitur Layanan dengan Kepuasan")
st.write("Lihat bagaimana korelasi fitur layanan dengan kepuasan berubah berdasarkan filter yang diterapkan.")

service_cols = ['Inflight wifi service', 'Ease of Online booking',
                'Food and drink', 'Online boarding', 'Seat comfort',
                'Inflight entertainment', 'On-board service', 'Leg room service',
                'Baggage handling', 'Checkin service', 'Inflight service', 'Cleanliness']

if 'Satisfaction_encoded' in filtered_df.columns and len(filtered_df) > 1 and filtered_df['Satisfaction_encoded'].nunique() > 1:
    correlations = filtered_df[service_cols + ['Satisfaction_encoded']].corr()['Satisfaction_encoded'].drop('Satisfaction_encoded', errors='ignore')
    correlations = correlations.dropna() 
    correlations_sorted = correlations.sort_values(ascending=False)
else:
    correlations_sorted = pd.Series([], dtype=float) 

selected_service_feature_highlight = st.sidebar.selectbox(
    "Sorot Fitur Layanan (Korelasi)",
    ['None'] + [col.replace('_', ' ').title() for col in service_cols], 
    index=0,
    help="Pilih fitur layanan untuk menyoroti bar korelasinya di plot."
)

original_selected_feature = selected_service_feature_highlight.replace(' ', '').lower() if selected_service_feature_highlight != 'None' else 'None'
if original_selected_feature not in service_cols and original_selected_feature != 'None':
    for col in service_cols:
        if col.replace('_', ' ').lower() == selected_service_feature_highlight.lower():
            original_selected_feature = col
            break


if not correlations_sorted.empty:
    features_display = [f.replace('_', ' ').title() for f in correlations_sorted.index.tolist()]

    source_corr = ColumnDataSource(data={
        'features_original': correlations_sorted.index.tolist(), 
        'features_display': features_display,
        'values': correlations_sorted.values.tolist(),
        'colors': [
            'red' if f == original_selected_feature else Spectral6[0]
            for f in correlations_sorted.index.tolist()
        ]
    })

    p_corr = figure(y_range=FactorRange(factors=features_display),
                    height=400, width=700,
                    title="Korelasi Fitur Layanan dengan Kepuasan (Disesuaikan Filter)",
                    x_axis_label="Nilai Korelasi", y_axis_label="Fitur Layanan",
                    tools="pan,wheel_zoom,box_zoom,reset,save")

    p_corr.hbar(y='features_display', right='values', height=0.7, source=source_corr,
                line_color='white', fill_color='colors')

    hover_corr = HoverTool()
    hover_corr.tooltips = [
        ("Fitur", "@features_display"),
        ("Korelasi", "@values{0.00}")
    ]
    p_corr.add_tools(hover_corr)

    p_corr.x_range.start = -0.5 
    p_corr.x_range.end = 0.5 

    st.bokeh_chart(p_corr, use_container_width=True)
else:
    st.info("Tidak cukup data untuk menghitung korelasi dengan filter yang dipilih, atau semua nilai pada fitur layanan konstan. Silakan sesuaikan filter Anda.")

st.markdown("---")

st.write("""
<p style='text-align: center;'>KELOMPOK 17</p>
<p style='text-align: center;'>VISUALISASI DATA</p>
""", unsafe_allow_html=True)