import pandas as pd
import re
import numpy as np
from .yad_2_column_identifier import identify_and_rename_columns

class Yad2RentalAnalyzer:
    """A class to analyze Yad2 rental property data"""
    
    def __init__(self, file_path):
        """Initialize with data file path and load the data"""
        self.file_path = file_path
        self.df = self._load_and_clean_data()
        if not self.df.empty:
            self.df = self._clean_price_values()
    
    def _load_and_clean_data(self):
        """Load and perform initial cleaning of the data"""
        try:
            # Load the CSV file
            data = pd.read_csv(self.file_path, encoding='utf-8')
            df = data.copy()
            
            # Use the Yad2 column identifier to properly name columns
            df = identify_and_rename_columns(df)
            
            # Basic cleaning
            df = df.dropna(how='all')
            df = df.drop_duplicates()
            df = df.reset_index(drop=True)
            
            # Drop rows that aren't rental listings (if any commercial listings exist)
            if 'info' in df.columns:
                df = df[~df['info'].str.contains('מסחרי|משרד', case=False, na=False)]
            
            return df
        
        except Exception as e:
            print(f"Error processing CSV file: {str(e)}")
            return pd.DataFrame()
    
    def _clean_price_values(self):
        """Clean price values to numeric format"""
        df_copy = self.df.copy()
        df_copy = df_copy.reset_index(drop=True)
        
        def clean_price(price_str):
            if pd.isna(price_str):
                return np.nan
            
            price_str = str(price_str)
            numeric_chars = []
            
            for char in price_str:
                if char.isdigit():
                    numeric_chars.append(char)
            
            if numeric_chars:
                try:
                    return int(''.join(numeric_chars))
                except ValueError:
                    return np.nan
            return np.nan
        
        # Find the price column (it might be named 'price' or 'price_1')
        price_col = next((col for col in df_copy.columns if 'price' in col), None)
        if price_col:
            df_copy['price_numeric'] = df_copy[price_col].apply(clean_price)
        
        self.df = df_copy
        return self.df
    
    def analyze_by_area(self):
        """Group and analyze rentals by area"""
        def extract_area(address):
            if pd.isna(address):
                return 'Unknown'
            # Handle both 'where' and 'address' columns
            parts = str(address).split(',')
            return parts[-1].strip() if len(parts) > 1 else parts[0].strip()
        
        # Find the appropriate column for location
        location_col = next((col for col in self.df.columns if col in ['where', 'address']), None)
        
        if location_col:
            self.df['area'] = self.df[location_col].apply(extract_area)
            
            area_analysis = self.df.groupby('area').agg({
                'price_numeric': ['mean', 'min', 'max', 'count']
            }).round(2)
            
            return area_analysis
        return pd.DataFrame()
    
    def find_cheaper_properties(self):
        """Find properties with below-average price"""
        if 'price_numeric' not in self.df.columns:
            return pd.DataFrame()
            
        average_price = self.df['price_numeric'].mean()
        
        self.df['price_difference_from_avg'] = None
        self.df['price_difference_percentage'] = None
        
        for index, row in self.df.iterrows():
            try:
                if pd.notna(row['price_numeric']):
                    difference = row['price_numeric'] - average_price
                    if difference < 0:
                        self.df.at[index, 'price_difference_from_avg'] = round(difference, 2)
                        percentage = (difference / average_price) * 100
                        self.df.at[index, 'price_difference_percentage'] = f"{round(percentage, 1)}%"
            except (ValueError, TypeError):
                continue
        
        # Find the link column
        link_col = next((col for col in self.df.columns if 'link' in col), None)
        columns_to_show = ['address' if 'address' in self.df.columns else 'where', 
                          'price_numeric', 'price_difference_from_avg', 
                          'price_difference_percentage']
        if link_col:
            columns_to_show.append(link_col)
        
        cheaper_properties = self.df[pd.notna(self.df['price_difference_from_avg'])][
            columns_to_show
        ].sort_values('price_difference_from_avg')
        
        return cheaper_properties
    
    def find_same_address(self):
        """Find properties with identical addresses"""
        address_col = next((col for col in self.df.columns if col in ['address', 'where']), None)
        if not address_col:
            return pd.DataFrame()
            
        duplicate_addresses = self.df.groupby(address_col).filter(lambda x: len(x) > 1)
        
        results = []
        link_col = next((col for col in self.df.columns if 'link' in col), None)
        
        for address, group in duplicate_addresses.groupby(address_col):
            for _, row in group.iterrows():
                result = {
                    'Address': address,
                    'Price': f"₪{row['price_numeric']:,.0f}",
                }
                if link_col:
                    result['Link'] = row[link_col]
                results.append(result)
        
        return pd.DataFrame(results)
    
    def find_same_street(self):
        """Find properties on the same street"""
        address_col = next((col for col in self.df.columns if col in ['address', 'where']), None)
        if not address_col:
            return pd.DataFrame()
            
        def extract_street_name(address):
            if not isinstance(address, str):
                return None
            parts = address.split(',')[0]
            return ' '.join(parts.split())
        
        df_streets = self.df.copy()
        df_streets['street_name'] = df_streets[address_col].apply(extract_street_name)
        
        duplicate_streets = df_streets.groupby('street_name').filter(lambda x: len(x) > 1)
        
        results = []
        link_col = next((col for col in self.df.columns if 'link' in col), None)
        
        for street, group in duplicate_streets.groupby('street_name'):
            if street is None:
                continue
            for _, row in group.iterrows():
                result = {
                    'Street': street,
                    'Full Address': row[address_col],
                    'Price': f"₪{row['price_numeric']:,.0f}",
                }
                if link_col:
                    result['Link'] = row[link_col]
                results.append(result)
        
        return pd.DataFrame(results)
    
    def get_display_data(self):
        """Get formatted data for website display"""
        display_df = self.df.copy()
        
        # Select and rename columns for display
        columns_to_display = {
            'link': 'לינק',
            'address': 'כתובת',
            'price_numeric': 'מחיר',
            'info': 'פרטים',
            'price_change': ' שינויי מחיר',
            'more_info_1': 'מידע נוסף 1',
            'more_info_2': 'מידע נוסף 2'
        }
        
        # Select available columns (some might not exist)
        available_columns = [col for col in columns_to_display.keys() if col in display_df.columns]
        display_df = display_df[available_columns]
        
        # Rename columns
        display_df = display_df.rename(columns={col: columns_to_display[col] for col in available_columns})
        
        # Format price with commas and ₪ symbol
        if 'Price' in display_df.columns:
            display_df['Price'] = display_df['Price'].apply(lambda x: f"₪{int(x):,}" if pd.notna(x) else '')
        
        # Clean up any NaN values
        display_df = display_df.fillna('')
        
        return display_df 