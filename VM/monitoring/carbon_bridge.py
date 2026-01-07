import time
import os
import threading
import subprocess
import requests
import json
from flask import Flask, request, render_template_string, redirect, url_for, Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from dotenv import load_dotenv

# Load .env file into environment
load_dotenv(dotenv_path="../docker")

# --- Configuration ---
TOKEN = os.getenv('ELECTRICITYMAP_TOKEN', 'cwrhbEPCxzpCCz83tPBK')
_zones_env = os.getenv('ELECTRICITYMAP_ZONES', 'AT,TR,SK,US-CENT-SWPP')
ZONES = [z.strip() for z in _zones_env.split(',') if z.strip()] if _zones_env else ['AT']

REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT_SECONDS', '10'))
FETCH_INTERVAL_SECONDS = int(os.getenv('FETCH_INTERVAL_SECONDS', '3600'))
PORT = int(os.getenv('EXPORTER_PORT', '9091'))

CURRENT_ZONE = os.getenv('CURRENT_ZONE', 'AT')
MAX_CI = float(os.getenv('MAX_CI')) if os.getenv('MAX_CI') else 200
CHOOSER_COOLDOWN_SECONDS = int(os.getenv('CHOOSER_COOLDOWN_SECONDS', 0))
CHOOSER_PATH = os.getenv('CHOOSER_PATH', 'monitoring/choose_green_region.py')

# --- Global State ---
# Stores the latest known data for display: { 'AT': {'value': 230, 'source': 'API', 'ts': 12345} }
zone_state = {z: {'value': 0.0, 'source': 'Init', 'ts': 0} for z in ZONES}
# Stores manual overrides: { 'AT': 500.0 }
overrides = {}
_last_trigger_ts = 0

# --- Prometheus Metrics ---
CARBON_INTENSITY = Gauge('carbon_intensity_gCo2perkWh', 'Current carbon intensity (gCO2eq/kWh)', ['zone'])

app = Flask(__name__)

# --- Core Logic ---

def run_region_chooser():
    global _last_trigger_ts, CURRENT_ZONE
    now = time.time()
    if now - _last_trigger_ts < CHOOSER_COOLDOWN_SECONDS:
        print(f"[bridge] Cooldown active. Skipping chooser.")
        return

    print(f"[bridge] Threshold exceeded; invoking chooser: {CHOOSER_PATH}")
    try:
        # Run the script
        result = subprocess.run(
            ["python3", CHOOSER_PATH, "--format", "json"],
            stdout=subprocess.PIPE, text=True
        )
        
        # 1. Try to parse JSON output regardless of success/failure
        try:
            data = json.loads(result.stdout)
            best_zone = data.get("best", {}).get("zone") if data.get("best") else None
            best_region = data.get("best", {}).get("region") if data.get("best") else None
            best_ci = data.get("best", {}).get("ci") if data.get("best") else None
            
            # Print the decision summary for debugging
            print(f"[chooser] Analysis complete. Best zone found: {best_zone}")
            
            # 2. Act on the decision
            if best_zone and best_zone != CURRENT_ZONE:
                print("\nRecommended deployment:")
                print(f"🚩 Zone:    {best_zone}")
                print(f"🌍 Region:  {best_region}")
                print(f"🌳 C-Index: {best_ci}\n")
                print(f"[bridge] 🚨 MIGRATION! Switching Active Zone: {CURRENT_ZONE} -> {best_zone}")
                CURRENT_ZONE = best_zone
                
                # OPTIONAL: Save to file for persistence
                with open("current_zone.txt", "w") as f:
                    f.write(best_zone)
            elif best_zone == CURRENT_ZONE:
                print(f"[bridge] Current zone {CURRENT_ZONE} is already the best option.")
            else:
                print(f"[bridge] No suitable green zone found (All zones > MAX_CI or Data Missing).")

        except json.JSONDecodeError:
            # If JSON parsing fails, it was a real crash (traceback in stderr/stdout)
            print(f"[bridge] Chooser crashed/invalid output.")
            if result.stdout.strip():
                print(f"[chooser] stdout: {result.stdout.strip()}")
            if result.stderr.strip():
                print(f"[chooser] stderr: {result.stderr.strip()}")

        _last_trigger_ts = now
        
    except Exception as e:
        print(f"[bridge] Failed to run chooser: {e}")

