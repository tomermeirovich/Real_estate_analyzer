import streamlit as st
import pandas as pd
import os
from madlan.madlan_df import MadlanAnalyzer
from madlan.yad2_handler import Yad2Analyzer
from madlan.rental_analyzer import RentalAnalyzer
from madlan.yad2_rental_analyzer import Yad2RentalAnalyzer

def save_uploaded_file(uploaded_file):
    """Save uploaded file to madlan directory"""
    if not os.path.exists('madlan'):
        os.makedirs('madlan')
    
    with open(os.path.join('madlan', 'madlan.csv'), 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return True

def landing_page():
    st.title("Real Estate Data Analysis")
    st.markdown("Choose your data source or upload your own CSV file")
    
    # Upload file first
    uploaded_file = st.file_uploader("Choose a CSV file", type='csv')
    
    if uploaded_file is not None:
        st.success("File uploaded successfully!")
        save_uploaded_file(uploaded_file)
        
        # Create three columns for the buttons
        col1, col2, col3 = st.columns(3)
        
        # Source selection
        with col1:
            source_type = st.radio("Select Analysis Type",
                                  ["Purchase", "Rental"],
                                  horizontal=True)

        if source_type == "Purchase":
            with col2:
                if st.button("Madlan Data", use_container_width=True):
                    st.session_state.source = 'madlan'
            with col3:
                if st.button("Yad2 Data", use_container_width=True):
                    st.session_state.source = 'yad2'
        else:  # Rental section
            with col2:
                if st.button("Madlan Rental", use_container_width=True):
                    st.session_state.source = 'madlan_rental'
            with col3:
                if st.button("Yad2 Rental", use_container_width=True):
                    st.session_state.source = 'yad2_rental'
        
        # Generate button
        if st.session_state.get('source'):
            if st.button("Generate Analysis", type="primary", use_container_width=True):
                st.session_state.page = 'analysis'
                st.rerun()
        else:
            st.warning("Please select a data source (Madlan, Yad2, or Rental)")

def analysis_page():
    # Get the data source from session state
    data_source = st.session_state.get('source', 'madlan')
    
    st.set_page_config(page_title=f"{data_source.title()} Data Analysis", layout="wide")
    
    # Title and description
    st.title(f"{data_source.title()} Real Estate Analysis")
    st.markdown(f"Analyze real estate data from {data_source.title()}")
    
    # Initialize appropriate analyzer based on source
    if data_source in ['madlan', 'madlan_rental']:
        if data_source == 'madlan_rental':
            analyzer = RentalAnalyzer('madlan/madlan.csv')
        else:
            analyzer = MadlanAnalyzer('madlan/madlan.csv')
    elif data_source in ['yad2', 'yad2_rental']:
        if data_source == 'yad2_rental':
            analyzer = RentalAnalyzer('madlan/madlan.csv')
        else:
            analyzer = Yad2Analyzer('madlan/madlan.csv')
    
    # Sidebar for navigation with different options based on source type
    if data_source in ['madlan_rental', 'yad2_rental']:
        analysis_type = st.sidebar.selectbox(
            "Choose Analysis Type",
            ["Raw Data", "Properties Below Average Rent", "Same Address Properties", "Same Street Properties"]
        )
    else:
        analysis_type = st.sidebar.selectbox(
            "Choose Analysis Type",
            ["Raw Data", "Cheaper Properties", "Same Address Properties", "Same Street Properties"]
        )
    
    # Display different analyses based on selection
    if analysis_type == "Raw Data":
        st.header("Raw Data")
        
        # Define desired columns based on data source
        if data_source == 'yad2_rental':
            display_df = analyzer.get_display_data()
            st.dataframe(
                display_df,
                column_config={
                    "link": st.column_config.LinkColumn(
                        "Link",
                        help="Click to open property page",
                        display_text="לינק"
                    ),
                    "address": st.column_config.TextColumn("כתובת"),
                    "price": st.column_config.NumberColumn("מחיר", format="₪%d"),
                    "info": st.column_config.NumberColumn("פרטים"),
                    "more_info_1": st.column_config.TextColumn("מידע ננוסף 1"),
                    "more_info_2": st.column_config.TextColumn("מידע ננוסף 2"),
                    "price_change": st.column_config.TextColumn("שינויי מחיר"),
                    
                    
                },
                hide_index=True
            )
            
            # Add download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name='yad2_rental_data.csv',
                mime='text/csv',
            )
        elif data_source == 'yad2':
            # First get all possible columns
            all_columns = ['link', 'publisher', 'price', 'info', 'address', 
                          'more_info_1', 'more_info_2', 'more_info_3', 
                          'price_change', 'price_per_meter', 'size_rooms_indicator']

            # Get available columns that exist in the DataFrame
            available_columns = [col for col in all_columns if col in analyzer.df.columns]

            if not available_columns:
                st.error("No valid columns found in the uploaded data")
                return

            # Create display DataFrame with only visible columns
            display_df = analyzer.df[available_columns].copy()

            # Add style conditions for optimal indicators
            styled_df = display_df.style.apply(
                lambda x: ['background-color: #90EE90' if v == 'optimal' else '' 
                          for v in x] if x.name == 'size_rooms_indicator' 
                          else ['' for _ in x], 
                axis=0
            )
            
            st.dataframe(
                styled_df,
                column_config={
                    "link": st.column_config.LinkColumn(
                        "לינק",
                        help="Click to open link",
                        display_text="Link"),
                    "price": st.column_config.TextColumn("מחיר"),
                    "price_per_meter": st.column_config.NumberColumn("מחיר למטר", format="₪%d"),
                    "info": st.column_config.TextColumn("פרטים"),
                    "address": st.column_config.TextColumn("כתובת"),
                    "publisher": st.column_config.TextColumn("מפרסם"),
                    "price_change": st.column_config.NumberColumn("שינויי מחיר", format="₪%d"),
                    "more_info_1": st.column_config.TextColumn("מידע נוסף 1"),
                    "more_info_2": st.column_config.TextColumn("מידע נוסף 2"),
                    "size_rooms_indicator": st.column_config.TextColumn("פוטנציאל השבחה")
                },
                hide_index=True
            )
            
            # Define Hebrew column names mapping
            hebrew_columns = {
                'link': 'לינק',
                'publisher':'מפרסם',
                'info':'פרטים',
                'price_change':'שינויי מחיר',
                'more_info_1':'מידע נוסף 1',
                'more_info_2':'מידע נוסף 2',
                'address': 'כתובת',
                'rooms': 'חדרים',
                'floor': 'קומה',
                'size': 'גודל',
                'price': 'מחיר',
                'project_name': 'שם הפרוייקט',
                'exclusive': 'בלעדיות',
                'price_per_meter': 'מיר למטר',
                'developer_link': 'לינק יזם',
                'size_rooms_indicator': 'פוטנציאל השבחה'
            }
            
            # Convert the styled dataframe back to regular dataframe for download
            download_df = styled_df.data  # This gets the data without the styling
            # Rename columns for download
            download_df = download_df.rename(columns=hebrew_columns)
            csv = download_df.to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=f'{data_source}_data.csv',
                mime='text/csv',
            )
        else:  # Madlan data
            # First get all columns including those needed for calculations
            all_columns = ['link', 'address', 'rooms', 'floor', 'size',
                          'price', 'project_name', 'exclusive', 'price_per_meter',
                          'developer_link', 'size_rooms_indicator']

            # Get available columns that exist in the DataFrame
            available_columns = [col for col in all_columns if col in analyzer.df.columns]

            if not available_columns:
                st.error("No valid columns found in the uploaded data")
                return

            # Create display DataFrame with only visible columns
            display_df = analyzer.df[available_columns].copy()

            # Add style conditions for optimal indicators
            styled_df = display_df.style.apply(
                lambda x: ['background-color: #90EE90' if v == 'optimal' else '' 
                          for v in x] if x.name == 'size_rooms_indicator' 
                          else ['' for _ in x], 
                axis=0
            )
            
            st.dataframe(
                styled_df,
                column_config={
                    "link": st.column_config.LinkColumn(
                        "לינק",
                        help="Click to open link",
                        display_text="Link"),
                    "developer_link": st.column_config.LinkColumn(
                        "מפתח",
                        help="Click to open developer link",
                        display_text="Link"),
                    "price": st.column_config.TextColumn("מחיר"),
                    "size": st.column_config.NumberColumn("גודל"),
                    "rooms": st.column_config.NumberColumn("חדרים"),
                    "floor": st.column_config.TextColumn("קומה"),
                    "project_name": st.column_config.TextColumn("שם הפרוייקט"),
                    "exclusive": st.column_config.TextColumn("בלעדיות"),
                    "price_per_meter": st.column_config.NumberColumn("מחיר למטר", format="₪%d"),
                    "address": st.column_config.TextColumn("כתובת"),
                    "size_rooms_indicator": st.column_config.TextColumn("פוטנציאל השבחה")
                },
            )
            
            # Define Hebrew column names mapping
            hebrew_columns = {
                'link': 'לינק',
                'address': 'כתובת',
                'rooms': 'חדרים',
                'floor': 'קומה',
                'size': 'גודל',
                'price': 'מחיר',
                'project_name': 'שם הפרוייקט',
                'exclusive': 'בלעדיות',
                'price_per_meter': 'מחיר למטר',
                'developer_link': 'לינק יזם',
                'size_rooms_indicator': 'פוטנציאל השבחה'
            }
            
            # Convert the styled dataframe back to regular dataframe for download
            download_df = styled_df.data  # This gets the data without the styling
            # Rename columns for download
            download_df = download_df.rename(columns=hebrew_columns)
            csv = download_df.to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=f'{data_source}_data.csv',
                mime='text/csv',
            )
        # For Yad2 rental data, show these specific columns
        if data_source == 'yad2_rental':
            all_columns = ['link', 'address', 'price', 'info', 'price_change', 
                           'more_info_1', 'more_info_2']
        
        # Show basic statistics based on source type
        if data_source in ['madlan_rental', 'yad2_rental']:
            st.header("Basic Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'price_numeric' in analyzer.df.columns:
                    lowest_price = analyzer.df['price_numeric'].min()
                    st.metric("Lowest Rent", f"₪{lowest_price:,.0f}")
                else:
                    st.metric("Lowest Rent", "N/A")

            with col2:
                if 'price_numeric' in analyzer.df.columns:
                    highest_price = analyzer.df['price_numeric'].max()
                    st.metric("Highest Rent", f"₪{highest_price:,.0f}")
                else:
                    st.metric("Highest Rent", "N/A")

            with col3:
                if 'price_numeric' in analyzer.df.columns:
                    avg_price = analyzer.df['price_numeric'].mean()
                    st.metric("Average Rent", f"₪{avg_price:,.0f}")
                else:
                    st.metric("Average Rent", "N/A")
        else:
            # Keep existing buying statistics code unchanged
            st.header("Basic Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if 'price_per_meter' in available_columns:
                    st.metric("Average Price per m²", 
                             f"₪{analyzer.df['price_per_meter'].mean():,.2f}")
                else:
                    st.metric("Average Price per m²", "N/A")
            
            with col2:
                if 'size_numeric' in analyzer.df.columns:
                    st.metric("Average Size", 
                             f"{analyzer.df['size_numeric'].mean():,.2f} m²")
                else:
                    st.metric("Average Size", "N/A")
            
            with col3:
                st.metric("Total Properties", 
                         len(analyzer.df))
            
            with col4:
                if data_source == 'yad2' and 'price_change' in available_columns:
                    price_changes = analyzer.df['price_change'].value_counts()
                    st.metric("Price Changes", len(price_changes[price_changes != 0]))
        
    elif analysis_type == "Cheaper Properties" and data_source not in ['madlan_rental', 'yad2_rental']:
        st.header("Properties Below Average Price")
        cheaper_props = analyzer.find_cheaper_properties()
        st.dataframe(
            cheaper_props,
            column_config={
                "link": st.column_config.LinkColumn("Link", display_text="Link")
            }
        )
        
        # Add horizontal statistics
        stats_container = st.container()
        with stats_container:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average Price per m²", 
                         f"₪{analyzer.df['price_per_meter'].mean():,.2f}")
            with col2:
                st.metric("Properties Below Average", 
                         len(cheaper_props))
        
        # Visualization of price differences
        if not cheaper_props.empty:
            st.bar_chart(cheaper_props['price_difference_percentage'])
            
    elif analysis_type == "Properties Below Average Rent" and data_source in ['madlan_rental', 'yad2_rental']:
        st.header("Properties Below Average Rent")
        cheaper_props = analyzer.find_cheaper_properties()
        st.dataframe(
            cheaper_props,
            column_config={
                "link": st.column_config.LinkColumn("Link", display_text="Link"),
                "price_numeric": st.column_config.NumberColumn("מחיר", format="₪%d"),
                "price_difference_from_avg": st.column_config.NumberColumn("הפרש מהממוצע", format="₪%d"),
                "price_difference_percentage": st.column_config.TextColumn("אחוז הפרש"),
                "address": st.column_config.TextColumn("כתובת")
            },
            hide_index=True
        )
        
        # Add statistics
        stats_container = st.container()
        with stats_container:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average Rent", 
                         f"₪{analyzer.df['price_numeric'].mean():,.0f}")
            with col2:
                st.metric("Properties Below Average", 
                         len(cheaper_props))
        
        # Visualization
        if not cheaper_props.empty:
            st.bar_chart(cheaper_props['price_difference_percentage'])

    elif analysis_type == "Properties at Same Address" and data_source in ['madlan_rental', 'yad2_rental']:
        st.header("Properties at Same Address")
        same_address = analyzer.find_same_address()
        st.dataframe(
            same_address,
            column_config={
                "Link": st.column_config.LinkColumn("Link", display_text="Link"),
                "Address": st.column_config.TextColumn("Address"),
                "Price": st.column_config.TextColumn("Price")
            },
            hide_index=True
        )
        
        stats_container = st.container()
        with stats_container:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Addresses", 
                         len(same_address['Address'].unique()))
            with col2:
                st.metric("Total Properties", 
                         len(same_address))

    else:  # Same Street Properties
        st.header("Properties on Same Street")
        same_street = analyzer.find_same_street()
        st.dataframe(
            same_street,
            column_config={
                "Link": st.column_config.LinkColumn("Link", display_text="Link")
            }
        )
        
        # Add horizontal statistics
        stats_container = st.container()
        with stats_container:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Streets", 
                         len(same_street['Street'].unique()))
            with col2:
                st.metric("Total Properties", 
                         len(same_street))
        
        if not same_street.empty:
            st.subheader("Number of Properties per Street")
            st.bar_chart(same_street['Street'].value_counts())

def display_rental_data():
    analyzer = Yad2RentalAnalyzer('path/to/data.csv')
    display_data = analyzer.get_display_data()
    
    # Display in Streamlit
    st.dataframe(
        display_data,
        column_config={
            "Link": st.column_config.LinkColumn(),
            "Price": st.column_config.TextColumn(width="medium"),
            "Info": st.column_config.TextColumn(width="large"),
        },
        hide_index=True
    )

def main():
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'landing'
    if 'source' not in st.session_state:
        st.session_state.source = None
    
    # Navigation
    if st.session_state.page == 'landing':
        landing_page()
    else:
        analysis_page()
        
        # Add a return button
        if st.sidebar.button("Return to Home"):
            st.session_state.page = 'landing'
            st.session_state.source = None
            st.rerun()

if __name__ == "__main__":
    main()
