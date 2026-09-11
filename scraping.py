import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

URL = "https://places.googleapis.com/v1/places:searchText"

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.primaryType",
    "places.primaryTypeDisplayName",
    "places.rating",
    "places.userRatingCount",
    "places.regularOpeningHours",
    "places.priceLevel",
    "places.priceRange",
    "places.location",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "nextPageToken",
])

HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": FIELD_MASK,
}


def search_places(keyword):
    results = []
    page_token = None

    while True:
        payload = {
            "textQuery": f"{keyword} Kecamatan Tembalang Semarang",
            "pageSize": 20,
            "languageCode": "id",
        }

        if page_token:
            payload["pageToken"] = page_token

        response = requests.post(
            URL,
            headers=HEADERS,
            json=payload
        )
        # print("STATUS:", response.status_code)
        # print("BODY:", response.text)


        response.raise_for_status()
        data = response.json()

        results.extend(data.get("places", []))

        page_token = data.get("nextPageToken")

        if not page_token:
            break

    return results

    
places = []

for keyword in ["bakmi", "ramen"]:
    results = search_places(keyword)

    for p in results:
        places.append({
            "Place ID": p.get("id"),
            "Nama Tempat":
                p.get("displayName", {}).get("text"),

            "Alamat":
                p.get("formattedAddress"),

            "Jenis Bisnis":
                p.get(
                    "primaryTypeDisplayName", {}
                ).get("text"),

            "Rating":
                p.get("rating"),

            "Jumlah Review":
                p.get("userRatingCount"),

            "Jam Operasional":
                " | ".join(
                    p.get(
                        "regularOpeningHours", {}
                    ).get("weekdayDescriptions", [])
                ),

            # "Harga":
                # p.get("priceLevel"),

            "Harga Start": (
                int(p.get("priceRange", {})
                    .get("startPrice", {})
                    .get("units"))
                if p.get("priceRange", {})
                    .get("startPrice", {})
                    .get("units") is not None
                else None
            ),

            "Harga End": (
                int(p.get("priceRange", {})
                    .get("endPrice", {})
                    .get("units"))
                if p.get("priceRange", {})
                    .get("endPrice", {})
                    .get("units") is not None
                else None
            ),


            "Latitude":
                p.get(
                    "location", {}
                ).get("latitude"),

            "Longitude":
                p.get(
                    "location", {}
                ).get("longitude"),

            "Telepon":
                p.get("nationalPhoneNumber"),

            "Website":
                p.get("websiteUri"),

            "Keyword":
                keyword
        })


df = pd.DataFrame(places)

# buang duplikat antara hasil "bakmi" dan "ramen"
df = df.drop_duplicates(
    subset=["Place ID"]
)

df.to_csv(
    "raw_data.csv",
    index=False
)

print(df)