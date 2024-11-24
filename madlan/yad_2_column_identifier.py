import pandas as pd
import re
import os

def identify_column(series):
    """Identify column type based on its content"""
    sample = series.dropna().head(20)
    
    # Check for links first
    if sample.str.contains('http').any():
        if sample.str.contains('yad2').any():
            return 'link'
        elif sample.str.contains('img').any():
            return 'img_src'
    
    # Enhanced price pattern checking
    if sample.str.contains('₪|שח|ש"ח', regex=True).any():
        # If it contains price change indicators, it's a price change column
        if sample.str.contains('ירד|עלה|עודכן', regex=True).any():
            return 'price_change'
        # If it has currency symbols and numbers, it's likely the main price column
        elif sample.str.contains(r'[0-9]', regex=True).any():
            return 'price'
    
    # Rest of the patterns remain the same
    if sample.str.contains('רחוב|שכונה|דירה', regex=True).any():
        return 'address'
    
    if sample.str.contains('מ"ר|חדרים|קומה', regex=True).any():
        return 'info'
    
    if sample.str.contains('תיווך|מתווך|פרטי', regex=True).any():
        return 'publisher'
    
    if sample.str.contains('צפון|דרום|מזרח|מערב|שכונה', regex=True).any():
        return 'where'
    
    # If no specific pattern is found, consider it as additional info
    return 'more_info'

def identify_and_rename_columns(df):
    """Identify and rename columns in the DataFrame"""
    # Drop columns with sequential identical values first
    df = drop_sequential_identical_columns(df)
    
    # Identify columns
    column_types = []
    for col in df.columns:
        col_type = identify_column(df[col])
        column_types.append(col_type)
    
    # Rename columns based on identification
    new_columns = []
    type_counts = {}  # Keep track of how many times we've seen each type
    
    for col_type in column_types:
        if col_type == 'more_info':
            new_columns.append(f'more_info_{len([x for x in new_columns if "more_info" in x]) + 1}')
        else:
            # If we've seen this type before, add a number to it
            if col_type in type_counts:
                type_counts[col_type] += 1
                new_columns.append(f'{col_type}_{type_counts[col_type]}')
            else:
                type_counts[col_type] = 1
                new_columns.append(col_type)
    
    # Ensure no duplicate column names
    df.columns = pd.Index(new_columns)
    return df

def main():
    """Example usage of column identification functions"""
    try:
        # Use the uploaded file path
        file_path = os.path.join('madlan', 'madlan.csv')
        
        # Read the uploaded CSV file
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # Apply column identification and renaming
        df = identify_and_rename_columns(df)
        
        # Print original and new column names
        print("\nOriginal number of columns:", len(df.columns))
        print("\nIdentified column types:")
        for i, col in enumerate(df.columns):
            print(f"Column {i+1}: {col}")
            
        # Print sample of renamed DataFrame
        print("\nSample of renamed DataFrame:")
        print(df.head())
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")

def drop_sequential_identical_columns(df):
    """Drop columns where sequential values are identical"""
    columns_to_drop = []
    
    for column in df.columns:
        # Get first value
        first_value = df[column].iloc[0]
        # Check if next 19 values are identical to first (total of 20 values)
        if df[column].iloc[1:20].eq(first_value).all():
            columns_to_drop.append(column)
    
    # Drop the columns and return the DataFrame
    if columns_to_drop:
        df = df.drop(columns=columns_to_drop)
    
    return df

if __name__ == "__main__":
    main()