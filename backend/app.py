from flask import Flask, request, jsonify, render_template, session
import requests

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "supersecretkey"  # ganti dengan kunci rahasia yg kuat

@app.route("/")
def index():
    # Menampilkan halaman index.html
    return render_template("index.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    query = ""
    category = ""

    # Ambil data dari JSON jika ada
    if request.is_json:
        data = request.get_json(silent=True) or {}
        query = (data.get("query") or "").strip()
        category = (data.get("category") or "").strip()
    else:
        # Ambil dari form / query string
        query = (request.values.get("query") or "").strip()
        category = (request.values.get("category") or "").strip()

    # Validasi input
    if not query:
        return jsonify({"error": "No query provided"}), 400

    # Gabungkan query dan kategori
    full_query = f"{query} {category}" if category else query

    # Gunakan Nominatim (OpenStreetMap) API
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": full_query, "format": "json", "limit": 10}
    headers = {"User-Agent": "LLM-Maps-Test-App"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return jsonify({"error": "Failed to fetch data", "details": str(e)}), 500

    if not data:
        return jsonify({"error": "Location not found"}), 404

    # Simpan riwayat pencarian di session
    history = session.get("history", [])
    history.append({"query": query, "category": category})
    session["history"] = history[-10:]  # simpan max 10 riwayat terakhir

    # Filter hasil kalau kategori dipilih
    results = []
    for item in data:
        name = item.get("display_name", "").lower()
        if category:
            if category.lower() in name:
                results.append({
                    "lat": item["lat"],
                    "lon": item["lon"],
                    "display_name": item["display_name"]
                })
        else:
            results.append({
                "lat": item["lat"],
                "lon": item["lon"],
                "display_name": item["display_name"]
            })

    if not results:
        return jsonify({"error": "No results match the category"}), 404

    return jsonify(results[:5])  # batasi 5 hasil

@app.route("/history", methods=["GET"])
def history():
    return jsonify(session.get("history", []))

if __name__ == "__main__":
    app.run(debug=True)
