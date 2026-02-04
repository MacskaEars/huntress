import pandas as pd
from jobspy import scrape_jobs
import time
import re
import os

try:
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "--upgrade", "pip"
    ])
    
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "requests", "pandas", "numpy", "bs4"
    ])
    import requests
except Exception as e:
    print(f"There was an exception installing requirements: {str(e)}")
    return

def extract_contact_info(description):
    """Extract emails and phone numbers from job description."""
    if not description or not isinstance(description, str):
        return "No direct contact found"
    
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', description)
    phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', description)
    
    contacts = []
    if emails:
        contacts.extend(list(set(emails)))
    if phones:
        contacts.extend(list(set(phones)))
    
    return ", ".join(contacts) if contacts else "No direct contact found"

def run_job_search(args):
    print("\n" + "="*60)
    print("HUNTRESS JOB SEARCH ENGINE")
    print("="*60)

    search_terms = args.term if args.term else ["Software Engineer"]
    locations = []
    country_ahead = "USA"

    if getattr(args, 'global', False):
        locations = ["Worldwide"]
        country_ahead = None
    elif args.country:
        locations = args.country
        country_ahead = args.country[0]
    elif args.state:
        locations = args.state
        country_ahead = "USA"
    elif args.zip:
        locations = args.zip
        country_ahead = "USA"
    else:
        locations = ["USA"]
        country_ahead = "USA"

    all_jobs = []
    for term in search_terms:
        for loc in locations:
            print(f"\nScanning Location: {loc}")
            print(f"  Searching: {term}...", end="", flush=True)
            try:
                is_remote_param = None
                if args.remote:
                    is_remote_param = True
                elif args.local:
                    is_remote_param = False

                jobs = scrape_jobs(
                    site_name=["indeed", "linkedin"],
                    search_term=term,
                    location=loc,
                    results_wanted=10, 
                    hours_old=72,
                    country_ahead=country_ahead,
                    is_remote=is_remote_param,
                    description_format="markdown"
                )
                
                if not jobs.empty:
                    jobs["contact_info"] = jobs["description"].apply(extract_contact_info)
                    jobs["search_origin"] = f"{term} | {loc}"
                    all_jobs.append(jobs)
                    print(f" Found {len(jobs)}")
                else:
                    print(" 0")
                
                time.sleep(2) 
            except Exception as e:
                print(f" Error during job search: {e}")

    if all_jobs:
        df = pd.concat(all_jobs, ignore_index=True)
        df = df.drop_duplicates(subset=["job_url", "title", "company"])
        
        if args.remote and "is_remote" in df.columns:
            df = df[df["is_remote"] == True]
        elif args.local and "is_remote" in df.columns:
            df = df[df["is_remote"] == False]

        return df
    return None
