import pandas as pd
import re

def identify_column(series):
    """Identify column type based on its content"""
    sample = series.dropna().head(20)
    
    # Check for links and images first
    if sample.str.contains('http').any():
        if sample.str.contains('madlan').any():
            return 'link'
        elif sample.str.contains('developer|agents').any():
            return 'developer_link'
        elif sample.str.contains('img|image|jpg|png|images2', regex=True).any():
            return 'image_src'
    
    # Check for address patterns
    if sample.str.contains('רחוב|שכונה|דירה|,', regex=True).any():
        return 'address'
    
    # Check for room patterns
    if sample.str.contains(r'\d+(\.\d+)?\s*חדרים', regex=True).any():
        return 'rooms'
    
    # Check for floor patterns
    if sample.str.contains('קומה|קרקע|מרתף', regex=True).any():
        return 'floor'
    
    # Check for size patterns
    if sample.str.contains('מ"ר|מטר', regex=True).any():
        return 'size'
    
    # Check for price patterns
    if sample.str.contains('₪|שח|ש"ח', regex=True).any():
        return 'price'
    
    # Check for project name patterns
    if sample.str.contains('פרויקט|מתחם', regex=True).any():
        return 'project_name'
    
    # Check for exclusive patterns
    if sample.str.contains('בלעדי|אקסקלוסיבי', regex=True).any():
        return 'exclusive'
    
    # If no specific pattern is found
    return 'additional_info'

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
    type_counts = {}
    
    for col_type in column_types:
        if col_type == 'additional_info':
            new_columns.append(f'additional_info_{len([x for x in new_columns if "additional_info" in x]) + 1}')
        else:
            if col_type in type_counts:
                type_counts[col_type] += 1
                new_columns.append(f'{col_type}_{type_counts[col_type]}')
            else:
                type_counts[col_type] = 1
                new_columns.append(col_type)
    
    df.columns = pd.Index(new_columns)
    return df

def drop_sequential_identical_columns(df):
    """Drop columns where sequential values are identical"""
    columns_to_drop = []
    
    for column in df.columns:
        first_value = df[column].iloc[0]
        if df[column].iloc[1:20].eq(first_value).all():
            columns_to_drop.append(column)
    
    if columns_to_drop:
        df = df.drop(columns=columns_to_drop)
    
    return df 