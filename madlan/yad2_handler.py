import pandas as pd
import numpy as np
import streamlit as st
from .yad_2_column_identifier import identify_and_rename_columns, drop_sequential_identical_columns
import re

class Yad2Analyzer:
    """A class to analyze Yad2 real estate data"""
    
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
            
            # Drop rows where all values are None/NaN
            df = df.dropna(how='all')
            
            # Drop columns with sequential identical values
            df = drop_sequential_identical_columns(df)
            
            # Identify and rename columns
            df = identify_and_rename_columns(df)
            
            # Drop unwanted columns if they exist
            columns_to_drop = ['img_src', 'link2','where']
            df = df.drop([col for col in columns_to_drop if col in df.columns], axis=1)
            
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
        
        # Improved size extraction from info column
        def extract_size(info_text):
            if pd.isna(info_text):
                return None
            # Look for patterns like "120 מ״ר" or "120 מטר"
            size_pattern = r'(\d+)\s*(?:מ"ר|מטר|מ״ר)'
            match = re.search(size_pattern, str(info_text))
            if match:
                return float(match.group(1))
            return None
        
        self.df['size_numeric'] = self.df['info'].apply(extract_size)
        
        # Convert to numeric values
        self.df['price_numeric'] = pd.to_numeric(self.df['price_numeric'], errors='coerce')
        self.df['size_numeric'] = pd.to_numeric(self.df['size_numeric'], errors='coerce')
        
        # Calculate price per meter using vectorized operations
        mask = (self.df['size_numeric'] > 0) & self.df['price_numeric'].notna() & self.df['size_numeric'].notna()
        self.df.loc[mask, 'price_per_meter'] = (self.df.loc[mask, 'price_numeric'] / 
                                               self.df.loc[mask, 'size_numeric']).round(2)
        
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
    
    def analyze_price_changes(self):
        """Analyze price changes in properties"""
        price_changes = self.df[self.df['price_change'] != 0].copy()
        price_changes['change_type'] = price_changes['price_change'].apply(
            lambda x: 'Increase' if x > 0 else 'Decrease'
        )
        
        results = []
        for _, row in price_changes.iterrows():
            results.append({
                'Address': row['address'],
                'Price Change': f"₪{abs(row['price_change']):,.2f}",
                'Change Type': row['change_type'],
                'Current Price': f"₪{row['price_numeric']:,.2f}",
                'Link': row['link']
            })
        
        return pd.DataFrame(results)
    
    def calculate_indicators(self):
        """Calculate size-rooms indicators for optimal apartment sizes"""
        # Extract rooms number from info column
        def extract_rooms(info_text):
            if pd.isna(info_text):
                return None
            # Look for patterns like "3 חדרים" or "2.5 חדרים"
            rooms_pattern = r'(\d+(?:\.\d+)?)\s*חדרים'
            match = re.search(rooms_pattern, str(info_text))
            if match:
                return float(match.group(1))
            return None

        self.df['rooms_numeric'] = self.df['info'].apply(extract_rooms)
        
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