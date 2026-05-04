import pandas as pd

def clean_negative_scores(input_file, output_file):
    """
    Clean negative scores in the SEO results CSV file by converting them to 0.
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file
    """
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # List of columns containing scores that should be non-negative
    score_columns = [
        'total_score',
        'content_length_score',
        'heading_structure_score',
        'link_quality_score',
        'image_optimization_score',
        'navigation_score',
        'title_score',
        'description_score',
        'social_tags_score',
        'keyword_optimization_score',
        'technical_seo_score',
        'content_quality_score',
        'user_experience_score',
        'meta_elements_score'
    ]
    
    # Replace negative values with 0 for each score column
    for column in score_columns:
        if column in df.columns:
            df[column] = df[column].apply(lambda x: max(0, float(x)) if pd.notnull(x) else x)
    
    # Save the cleaned data
    df.to_csv(output_file, index=False)
    
    # Print summary of changes
    print("Score cleaning summary:")
    for column in score_columns:
        if column in df.columns:
            print(f"{column}:")
            print(f"  Min value: {df[column].min()}")
            print(f"  Max value: {df[column].max()}")
            print(f"  Mean value: {df[column].mean():.2f}")
            print()

if __name__ == "__main__":
    input_file = "misinformation_seo_results.csv"
    output_file = "misinformation_seo_results_cleaned.csv"
    
    clean_negative_scores(input_file, output_file)
    print(f"Cleaned data saved to {output_file}")
