
from flask import Flask

import requests
from bs4 import BeautifulSoup
import pandas as pd

from google.cloud import storage

BUCKET = "your-bucket-name"

def scrape():
    # Initialize a DataFrame to store the data.
    df = pd.DataFrame()

    # Send a GET request to the podcast page.
    result = requests.get("https://podcasts.apple.com/us/podcast/1014096501")
    scr = result.content

    # Parse the HTML content.
    soup = BeautifulSoup(scr, 'lxml')

    # Extract the data from the HTML.
    Podcast_Name = soup.find("span", {"class": "product-header__title"}).text.strip()
    Podcast_Producer = soup.find("span", {"class": "product-header__identity podcast-header__identity"}).text.strip()
    Podcast_Description = soup.find("section", {"class": "product-hero-desc__section"}).text.strip()

    Episode_Dates = [date.text.strip() for date in soup.find_all("li", {'class': "inline-list__item inline-list__item--margin-inline-start-large tracks__track__eyebrow-item"})]
    Episode_Titles = [title.text.strip() for title in soup.find_all("h2", {'class': 'tracks__track__headline spread'})]
    Episode_Summaries = [summary.text.strip() for summary in soup.find_all("div", {"class": "tracks__track__copy"})]
    Episode_URLs = [url["href"] for url in soup.find_all("a", {"class": "link tracks__track__link--block"})]

    # Add the data to the DataFrame.
    df['Podcast_Name'] = Podcast_Name
    df['Podcast_Producer'] = Podcast_Producer
    df['Podcast_Description'] = Podcast_Description
    df['Episode_Date'] = Episode_Dates
    df['Episode_Title'] = Episode_Titles
    df['Episode_Summary'] = Episode_Summaries
    df['Episode_URL'] = Episode_URLs

    return df

# Define a function to save a DataFrame to Google Cloud Storage as a CSV file.  
def save_df_to_gcs_as_csv(df, bucket_name, blob_name):
    """Saves a DataFrame to Google Cloud Storage as a CSV file.

    Args:
        df: The DataFrame to save.
        bucket_name: The name of the bucket to save the file to.
        blob_name: The name of the blob to save the file as.
    """

    # Create a client.
    storage_client = storage.Client()

    # Get the bucket.
    bucket = storage_client.bucket(bucket_name)

    # Convert the DataFrame to a CSV string.
    csv_string = df.to_csv()

    # Upload the CSV string to GCS.
    bucket.blob(blob_name).upload_from_string(csv_string)

    # Print a success message.
    print(f"Saved {blob_name} to {bucket_name}.")
    

# Initialize the Flask app
app = Flask(__name__)

@app.route('/')
def index():
    # Scrape the data
    df = scrape()

    # Save the data to GCS
    save_df_to_gcs_as_csv(df, BUCKET, 'test.csv')

    return 'Data scraped and saved to GCS.'

if __name__ == '__main__':
  app.run()