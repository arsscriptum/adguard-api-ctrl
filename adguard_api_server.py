#!/usr/bin/env python3
from dotenv import load_dotenv
import os
import json
from flask import Flask, render_template, jsonify
import requests
from requests.auth import HTTPBasicAuth

app = Flask(__name__)

app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

load_dotenv()

ADGUARD_USER = os.getenv("ADGUARD_USER")
ADGUARD_PASS = os.getenv("ADGUARD_PASS")
ADGUARD_URL = os.getenv("ADGUARD_URL")


def adguard_get(endpoint):
    url = f"{ADGUARD_URL}{endpoint}"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(ADGUARD_USER, ADGUARD_PASS), timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}
    except ValueError:
        return {"error": "Response is not JSON."}


def adguard_post(endpoint, payload):
    url = f"{ADGUARD_URL}{endpoint}"
    response = requests.post(url, json=payload, auth=HTTPBasicAuth(ADGUARD_USER, ADGUARD_PASS))
    try:
        return response.json()
    except ValueError:
        return {"result": response.text}


def delete_rewrite(domain, answer):
    """
    Deletes a DNS rewrite entry in AdGuard Home.
    
    Args:
        domain (str): Domain pattern to delete.
        
    Returns:
        dict: JSON response or plain text.
    """

    url = f"{ADGUARD_URL}/control/rewrite/delete"
    payload = {
        "domain": domain,
        "answer": answer
    }
    try:
        response = requests.post(
            url,
            json=payload,
            auth=HTTPBasicAuth(ADGUARD_USER, ADGUARD_PASS),
            timeout=10
        )
        try:
            return response.json()
        except ValueError:
            return {"result": response.text}
    except requests.RequestException as e:
        return {"error": str(e)}


def add_rewrite(domain, answer):
    """
    Adds a DNS rewrite entry to AdGuard Home.
    
    Args:
        domain (str): Domain pattern to rewrite (e.g. '*.desjardins.ca')
        answer (str): IP address to respond with (e.g. '10.0.0.111')
        
    Returns:
        dict: JSON response or plain text from AdGuard Home.
    """

    url = f"{ADGUARD_URL}/control/rewrite/add"
    payload = {
        "domain": domain,
        "answer": answer
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            auth=HTTPBasicAuth(ADGUARD_USER, ADGUARD_PASS),
            timeout=10
        )
        # Attempt to parse JSON; fallback to text
        try:
            return response.json()
        except ValueError:
            return {"result": response.text}
    except requests.RequestException as e:
        return {"error": str(e)}


def load_presets():
    """
    Loads presets from presets.json file.
    Returns:
        dict: domain → answer mappings
    Raises:
        RuntimeError: if file missing or invalid
    """
    try:
        with open("/home/gp/adguard-api-ctrl/presets.json", "r") as f:
            presets = json.load(f)

        if not isinstance(presets, dict):
            raise RuntimeError("presets.json is not a JSON object.")

        return presets
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to load presets.json: {str(e)}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/list", methods=["POST"])
def list_rewrites():
    data = adguard_get("/control/rewrite/list")
    return jsonify(data)

@app.route("/api/delete_all", methods=["POST"])
def delete_all_rewrites():
    data = adguard_get("/control/rewrite/list")
    count = len(data) if data else 0

    if count == 0:
        print("No rewrites found.")
        return jsonify({"message": "No rewrites found."})

    print(f"Found {count} rewrites. Deleting them now...\n")

    results = []
    for entry in data:
        domain = entry.get("domain", "")
        answer = entry.get("answer", "")
        result = delete_rewrite(domain, answer)
        print(f"Deleted: {domain} → {answer} | API result: {result}")
        results.append({
            "domain": domain,
            "answer": answer,
            "result": result
        })

    return jsonify({
        "message": f"Deleted {count} rewrites.",
        "details": results
    })


@app.route("/api/add_presets", methods=["POST"])
def add_presets():
    try:
        presets = load_presets()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    results = []
    for domain, answer in presets.items():
        result = add_rewrite(domain, answer)
        app.logger.info(f"Adding Redirect: {domain} → {answer} | API result: {result}")
        results.append({
            "domain": domain,
            "answer": answer,
            "result": result
        })

    return jsonify({
        "message": f"Preset rewrites added: {len(results)} entries.",
        "details": results
    })



@app.route("/api/run_tests", methods=["POST"])
def run_tests():
    try:
        presets = load_presets()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    count = len(presets) if presets else 0

    if count == 0:
        app.logger.info("No presets found.")
        return jsonify({"message": "No presets found."})

    app.logger.info(f"Found {count} presets. Testing...")

    results = []
    for domain, answer in presets.items():
        result = add_rewrite(domain, answer)
        app.logger.info(f"Tested preset: {domain} → {answer} | API result: {result}")
        results.append({
            "domain": domain,
            "answer": answer,
            "result": result
        })

    return jsonify({
        "message": f"Tested {count} presets.",
        "details": results
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
