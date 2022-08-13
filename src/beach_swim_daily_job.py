
# Auto-retrieve daily beach data (Prefect) - non-mapped
#
# Automated daily job (in Prefect) that runs just after 7:30AM Sydney time when the pages are updated each day.

# Migration to Prefect 2.0.x
# See https://docs.prefect.io/migration-guide/

import contextlib
from datetime import timedelta

import httpx
import pandas as pd
import pendulum
import requests
from bs4 import BeautifulSoup
from prefect import task, flow
#from prefect.deployments import DeploymentSpec
from prefect.orion.schemas.schedules import IntervalSchedule, RRuleSchedule
from sqlite_utils import Database

from scaleway_s3_storage import connect_to_s3, dataframe_to_csv_s3


BEACHMAPP_BASE_URL = "https://www.environment.nsw.gov.au/beachmapp"

BEACHWATCH_FIELDS = {
    "navbar-title-text": "Beach name",
    "beach-timelapse-panel": "Data last updated",
    "bw-status-text": "Pollution status",
    "bw-air-temp-value": "Maximum forecast air temperature",
    "bw-ocean-temp-value": "Water temperature",
    "bw-weather-text": "Weather forecast",
    "bw-swell": "Swell",
    "bw-wind": "Wind",
    "bw-patrol-info": "Patrol info",
    "bw-rainfall": "Rainfall",
    "bw-high-tide": "High tide",
    "bw-low-tide": "Low tide",
    "bw-alert-text": "Alert"
}

#@task
def retrieve_url(url):
    r = httpx.get(url)
    r.raise_for_status()
    return r.text


# Define various helper functions to parse the html pages to extract the data for each beach

def get_beachwatch_data_for_class(beach_soup, classname, item_name):
    """
    Given the parsed html from BeautifulSoup for a particular page, 
    search for a specific class name within either a 'div' or 'span' block.
    item_name is the user-friendly name that we have chosen for each class name
    """
    if classname == "bw-alert-text":
        item = beach_soup.find_all("div", {"class": classname})
        return ([x.contents[0] for x in item], item_name)
    else:
        item = beach_soup.find("div", {"class": classname})
        if item is None:
            item = beach_soup.find("span", {"class": classname})
    return (item.contents[0], item_name)



def get_all_data_for_beach(beach_soup, beachwatch_fields):
    beach_data = []
    for classname in beachwatch_fields:
        try:
            item, item_name = get_beachwatch_data_for_class(beach_soup, classname, beachwatch_fields[classname])
        except Exception:
            item = classname
            item_name = beachwatch_fields[classname]
        beach_data.append((item, item_name))
    return beach_data



def scrape_beach_daily_data(beachmapp_html, beachwatch_fields):
    """
    Given a string of html representing a Beachmapp page,
    returns the daily data for that beach
    """

    beach_soup = BeautifulSoup(beachmapp_html, "html.parser")

    return get_all_data_for_beach(beach_soup, beachwatch_fields)


#@task
def create_beach_list(base_url, main_html, url_path, bypass):
    """
    Given the main page html, creates a list of the beach URLs from 
    this page which will be subsequently passed to scrape_beach_daily_data
    """

    if bypass:
        return [base_url]

    main_page = BeautifulSoup(main_html, "html.parser")

    return [
        base_url.replace("/beachmapp", "") + link.get("href")
        for link in main_page.find_all("a")
        if url_path in link.get("href")
    ]


def write_daily_beach_data_local(all_beach_daily_data_df, write_local=False):
    if write_local is True:
        data_filename = "data/all_beach_daily_data_"
        data_parquet = data_filename.replace("data_", "data.parquet")
        data_xlsx = data_filename + pendulum.now().isoformat() + ".xlsx"
        data_csv = data_xlsx.replace(".xlsx", ".csv")
        print(f'Created: {data_csv}')
        #with contextlib.suppress(Exception):
            #all_beach_daily_data_df.to_parquet(data_parquet)
        all_beach_daily_data_df.to_excel(data_xlsx, index=False)
            #all_beach_daily_data_df.to_csv(data_csv, index=False)
        db = Database("data/daily_beach_data_db.sqlite")
        all_beach_daily_data_df.to_sql("beaches", con=db.conn, if_exists="append")
    else:
        bucket_name = "databooth-beach-swim"
        data_filename = "all_beach_daily_data.csv"
        s3 = connect_to_s3()
        dataframe_to_csv_s3(s3, all_beach_daily_data_df, bucket_name, data_filename)
        print(f'Wrote data to s3://{bucket_name}/{data_filename}')

        db = Database("data/daily_beach_data_db.sqlite")
        all_beach_daily_data_df.to_sql("beaches", con=db.conn, if_exists="append")
        print("Also wrote local SQLite DB: data/daily_beach_data_db.sqlite")


#@flow
def create_all_beaches_list(base_url, bypass):
    base_html = retrieve_url(base_url)
    region_URLs = create_beach_list(
        base_url, base_html, "beachmapp/Beaches", bypass)
    all_beaches = []
    for region_url in region_URLs:
        region = region_url.split("/")[-1]
        region_html = retrieve_url(region_url)
        beaches_list = create_beach_list(
            base_url, region_html, "/beachmapp/Beach", bypass)
        all_beaches.append([region, beaches_list])
    return [[region, item] for region, sublist in all_beaches for item in sublist]



#@flow
def get_daily_beach_data(beachwatch_fields, beaches_url_list, write_local):
    COLUMN_NAMES = ["Retrieved at"] + ["Region"] + \
        list(beachwatch_fields.values())
    all_beach_daily_data_df = pd.DataFrame(columns=COLUMN_NAMES)

    for region, beach_url in beaches_url_list:
        beachmapp_html = retrieve_url(beach_url)
        beach_data = scrape_beach_daily_data(beachmapp_html, beachwatch_fields)
        scraped_time = pendulum.now().isoformat()
        all_beach_daily_data_df.loc[len(all_beach_daily_data_df)] = [
            scraped_time] + [region] + [value for (value, _) in beach_data]

    all_beach_daily_data_df["Alert"] = all_beach_daily_data_df["Alert"].apply(
        lambda alist: " ".join(alist))

    write_daily_beach_data_local(all_beach_daily_data_df, write_local)

    return all_beach_daily_data_df

# TODO: Could cache list of beaches (as generally not changing) and re-use

# Define Prefect job - schedule, executor and Flow of tasks

# DeploymentSpec(
#     flow_location="/Developer/workflows/my_flow.py",
#     name="my-first-deployment",
#     parameters={"nums": [1, 2, 3, 4]}, 
#     schedule=IntervalSchedule(interval=timedelta(minutes=15)),
# )


#@flow(name="daily-beach-data-job")
def beach_data_daily_job():
    WRITE_LOCAL_FILE = True
    beaches_url_list = create_all_beaches_list(BEACHMAPP_BASE_URL, False)
    return get_daily_beach_data(BEACHWATCH_FIELDS, beaches_url_list, WRITE_LOCAL_FILE)


beach_data_daily_job()

# schedule = IntervalSchedule(anchor_date=pendulum.datetime(2022, 2, 26, 7, 40, 0, tz="Australia/Sydney"))
# schedule.get_dates(n=10)

# TODO: Check that the data has actually been updated "NN minutes ago" from the "Data last updated" field