def update_zone(zone):
    """Updates a single zone based on override OR API."""
    # 1. Check for Manual Override
    if zone in overrides:
        val = overrides[zone]
        CARBON_INTENSITY.labels(zone=zone).set(val)
        zone_state[zone] = {'value': val, 'source': 'Manual Override', 'ts': time.time()}
        return val

    # 2. Fetch from API
    url = f"https://api.electricitymaps.com/v3/carbon-intensity/latest?zone={zone}"
    headers = {"auth-token": TOKEN}
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.ok:
            data = resp.json()
            val = float(data.get('carbonIntensity', 0.0))
            CARBON_INTENSITY.labels(zone=zone).set(val)
            zone_state[zone] = {'value': val, 'source': 'API', 'ts': time.time()}
            return val
        else:
            print(f"Failed to fetch {zone}: {resp.status_code}")
    except Exception as e:
        print(f"Error fetching {zone}: {e}")
    return None

def background_loop():
    """Background thread to update data and check thresholds."""
    print(f"[bridge] Background loop started. Interval: {FETCH_INTERVAL_SECONDS}s")
    while True:
        for zone in ZONES:
            ci = update_zone(zone)
            
            # Trigger Logic
            if zone == CURRENT_ZONE and ci is not None:
                if ci > MAX_CI:
                    print(f"[bridge] {zone} CI {ci} > {MAX_CI}. Triggering...")
                    run_region_chooser()
        
        time.sleep(FETCH_INTERVAL_SECONDS)

# --- Flask Web Interface ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Green Cloud Control</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background: #f4f4f4; }
        .dirty { color: #d32f2f; font-weight: bold; }
        .clean { color: #388e3c; font-weight: bold; }
        .btn { padding: 5px 10px; cursor: pointer; }
        .manual { background: #fff3e0; }
    </style>
</head>
<body>
    <h1>🌍 Carbon Bridge Control</h1>
    <p><strong>Current Deployment Zone:</strong> {{ current_zone }} (Max Threshold: {{ max_ci }})</p>
    
    <table>
        <thead>
            <tr>
                <th>Zone</th>
                <th>Intensity (gCO2/kWh)</th>
                <th>Source</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
            {% for zone, data in states.items() %}
            <tr class="{{ 'manual' if data.source == 'Manual Override' else '' }}">
                <td>
                    {{ zone }}
                    {% if zone == current_zone %} 👈 <b>ACTIVE</b>{% endif %}
                </td>
                <td class="{{ 'dirty' if data.value > max_ci else 'clean' }}">
                    {{ data.value }}
                </td>
                <td>{{ data.source }}</td>
                <td>
                    <form action="/override" method="POST" style="display:inline-flex; gap:5px;">
                        <input type="hidden" name="zone" value="{{ zone }}">
                        {% if zone in overrides %}
                            <button type="submit" name="action" value="clear" class="btn">Rest to API</button>
                        {% else %}
                            <input type="number" name="value" placeholder="100" style="width: 60px;" required>
                            <button type="submit" name="action" value="set" class="btn">Set</button>
                        {% endif %}
                    </form>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <p><small>Changes take effect immediately. Metrics exposed at <a href="/metrics">/metrics</a>.</small></p>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(
        HTML_TEMPLATE, 
        states=zone_state, 
        overrides=overrides, 
        current_zone=CURRENT_ZONE,
        max_ci=MAX_CI
    )

@app.route('/override', methods=['POST'])
def override():
    zone = request.form.get('zone')
    action = request.form.get('action')
    
    if zone:
        if action == 'clear' and zone in overrides:
            del overrides[zone]
            
            # --- FIX STARTS HERE ---
            # Define a small wrapper to update AND check the threshold
            def reset_and_check(z):
                # 1. Fetch real value from API
                val = update_zone(z)
                # 2. Check trigger immediately
                if z == CURRENT_ZONE and val is not None and val > MAX_CI:
                    print(f"[bridge] API restored for {z}. Value {val} > {MAX_CI}. Triggering...")
                    run_region_chooser()

            # Run this in a thread so the web page reloads instantly
            threading.Thread(target=reset_and_check, args=(zone,)).start()
            # --- FIX ENDS HERE ---

        elif action == 'set':
            try:
                val = float(request.form.get('value'))
                overrides[zone] = val
                # Immediately apply override
                update_zone(zone)
                
                # Check trigger immediately if it's the current zone
                if zone == CURRENT_ZONE and val > MAX_CI:
                    threading.Thread(target=run_region_chooser).start()
            except ValueError:
                pass
                
    return redirect(url_for('index'))

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    # Start the background data fetcher
    t = threading.Thread(target=background_loop, daemon=True)
    t.start()
    
    # Run Flask (blocks main thread)
    print(f"[bridge] Starting Web UI on port {PORT}")
    app.run(host='0.0.0.0', port=PORT)