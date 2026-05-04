import pandas as pd

def normalize_url(url):
    """Normalize URLs by removing http(s):// and www."""
    if isinstance(url, str):
        return url.replace('https://', '').replace('http://', '').replace('www.', '').strip().lower()
    return url

def compare_urls(input_file, output_file, missing_file):
    """
    Compare URLs between input and output files and save missing URLs to a new file.

    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file
        missing_file (str): Path to save missing URLs CSV file
    """
    try:
        # Read input URLs
        input_df = pd.read_csv(input_file)
        print(f"Total URLs in input file: {len(input_df)}")

        # Read output URLs
        output_df = pd.read_csv(output_file)
        print(f"Total URLs in output file: {len(output_df)}")

        # Normalize URLs in both dataframes
        input_urls = set(input_df['url'].apply(normalize_url))
        output_urls = set(output_df['url'].apply(normalize_url))

        # Find missing URLs (keeping original format)
        missing_urls = input_df[~input_df['url'].apply(normalize_url).isin(output_urls)]
        print(f"Number of missing URLs: {len(missing_urls)}")

        # Save missing URLs to new CSV file
        missing_urls.to_csv(missing_file, index=False)
        print(f"\nMissing URLs have been saved to {missing_file}")

        # Display first few missing URLs as a sample
        print("\nFirst 5 missing URLs (sample):")
        print(missing_urls['url'].head().to_string())

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # File paths
    input_file = "input_urls.csv"
    output_file = "output_results.csv"
    missing_file = "missing_urls_1812.csv"

    # Run the comparison
    compare_urls(input_file, output_file, missing_file)
