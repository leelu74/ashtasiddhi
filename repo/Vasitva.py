#!/usr/bin/env python3
"""
Vasitva.py - UI Agent
Handles user interface with Streamlit for exoplanet analysis dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import other agents
from Anima import AnimaAgent
from Isitva import IsitvaAgent
from Garima import GarimaAgent

class VasitvaAgent:
    """Agent for Streamlit UI and data visualization"""
    
    def __init__(self, data_dir: str = "/data"):
        self.logger = logging.getLogger("Vasitva")
        self.data_dir = Path(data_dir)
        
        # Initialize other agents
        self.anima = AnimaAgent(data_dir)
        self.isitva = IsitvaAgent(data_dir)
        self.garima = GarimaAgent()
        
        # Configure Streamlit
        st.set_page_config(
            page_title="Exoplanet Analysis Dashboard",
            page_icon="🪐",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def start_ui(self, host: str = "0.0.0.0", port: int = 8501):
        """Start the Streamlit UI"""
        self.run_dashboard()
    
    def run_dashboard(self):
        """Main dashboard interface"""
        # Sidebar navigation
        st.sidebar.title("🪐 Exoplanet Analysis")
        page = st.sidebar.radio(
            "Navigate to:",
            ["Dashboard", "PDF Analysis", "Paper Search", "Data Explorer", "Simulations"]
        )
        
        if page == "Dashboard":
            self.show_main_dashboard()
        elif page == "PDF Analysis":
            self.show_pdf_analysis()
        elif page == "Paper Search":
            self.show_paper_search()
        elif page == "Data Explorer":
            self.show_data_explorer()
        elif page == "Simulations":
            self.show_simulations()
    
    def show_main_dashboard(self):
        """Main dashboard with overview statistics"""
        st.title("🪐 Exoplanet Analysis Dashboard")
        st.markdown("---")
        
        # Get summary data
        summary = self.isitva.get_analysis_summary()
        stats = self.isitva.get_statistics()
        
        if 'error' in summary:
            st.error(f"Error loading data: {summary['error']}")
            return
        
        # Top-level metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Analyses", summary.get('total_analyses', 0))
        
        with col2:
            habitable_count = summary.get('habitable_zone_statistics', {}).get('habitable_count', 0)
            st.metric("Habitable Zone Planets", int(habitable_count) if habitable_count else 0)
        
        with col3:
            h2o_count = summary.get('composition_statistics', {}).get('h2o_count', 0)
            st.metric("Water Detected", int(h2o_count) if h2o_count else 0)
        
        with col4:
            sulfur_count = summary.get('composition_statistics', {}).get('sulfur_count', 0)
            st.metric("Sulfur Detected", int(sulfur_count) if sulfur_count else 0)
        
        # Charts section
        st.markdown("## 📊 Analysis Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self._plot_atmospheric_composition(stats)
        
        with col2:
            self._plot_planet_types(stats)
        
        # Recent analyses
        st.markdown("## 📄 Recent Analyses")
        recent = summary.get('recent_analyses', [])
        if recent:
            df_recent = pd.DataFrame(recent)
            st.dataframe(df_recent, use_container_width=True)
        else:
            st.info("No analyses found. Upload and analyze PDFs to see results here.")
    
    def show_pdf_analysis(self):
        """PDF upload and analysis interface"""
        st.title("📄 PDF Analysis")
        st.markdown("Upload exoplanet research papers for analysis")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload research papers about exoplanets for analysis"
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                st.markdown(f"### Analysis: {uploaded_file.name}")
                
                # Save uploaded file
                temp_path = self.data_dir / "temp" / uploaded_file.name
                temp_path.parent.mkdir(exist_ok=True)
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Analysis button
                if st.button(f"Analyze {uploaded_file.name}", key=uploaded_file.name):
                    with st.spinner("Analyzing PDF..."):
                        try:
                            # Run analysis
                            results = self.anima.analyze_pdf(str(temp_path))
                            
                            # Display results
                            self._display_analysis_results(results)
                            
                            st.success("Analysis completed!")
                            
                        except Exception as e:
                            st.error(f"Analysis failed: {str(e)}")
                
                st.markdown("---")
    
    def show_paper_search(self):
        """Paper search interface"""
        st.title("🔍 Paper Search")
        st.markdown("Search for exoplanet research papers")
        
        # Search interface
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_terms = st.text_input(
                "Search terms",
                placeholder="e.g., exoplanet atmosphere sulfur",
                help="Enter keywords separated by spaces"
            )
        
        with col2:
            max_papers = st.number_input("Max papers", min_value=1, max_value=50, value=10)
        
        if st.button("Search Papers") and search_terms:
            keywords = search_terms.split()
            
            with st.spinner("Searching papers..."):
                papers = self.anima.search_papers(keywords, max_papers)
            
            if papers:
                st.success(f"Found {len(papers)} papers")
                
                for i, paper in enumerate(papers):
                    with st.expander(f"📄 {paper.get('title', 'Unknown Title')}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown(f"**Authors:** {', '.join(paper.get('authors', []))}")
                            st.markdown(f"**Published:** {paper.get('published', 'Unknown')}")
                            st.markdown(f"**Source:** {paper.get('source', 'Unknown')}")
                            
                            if paper.get('abstract'):
                                st.markdown("**Abstract:**")
                                st.text(paper['abstract'][:500] + "..." if len(paper['abstract']) > 500 else paper['abstract'])
                        
                        with col2:
                            if paper.get('relevance_score'):
                                st.metric("Relevance", f"{paper['relevance_score']:.2f}")
                            
                            if paper.get('pdf_url'):
                                st.markdown(f"[📄 PDF]({paper['pdf_url']})")
                            if paper.get('url'):
                                st.markdown(f"[🔗 Link]({paper['url']})")
            else:
                st.warning("No papers found. Try different search terms.")
    
    def show_data_explorer(self):
        """Data exploration and filtering interface"""
        st.title("🗂️ Data Explorer")
        st.markdown("Explore and filter exoplanet analysis data")
        
        # Filters
        with st.sidebar:
            st.markdown("### Filters")
            
            habitable_only = st.checkbox("Habitable zone only")
            has_atmosphere = st.checkbox("Has atmospheric data")
            
            detection_method = st.selectbox(
                "Detection method",
                ["All", "Transit", "Radial Velocity"]
            )
            
            radius_range = st.slider(
                "Planet radius (Earth radii)",
                min_value=0.1,
                max_value=20.0,
                value=(0.1, 20.0)
            )
        
        # Apply filters
        filters = {
            'habitable_only': habitable_only,
            'has_atmosphere': has_atmosphere,
            'min_radius': radius_range[0],
            'max_radius': radius_range[1]
        }
        
        if detection_method != "All":
            filters['detection_method'] = detection_method.lower().replace(" ", "_")
        
        # Get filtered data
        data = self.isitva.search_exoplanets(filters)
        
        if data:
            st.markdown(f"### Found {len(data)} exoplanets")
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Display summary statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                habitable_count = df['in_habitable_zone'].sum() if 'in_habitable_zone' in df.columns else 0
                st.metric("In Habitable Zone", int(habitable_count))
            
            with col2:
                if 'planet_radius_earth' in df.columns:
                    avg_radius = df['planet_radius_earth'].mean()
                    st.metric("Avg Radius", f"{avg_radius:.2f} R⊕" if not pd.isna(avg_radius) else "N/A")
            
            with col3:
                if 'habitability_index' in df.columns:
                    avg_hab = df['habitability_index'].mean()
                    st.metric("Avg Habitability", f"{avg_hab:.2f}" if not pd.isna(avg_hab) else "N/A")
            
            # Data table
            st.markdown("### Data Table")
            
            # Select relevant columns for display
            display_cols = [
                'filename', 'in_habitable_zone', 'h2o_detected', 'sulfur_detected',
                'planet_radius_earth', 'habitability_index', 'timestamp'
            ]
            available_cols = [col for col in display_cols if col in df.columns]
            
            if available_cols:
                st.dataframe(df[available_cols], use_container_width=True)
            
            # Visualization
            st.markdown("### Visualizations")
            self._plot_filtered_data(df)
            
        else:
            st.info("No data matches the selected filters.")
    
    def show_simulations(self):
        """Transit simulation interface"""
        st.title("🌟 Transit Simulations")
        st.markdown("Run exoplanet transit simulations")
        
        # Simulation parameters
        st.markdown("### Simulation Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            radius_ratio = st.slider("Planet/Star Radius Ratio", 0.01, 0.3, 0.1, 0.01)
            period = st.slider("Orbital Period (days)", 0.5, 365.0, 3.0)
            inclination = st.slider("Inclination (degrees)", 80.0, 90.0, 90.0)
        
        with col2:
            semi_major_axis = st.slider("Semi-major Axis (AU)", 0.01, 2.0, 0.05)
            n_exposures = st.slider("Number of Exposures", 50, 500, 100)
            obs_duration = st.slider("Observation Duration (hours)", 2.0, 24.0, 6.0)
        
        planet_params = {
            'radius_ratio': radius_ratio,
            'period': period,
            'inclination': inclination,
            'semi_major_axis': semi_major_axis,
            'n_exposures': n_exposures,
            'obs_duration': obs_duration
        }
        
        # Run simulation
        if st.button("Run Simulation"):
            with st.spinner("Running transit simulation..."):
                try:
                    results = self.anima.run_simulation(planet_params)
                    
                    if 'error' not in results:
                        st.success("Simulation completed!")
                        
                        # Display results
                        self._display_simulation_results(results)
                    else:
                        st.error(f"Simulation failed: {results['error']}")
                        
                except Exception as e:
                    st.error(f"Simulation error: {str(e)}")
    
    def _display_analysis_results(self, results: Dict[str, Any]):
        """Display PDF analysis results"""
        # Summary metrics
        st.markdown("### Analysis Summary")
        
        col1, col2, col3 = st.columns(3)
        
        composition = results.get('chemical_composition', {})
        hz_data = results.get('habitable_zone', {})
        metrics = results.get('computed_metrics', {})
        
        with col1:
            species_count = len(composition.get('detected_species', []))
            st.metric("Chemical Species", species_count)
        
        with col2:
            is_habitable = hz_data.get('in_habitable_zone', False)
            st.metric("Habitable Zone", "Yes" if is_habitable else "No")
        
        with col3:
            hab_index = metrics.get('habitability_index', 0)
            st.metric("Habitability Index", f"{hab_index:.2f}")
        
        # Detailed results in tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Chemical Composition", "Detection Methods", "Habitability", "Raw Data"])
        
        with tab1:
            detected = composition.get('detected_species', [])
            if detected:
                st.markdown("**Detected Species:**")
                for species in detected:
                    st.markdown(f"- {species.upper()}")
                
                abundances = composition.get('abundances', {})
                if abundances:
                    st.markdown("**Abundances:**")
                    for species, data in abundances.items():
                        st.markdown(f"- {species}: {data['value']} {data['unit']}")
            else:
                st.info("No chemical species detected")
        
        with tab2:
            rv_data = results.get('radial_velocity', {})
            transit_data = results.get('transit_analysis', {})
            
            if rv_data.get('k_velocity'):
                st.markdown("**Radial Velocity Detection:**")
                st.markdown(f"- K velocity: {rv_data['k_velocity']:.2f} m/s")
                if rv_data.get('minimum_mass'):
                    st.markdown(f"- Minimum mass: {rv_data['minimum_mass']:.2f} Earth masses")
            
            if transit_data.get('depth'):
                st.markdown("**Transit Detection:**")
                st.markdown(f"- Transit depth: {transit_data['depth']:.6f}")
                if transit_data.get('radius_ratio'):
                    st.markdown(f"- Radius ratio: {transit_data['radius_ratio']:.3f}")
        
        with tab3:
            if hz_data.get('insolation'):
                st.markdown(f"**Insolation:** {hz_data['insolation']:.2f} S⊕")
            if hz_data.get('effective_temperature'):
                st.markdown(f"**Effective Temperature:** {hz_data['effective_temperature']:.1f} K")
            
            st.markdown(f"**In Habitable Zone:** {'Yes' if is_habitable else 'No'}")
        
        with tab4:
            st.json(results)
    
    def _display_simulation_results(self, results: Dict[str, Any]):
        """Display simulation results with plots"""
        # Metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            measured_depth = results.get('transit_depth_measured', 0)
            st.metric("Transit Depth", f"{measured_depth:.6f}")
        
        with col2:
            expected_depth = results.get('transit_depth_expected', 0)
            st.metric("Expected Depth", f"{expected_depth:.6f}")
        
        with col3:
            planet_params = results.get('planet_params', {})
            radius_ratio = planet_params.get('radius_ratio', 0)
            st.metric("Radius Ratio", f"{radius_ratio:.3f}")
        
        # Light curve plot
        st.markdown("### Transit Light Curve")
        
        times = np.array(results.get('times', []))
        fluxes = np.array(results.get('fluxes', []))
        model = np.array(results.get('light_curve_model', []))
        
        if len(times) > 0 and len(fluxes) > 0:
            fig = go.Figure()
            
            # Add observed data
            fig.add_trace(go.Scatter(
                x=times,
                y=fluxes,
                mode='markers',
                name='Observed',
                marker=dict(size=4, color='blue', opacity=0.7)
            ))
            
            # Add model if available
            if len(model) > 0:
                fig.add_trace(go.Scatter(
                    x=times,
                    y=np.median(fluxes) * model / np.median(model),
                    mode='lines',
                    name='Model',
                    line=dict(color='red', width=2)
                ))
            
            fig.update_layout(
                title="Transit Light Curve",
                xaxis_title="Time (hours)",
                yaxis_title="Flux",
                width=800,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Parameters table
        st.markdown("### Simulation Parameters")
        params_df = pd.DataFrame([planet_params])
        st.dataframe(params_df.T, use_container_width=True)
    
    def _plot_atmospheric_composition(self, stats: Dict[str, Any]):
        """Plot atmospheric composition statistics"""
        atm_data = stats.get('atmospheric_composition', [])
        
        if atm_data:
            df = pd.DataFrame(atm_data)
            
            fig = px.bar(
                df,
                x='species',
                y='count',
                title="Atmospheric Species Detection",
                labels={'species': 'Chemical Species', 'count': 'Detection Count'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No atmospheric composition data available")
    
    def _plot_planet_types(self, stats: Dict[str, Any]):
        """Plot planet type distribution"""
        planet_data = stats.get('planet_type_distribution', [])
        
        if planet_data:
            df = pd.DataFrame(planet_data)
            
            fig = px.pie(
                df,
                values='count',
                names='planet_type',
                title="Planet Type Distribution"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No planet type data available")
    
    def _plot_filtered_data(self, df: pd.DataFrame):
        """Plot visualizations for filtered data"""
        if df.empty:
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Habitable zone distribution
            if 'in_habitable_zone' in df.columns:
                hz_counts = df['in_habitable_zone'].value_counts()
                fig = px.pie(
                    values=hz_counts.values,
                    names=['Not in HZ', 'In HZ'],
                    title="Habitable Zone Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Radius vs Habitability scatter plot
            if 'planet_radius_earth' in df.columns and 'habitability_index' in df.columns:
                fig = px.scatter(
                    df,
                    x='planet_radius_earth',
                    y='habitability_index',
                    color='in_habitable_zone' if 'in_habitable_zone' in df.columns else None,
                    title="Planet Radius vs Habitability",
                    labels={
                        'planet_radius_earth': 'Planet Radius (Earth radii)',
                        'habitability_index': 'Habitability Index'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)

def main():
    """Run the Streamlit app"""
    agent = VasitvaAgent()
    agent.run_dashboard()

if __name__ == "__main__":
    main()