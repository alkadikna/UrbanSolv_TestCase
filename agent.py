import os
import json
import requests
from dotenv import load_dotenv
from groq import Groq


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_BASE_URL = "http://127.0.0.1:8000"
MODEL = "openai/gpt-oss-120b"

client = Groq(
    api_key=GROQ_API_KEY
)


def api_get(endpoint, params=None):
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            params=params,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:
        return {
            "error": f"Gagal mengakses API: {str(e)}"
        }

# tools to call search businesses from API
def search_businesses(
    keyword=None,
    kelurahan=None,
    kecamatan=None,
    rating=None,
    min_rating=None,
    max_rating=None,
):

    params = {}

    if keyword is not None:
        params["keyword"] = keyword

    if kelurahan is not None:
        params["kelurahan"] = kelurahan

    if kecamatan is not None:
        params["kecamatan"] = kecamatan

    if rating is not None:
        params["rating"] = rating

    if min_rating is not None:
        params["min_rating"] = min_rating

    if max_rating is not None:
        params["max_rating"] = max_rating

    return api_get(
        "/businesses/search",
        params=params
    )

# tools to call get statistics from API
def get_statistics():
    """
    Mendapatkan summary dataset.
    """

    return api_get("/statistics")

# tools to call get top reviewed from API
def get_top_reviewed(
    limit=1,
    keyword=None,
    kelurahan=None,
    kecamatan=None,
):
    if keyword or kelurahan or kecamatan:

        businesses = search_businesses(
            keyword=keyword,
            kelurahan=kelurahan,
            kecamatan=kecamatan
        )

    else:

        businesses = api_get("/businesses")

    if isinstance(businesses, dict) and "error" in businesses:
        return businesses

    if not businesses:
        return []

    sorted_businesses = sorted(
        businesses,
        key=lambda x: x.get("jumlah_review", 0),
        reverse=True
    )

    return sorted_businesses[:limit]

# tools to call find businesses closing at from API
def find_businesses_closing_at(
    hour,
    keyword=None,
    kelurahan=None,
    kecamatan=None,
):

    businesses = search_businesses(
        keyword=keyword,
        kelurahan=kelurahan,
        kecamatan=kecamatan
    )

    if isinstance(businesses, dict) and "error" in businesses:
        return businesses

    # Normalize 
    normalized_hour = (
        hour
        .strip()
        .replace(".", ":")
    )

    try:
        hh, mm = normalized_hour.split(":")

        target_colon = f"{int(hh):02d}:{int(mm):02d}"
        target_dot = f"{int(hh):02d}.{int(mm):02d}"

    except ValueError:
        return {
            "error": (
                "Format jam tidak valid."
            )
        }

    results = []

    for business in businesses:

        opening_hours = business.get(
            "jam_operasional"
        )

        if not opening_hours:
            continue

        text = str(opening_hours)

        if (
            target_colon in text
            or target_dot in text
        ):
            results.append(business)

    return results



# making tools schema for Groq 
TOOLS = [

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "search_businesses",

            "description": (
                "Search dan filter business berdasarkan "
                "keyword, kelurahan, kecamatan, atau rating. "
                "Gunakan tool ini untuk pertanyaan seperti "
                "'cari ramen rating di atas 4.7' atau "
                "'berapa ramen di Bulusan'."
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "keyword": {
                        "type": "string",
                        "description": (
                            "Kategori atau keyword bisnis, "
                            "contoh: ramen atau bakmi"
                        )
                    },

                    "kelurahan": {
                        "type": "string",
                        "description": (
                            "Nama kelurahan, contoh: Bulusan"
                        )
                    },

                    "kecamatan": {
                        "type": "string",
                        "description": (
                            "Nama kecamatan, contoh: Tembalang"
                        )
                    },

                    "rating": {
                        "type": "number",
                        "description": "Exact rating"
                    },

                    "min_rating": {
                        "type": "number",
                        "description": "Minimum rating"
                    },

                    "max_rating": {
                        "type": "number",
                        "description": "Maximum rating"
                    }
                },

                "additionalProperties": False
            }
        }
    },


    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "get_statistics",

            "description": (
                "Mendapatkan statistik keseluruhan dataset "
                "seperti total bisnis, rata-rata rating, "
                "total review, jumlah bakmi dan ramen."
            ),

            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },


    # --------------------------------------------------------
    # Top reviewed
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "get_top_reviewed",

            "description": (
                "Cari restoran atau bisnis dengan jumlah "
                "review paling banyak. Bisa difilter berdasarkan "
                "keyword, kelurahan, atau kecamatan."
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "limit": {
                        "type": "integer",
                        "description": (
                            "Jumlah bisnis yang ingin ditampilkan"
                        ),
                        "default": 1
                    },

                    "keyword": {
                        "type": "string",
                        "description": (
                            "Contoh ramen atau bakmi"
                        )
                    },

                    "kelurahan": {
                        "type": "string"
                    },

                    "kecamatan": {
                        "type": "string"
                    }
                },

                "additionalProperties": False
            }
        }
    },


    # --------------------------------------------------------
    # Closing time
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "find_businesses_closing_at",

            "description": (
                "Cari bisnis berdasarkan jam tutup. "
                "Gunakan untuk pertanyaan seperti "
                "'Bakmi mana yang buka sampai jam 22.00?'"
            ),

            "parameters": {
                "type": "object",

                "properties": {

                    "hour": {
                        "type": "string",
                        "description": (
                            "Jam tutup format HH:MM. "
                            "Contoh 22:00"
                        )
                    },

                    "keyword": {
                        "type": "string",
                        "description": (
                            "Kategori bisnis seperti bakmi "
                            "atau ramen"
                        )
                    },

                    "kelurahan": {
                        "type": "string"
                    },

                    "kecamatan": {
                        "type": "string"
                    }
                },

                "required": ["hour"],

                "additionalProperties": False
            }
        }
    }
]


