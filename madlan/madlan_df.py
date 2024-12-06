import pandas as pd
import numpy as np
import streamlit as st

class MadlanAnalyzer:
    """A class to analyze Madlan real estate data"""
    
    def __init__(self, file_path):
        """Initialize with data file path and load the data"""
        self.file_path = file_path
        self.df = self._load_and_clean_data()
        if not self.df.empty:
            self.df = self._calculate_price_per_meter()
            self.df = self.calculate_indicators()
    
    def _load_and_clean_data(self):
        """Load and perform initial cleaning of the data"""
        try:
            # Load the CSV file
            data = pd.read_csv(self.file_path, encoding='utf-8')
            df = data.copy()
            
            if len(df.columns) == 9:  
                df.columns = ['link', 'price', 'rooms', 'floor', 
                              'size', 'adress', 'price_change', 'price_change', 
                              'exclusive']
            # Check number of columns and assign appropriate column names
            if len(df.columns) == 12:  # No project_name column
                df.columns = ['link', 'image_src', 'address', 'rooms', 'floor', 
                             'floor_info', 'size', 'area', 'price', 'developer_link', 
                             'developer_image', 'exclusive']
                 # Drop unwanted columns
                columns_to_drop = ['floor_info', 'developer_image', 'area']
                df = df.drop(columns_to_drop, axis=1)
            elif len(df.columns) == 13:  # With project_name
                df.columns = ['link', 'image_src', 'address', 'rooms', 'floor', 
                             'floor_info', 'size', 'area', 'price', 'developer_link', 
                             'developer_image', 'project_name', 'exclusive']
                columns_to_drop = ['floor_info', 'developer_image', 'area']
                df = df.drop(columns_to_drop, axis=1)
            elif len(df.columns) == 14:  # With info column after image_src
                df.columns = ['link', 'image_src', 'address', 'rooms', 'floor', 
                             'floor_info', 'size', 'area', 'price', 'developer_link', 
                             'developer_image', 'info', 'project_name', 'exclusive']
                columns_to_drop = ['floor_info', 'developer_image', 'area', 'info']
                df = df.drop(columns_to_drop, axis=1)
            
            # Drop rows containing 'projects' in the link
            df = df[~df['link'].str.contains('projects', case=False, na=False)]
            
            # Basic cleaning
            df = df.drop_duplicates()
            
            return df
            
        except Exception as e:
            st.error(f"Error processing CSV file: {str(e)}")
            return pd.DataFrame()
    
    def _calculate_price_per_meter(self):
        """Calculate price per meter for each property"""
        self.df['price_per_meter'] = None
        
        # Create new columns for numeric values while preserving original data
        self.df['price_numeric'] = self.df['price'].apply(lambda x: ''.join(char for char in str(x) if char.isdigit()))
        
        # Improved size extraction
        def extract_size(size_str):
            if pd.isna(size_str):
                return None
            # Extract only digits and decimal points
            numeric_str = ''.join(char for char in str(size_str) if char.isdigit() or char == '.')
            try:
                # Convert to float
                return float(numeric_str) if numeric_str else None
            except ValueError:
                return None
        
        self.df['size_numeric'] = self.df['size'].apply(extract_size)
        
        # Convert price to numeric values
        self.df['price_numeric'] = pd.to_numeric(self.df['price_numeric'], errors='coerce')
        
        # Calculate price per meter using vectorized operations
        mask = (self.df['size_numeric'] > 0) & self.df['price_numeric'].notna() & self.df['size_numeric'].notna()
        self.df.loc[mask, 'price_per_meter'] = (self.df.loc[mask, 'price_numeric'] / 
                                               self.df.loc[mask, 'size_numeric'])
        
        return self.df
    
    def find_cheaper_properties(self):
        """Find properties with below-average price per meter"""
        average_price_per_meter = self.df['price_per_meter'].mean()
        
        self.df['price_difference_from_avg'] = None
        self.df['price_difference_percentage'] = None
        
        for index, row in self.df.iterrows():
            try:
                if pd.notna(row['price_per_meter']):
                    difference = row['price_per_meter'] - average_price_per_meter
                    if difference < 0:
                        self.df.at[index, 'price_difference_from_avg'] = round(difference, 2)
                        percentage = (difference / average_price_per_meter) * 100
                        self.df.at[index, 'price_difference_percentage'] = f"{round(percentage, 1)}%"
            except (ValueError, TypeError) as e:
                continue
        
        cheaper_properties = self.df[pd.notna(self.df['price_difference_from_avg'])][
            ['address', 'price_per_meter', 'price_difference_from_avg', 
             'price_difference_percentage', 'link']
        ].sort_values('price_difference_from_avg')
        
        print(f"\nAverage price per meter: {round(average_price_per_meter, 2)}")
        print(f"\nFound {len(cheaper_properties)} properties cheaper than average")
        
        return cheaper_properties
    
    def find_same_address(self):
        """Find properties with identical addresses"""
        duplicate_addresses = self.df.groupby('address').filter(lambda x: len(x) > 1)
        
        results = []
        for address, group in duplicate_addresses.groupby('address'):
            for link in group['link']:
                results.append({
                    'Address': address,
                    'Link': link
                })
        
        return pd.DataFrame(results)
    
    def find_same_street(self):
        """Find properties on the same street"""
        def extract_street_name(address):
            if not isinstance(address, str):
                return None
            street = ''.join(char for char in address if not char.isdigit())
            return ' '.join(street.split())
        
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
                    'Link': row['link']
                })
        
        return pd.DataFrame(results)
    
    def calculate_indicators(self):
        """Calculate size-rooms indicators for optimal apartment sizes"""
        # Create rooms_numeric column with better error handling
        def extract_numeric_rooms(x):
            if pd.isna(x) or str(x).strip() == '':
                return None
            # Extract only digits and decimal points
            numeric_chars = ''.join(char for char in str(x) if char.isdigit() or char == '.')
            try:
                # Handle cases with multiple decimal points
                if numeric_chars.count('.') > 1:
                    numeric_chars = numeric_chars.replace('.', '', numeric_chars.count('.') - 1)
                return float(numeric_chars) if numeric_chars else None
            except ValueError:
                return None

        self.df['rooms_numeric'] = self.df['rooms'].apply(extract_numeric_rooms)
        
        # Initialize indicator column
        self.df['size_rooms_indicator'] = 'regular'
        
        # Define optimal conditions
        condition1 = (
            (self.df['size_numeric'] > 60) & 
            (self.df['size_numeric'] < 75) & 
            (self.df['rooms_numeric'] == 2)
        )
        
        condition2 = (
            (self.df['size_numeric'] > 75) & 
            (self.df['size_numeric'] < 90) & 
            ((self.df['rooms_numeric'] == 2) | (self.df['rooms_numeric'] == 3))
        )
        
        # Set indicators
        self.df.loc[condition1 | condition2, 'size_rooms_indicator'] = 'optimal'
        
        return self.df

def main():
    """Example usage of the MadlanAnalyzer class"""
    # Create analyzer instance
    analyzer = MadlanAnalyzer('madlan.csv')
    
    # Find cheaper properties
    cheap_properties = analyzer.find_cheaper_properties()
    print("\nCheaper Properties:")
    print(cheap_properties)
    
    # Find duplicate addresses
    address_duplicates = analyzer.find_same_address()
    print("\nDuplicate Addresses:")
    print(address_duplicates)
    
    # Find properties on same streets
    street_duplicates = analyzer.find_same_street()
    print("\nSame Street Properties:")
    print(street_duplicates)

if __name__ == "__main__":
    main()
