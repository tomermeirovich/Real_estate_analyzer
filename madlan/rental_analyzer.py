import pandas as pd
import re
import numpy as np

class RentalAnalyzer:
    """A class to analyze rental property data"""
    
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
            
            # Check number of columns and assign appropriate column names
            if len(df.columns) == 16:  # Standard rental listing format
                df.columns = ['link', 'delete_1','image_src', 'address', 'rooms', 'floor', 
                             'floor_info', 'size', 'area', 'price', 'developer_link', 
                             'image', 'exclusive','delete_2','price_change_1','price_change_2']
                # Drop unwanted columns
                columns_to_drop = ['delete_1', 'delete_2', 'area', 'image_src', 'image', 
                                 'floor_info']
                df = df.drop(columns_to_drop, axis=1)
            
                # Basic cleaning
                df = df.dropna(how='all')
                df = df.drop_duplicates()
                df = df.reset_index(drop=True)
                
              # Check number of columns and assign appropriate column names
            elif len(df.columns) == 12:  # Standard rental listing format
                df.columns = ['link', 'image_src', 'address', 'rooms', 'floor', 
                             'floor_info', 'size', 'area', 'price', 'developer_link', 
                             'image', 'exclusive']
                # Drop unwanted columns
                columns_to_drop = [ 'area', 'image_src', 'image', 
                                 'floor_info']
                df = df.drop(columns_to_drop, axis=1)
            
                # Basic cleaning
                df = df.dropna(how='all')
                df = df.drop_duplicates()
                df = df.reset_index(drop=True)
            
               # Check number of columns and assign appropriate column names
            elif len(df.columns) == 13:  # Standard rental listing format
                df.columns = ['link', 'image_src', 'address', 'rooms', 'floor', 
                             'floor_info', 'size', 'area', 'price', 'developer_link', 
                             'image', 'exclusive','project_name']
                # Drop unwanted columns
                columns_to_drop = [ 'area', 'image_src', 'image', 
                                 'floor_info','project_name']
                df = df.drop(columns_to_drop, axis=1)
            
                # Basic cleaning
                df = df.dropna(how='all')
                df = df.drop_duplicates()
                df = df.reset_index(drop=True)
            
              # Drop rows containing 'projects' in the link
            df = df[~df['link'].str.contains('projects', case=False, na=False)]
            
            return df
        
        except Exception as e:
            print(f"Error processing CSV file: {str(e)}")
            return pd.DataFrame()
    
    def _clean_price_values(self):
        """Clean price values to numeric format"""
        df_copy = self.df.copy()
        df_copy = df_copy.reset_index(drop=True)
        
        # Find the price column (it might be named 'price' or 'price_1')
        price_col = next((col for col in df_copy.columns if 'price' in col), None)
        if price_col:
            df_copy['price_numeric'] = df_copy[price_col].apply(
                lambda x: ''.join(char for char in str(x) if char.isdigit())
            )
            df_copy['price_numeric'] = pd.to_numeric(df_copy['price_numeric'], errors='coerce')
        
        self.df = df_copy
        return self.df
    
    def analyze_by_area(self):
        """Group and analyze rentals by area"""
        def extract_area(address):
            if pd.isna(address):
                return 'Unknown'
            parts = str(address).split(',')
            return parts[-1].strip() if len(parts) > 1 else parts[0].strip()
        
        self.df['area'] = self.df['address'].apply(extract_area)
        
        area_analysis = self.df.groupby('area').agg({
            'price_numeric': ['mean', 'min', 'max', 'count']
        }).round(2)
        
        return area_analysis
    
    def find_cheaper_properties(self):
        """Find properties with below-average price"""
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
            except (ValueError, TypeError) as e:
                continue
        
        cheaper_properties = self.df[pd.notna(self.df['price_difference_from_avg'])][
            ['address', 'price_numeric', 'price_difference_from_avg', 
             'price_difference_percentage', 'link']
        ].sort_values('price_difference_from_avg')
        
        return cheaper_properties
    
    def find_same_address(self):
        """Find properties with identical addresses"""
        duplicate_addresses = self.df.groupby('address').filter(lambda x: len(x) > 1)
        
        results = []
        for address, group in duplicate_addresses.groupby('address'):
            for _, row in group.iterrows():
                results.append({
                    'Address': address,
                    'Price': f"₪{row['price_numeric']:,.0f}",
                    'Link': row['link']
                })
        
        return pd.DataFrame(results)
    
    def find_same_street(self):
        """Find properties on the same street"""
        def extract_street_name(address):
            if not isinstance(address, str):
                return None
            parts = address.split(',')[0]  # Take first part before comma
            return ' '.join(parts.split())
        
        df_streets = self.df.copy()
        df_streets['street_name'] = df_streets['address'].apply(extract_street_name)
        
        duplicate_streets = df_streets.groupby('street_name').filter(lambda x: len(x) > 1)
        
        results = []
        for street, group in duplicate_streets.groupby('street_name'):
            if street is None:
                continue
            for _, row in group.iterrows():
                results.append({
                    'Street': street,
                    'Full Address': row['address'],
                    'Price': f"₪{row['price_numeric']:,.0f}",
                    'Link': row['link']
                })
        
        return pd.DataFrame(results)
    
    def get_display_data(self):
        """Get formatted data for website display"""
        display_df = self.df.copy()
        
        # Keep original column names, just select the ones we want to display
        columns_to_display = [
            'link', 'address', 'price', 'info', 'floor', 
            'size', 'developer_link', 'exclusive','more_info_1','price_change','more_info_2'
        ]
        
        # Select only available columns
        available_columns = [col for col in columns_to_display if col in display_df.columns]
        display_df = display_df[available_columns]
        
        # Clean up any NaN values
        display_df = display_df.fillna('')
        
        return display_df