AVAILABLE_FUNCTIONS = {
    "search_businesses": search_businesses,
    "get_statistics": get_statistics,
    "get_top_reviewed": get_top_reviewed,
    "find_businesses_closing_at":
        find_businesses_closing_at,
}

# executor
def execute_tool(tool_call):

    function_name = tool_call.function.name

    arguments = json.loads(
        tool_call.function.arguments
    )

    function = AVAILABLE_FUNCTIONS.get(
        function_name
    )

    if function is None:
        return {
            "error":
                f"Unknown function: {function_name}"
        }

    return function(**arguments)



# prompting
SYSTEM_PROMPT = """
Kamu adalah UrbanSolv Business Agent.

Tugasmu adalah menjawab pertanyaan tentang dataset bisnis
Bakmi dan Ramen.

ATURAN PENTING:

1. Gunakan tools yang tersedia untuk menjawab pertanyaan
   yang membutuhkan informasi dari dataset.

2. Jangan mengarang nama restoran, rating, jumlah review,
   lokasi, harga, atau jam operasional.

3. Dataset/API adalah sumber utama dan sumber kebenaran.

4. Jika data tidak tersedia, katakan bahwa data tersebut
   tidak tersedia.

5. Jika hasil pencarian kosong, katakan bahwa tidak ditemukan
   bisnis yang sesuai.

6. Jika user meminta jumlah bisnis, hitung berdasarkan hasil
   tool yang dikembalikan.

7. Jawab dengan ringkas dan jelas dalam Bahasa Indonesia.

8. Untuk daftar bisnis, tampilkan nama tempat terlebih dahulu
   kemudian informasi relevan seperti rating atau jumlah review.

9. Jangan mengatakan bahwa suatu restoran tutup hanya karena
   data jam operasional tidak tersedia.

10.Jika ada n results, tampilkan tepat n bisnis, dimana n adalah jumlah hasil pencarian yang dikembalikan oleh api.
"""

# agent 
def ask_agent(question):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": question
        }
    ]


    # Maksimal 5 agent iterations
    for _ in range(5):

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0
        )


        response_message = (
            response
            .choices[0]
            .message
        )


        # Kalau tidak butuh tool lagi,
        # berarti model sudah punya final answer
        if not response_message.tool_calls:
            return response_message.content


        # Masukkan tool call dari assistant
        messages.append(response_message)


        # Bisa ada lebih dari satu tool call
        for tool_call in response_message.tool_calls:

            result = execute_tool(
                tool_call
            )


            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": json.dumps(
                    result,
                    ensure_ascii=False
                )
            })


    return (
        "Agent mencapai batas maksimum proses "
        "sebelum mendapatkan jawaban."
    )


# cli
if __name__ == "__main__":

    print("=" * 50)
    print("UrbanSolv Business AI Agent")
    print("=" * 50)
    print("Ketik 'exit' untuk keluar.\n")


    while True:

        question = input("User: ").strip()


        if question.lower() in {
            "exit",
            "quit",
            "keluar"
        }:
            print("Agent: Sampai jumpa.")
            break


        if not question:
            continue


        try:

            answer = ask_agent(question)

            print(
                f"\nAgent: {answer}\n"
            )


        except Exception as e:

            print(
                f"\nError: {e}\n"
            )