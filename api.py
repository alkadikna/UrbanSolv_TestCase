import json
import pandas as pd
from fastapi import FastAPI, Query
from pathlib import Path


DATA_PATH = "clean_data.csv"

app = FastAPI(
    title="UrbanSolv Business API",
    description=(
        "REST API untuk mengakses dataset bisnis Bakmi dan Ramen "
        "yang telah melalui proses data cleaning."
    ),
    version="1.0.0",
)

df = pd.read_csv(DATA_PATH)


def dataframe_to_records(dataframe: pd.DataFrame):
    return json.loads(
        dataframe.to_json(
            orient="records",
            force_ascii=False,
        )
    )


def contains_text(
    dataframe: pd.DataFrame,
    column: str,
    value: str,
):
    """
    Case-insensitive text search.
    """

    if column not in dataframe.columns:
        return pd.Series(
            False,
            index=dataframe.index,
        )

    return (
        dataframe[column]
        .fillna("")
        .astype(str)
        .str.contains(
            value,
            case=False,
            na=False,
            regex=False,
        )
    )


# root endpoint
@app.get("/")
def root():
    return {
        "message": "UrbanSolv Business API",
        "docs": "/docs",
        "endpoints": {
            "businesses": "/businesses",
            "search": "/businesses/search",
            "statistics": "/statistics",
        },
    }

# businesses endpoint
@app.get("/businesses")
def get_businesses():
    return dataframe_to_records(df)

# search businesses endpoint
@app.get("/businesses/search")
def search_businesses(
    keyword: str | None = Query(
        default=None,
        description="Cari bisnis berdasarkan keyword, nama, atau jenis bisnis",
        examples=["ramen"],
    ),

    kelurahan: str | None = Query(
        default=None,
        description="Filter berdasarkan kelurahan",
        examples=["Bulusan"],
    ),

    kecamatan: str | None = Query(
        default=None,
        description="Filter berdasarkan kecamatan",
        examples=["Tembalang"],
    ),

    rating: float | None = Query(
        default=None,
        ge=0,
        le=5,
        description="Filter berdasarkan rating (exact match)",
        examples=[4.5],
    ),

    min_rating: float | None = Query(
        default=None,
        ge=0,
        le=5,
        description="Minimum rating",
        examples=[4.0],
    ),

    max_rating: float | None = Query(
        default=None,
        ge=0,
        le=5,
        description="Maximum rating",
        examples=[5.0],
    ),
):
    result = df.copy()

    if keyword is not None:
        keyword_mask = pd.Series(
            False,
            index=result.index,
        )

        searchable_columns = [
            "keyword",
            "nama_tempat",
            "jenis_bisnis",
        ]

        for column in searchable_columns:
            if column in result.columns:
                keyword_mask |= contains_text(
                    result,
                    column,
                    keyword,
                )

        result = result[keyword_mask]


    # --------------------------------------------------------
    # Kelurahan
    # --------------------------------------------------------

    if kelurahan is not None:
        result = result[
            result["kelurahan"]
            .fillna("")
            .str.strip()
            .str.casefold()
            == kelurahan.strip().casefold()
        ]

    if kecamatan is not None:
        result = result[
            result["kecamatan"]
            .fillna("")
            .str.strip()
            .str.casefold()
            == kecamatan.strip().casefold()
        ]

    if rating is not None: #exact rating
        result = result[
            result["rating"].notna()
            & result["rating"].between(
                rating - 0.0001,
                rating + 0.0001,
            )
        ]

    if min_rating is not None:

        result = result[
            result["rating"].notna()
            & (result["rating"] >= min_rating)
        ]

    if max_rating is not None:

        result = result[
            result["rating"].notna()
            & (result["rating"] <= max_rating)
        ]

    return dataframe_to_records(result)

# statistics endpoint
@app.get("/statistics")
def get_statistics():

    total_business = len(df)
    average_rating = (
        round(float(df["rating"].mean()), 2)
        if "rating" in df.columns
        and df["rating"].notna().any()
        else None
    )
    total_reviews = (
        int(df["jumlah_review"].sum())
        if "jumlah_review" in df.columns
        else 0
    )

    bakmi_mask = pd.Series(
        False,
        index=df.index,
    )

    ramen_mask = pd.Series(
        False,
        index=df.index,
    )

    category_columns = [
        "keyword",
        "nama_tempat",
        "jenis_bisnis",
    ]

    for column in category_columns:

        if column not in df.columns:
            continue

        values = (
            df[column]
            .fillna("")
            .astype(str)
        )

        bakmi_mask |= values.str.contains(
            r"bakmi|bakmie",
            case=False,
            regex=True,
        )

        ramen_mask |= values.str.contains(
            "ramen",
            case=False,
            regex=False,
        )

    bakmie_count = int(bakmi_mask.sum())
    ramen_count = int(ramen_mask.sum())

    return {
        "total_business": total_business,
        "average_rating": average_rating,
        "total_reviews": total_reviews,
        "bakmie": bakmie_count,
        "ramen": ramen_count,
    }