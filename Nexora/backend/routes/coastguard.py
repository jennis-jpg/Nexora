from fastapi import APIRouter, HTTPException, Header
from typing import Optional, Dict, List
import os

router = APIRouter(prefix="/coastguard", tags=["coastguard"])

# ---------------------------------------------------------
# DOCK CREDENTIALS & METADATA (INCLUDES NEW LOCATIONS)
# ---------------------------------------------------------
DOCK_CREDENTIALS = {
    "kunthukal": os.getenv("DOCK_KUNTHUKAL_KEY", "ktk_123"),
    "point_pedro": os.getenv("DOCK_PEDRO_KEY", "pedro_123"),
    "mandapam": os.getenv("DOCK_MANDAPAM_KEY", "mdp_123"),
    "mangalore": os.getenv("DOCK_MANGALORE_KEY", "mng_123"),
    "malpe": os.getenv("DOCK_MALPE_KEY", "mlp_123"),
    "all": os.getenv("COASTGUARD_PASSWORD", "master_123")  # Master Command
}

DOCK_METADATA = {
    "kunthukal": {
        "name": "Kunthukal Fish Landing Centre",
        "region": "Tamil Nadu, India",
        "latitude": 9.2757,
        "longitude": 79.1236,
        "notes": "Near Mandapam, Ramanathapuram district."
    },
    "point_pedro": {
        "name": "Point Pedro Fishing Port",
        "region": "Jaffna Peninsula, Sri Lanka",
        "latitude": 9.8283,
        "longitude": 80.2354,
        "notes": "Northernmost tip of Jaffna Peninsula."
    },
    "mandapam": {
        "name": "Mandapam Fisheries Jetty",
        "region": "Tamil Nadu, India",
        "latitude": 9.2827,
        "longitude": 79.1527,
        "notes": "Close to Rameswaram, major fishing hub."
    },
    "mangalore": {
        "name": "Mangalore Old Port Authority",
        "region": "Karnataka, India",
        "latitude": 12.8700,
        "longitude": 74.8800,
        "notes": "Dakshina Kannada hub."
    },
    "malpe": {
        "name": "Malpe Fishing Harbour Authority",
        "region": "Karnataka, India",
        "latitude": 13.3500,
        "longitude": 74.7000,
        "notes": "Udupi district hub."
    },
    "all": {
        "name": "Master Coordination Command (All Docks)",
        "region": "Multi-Region Sector",
        "latitude": 9.5000,
        "longitude": 79.5000,
        "notes": "Central Command view."
    }
}

# ---------------------------------------------------------
# MOCK TELEMETRY DATABASE WITH UPDATED COORDINATES
# ---------------------------------------------------------
MOCK_FLEET_DATABASE = [
    # Kunthukal Vessels (Tamil Nadu)
    {
        "vessel_id": "IND-TN-09-101",
        "name": "Ramanatha Express",
        "dock_id": "kunthukal",
        "status": "Active",
        "risk": "Low",
        "latitude": 9.2757,
        "longitude": 79.1236
    },
    {
        "vessel_id": "IND-TN-09-102",
        "name": "Sethu Express",
        "dock_id": "kunthukal",
        "status": "Anchored",
        "risk": "Low",
        "latitude": 9.2740,
        "longitude": 79.1210
    },

    # Point Pedro Vessels (Sri Lanka)
    {
        "vessel_id": "LKA-JAF-01-88",
        "name": "Jaffna Breeze",
        "dock_id": "point_pedro",
        "status": "In Transit",
        "risk": "Moderate",
        "latitude": 9.8283,
        "longitude": 80.2354
    },
    {
        "vessel_id": "LKA-JAF-01-99",
        "name": "Northern Pearl",
        "dock_id": "point_pedro",
        "status": "SOS Alert",
        "risk": "Critical",
        "latitude": 9.8310,
        "longitude": 80.2400
    },

    # Mandapam Vessels (Tamil Nadu)
    {
        "vessel_id": "IND-TN-09-505",
        "name": "Pamban Trawler",
        "dock_id": "mandapam",
        "status": "Active",
        "risk": "Low",
        "latitude": 9.2827,
        "longitude": 79.1527
    },
    {
        "vessel_id": "IND-TN-09-506",
        "name": "Rameswaram King",
        "dock_id": "mandapam",
        "status": "Drifting",
        "risk": "High",
        "latitude": 9.2850,
        "longitude": 79.1580
    }
]

MOCK_INCIDENTS_DATABASE = [
    {
        "incident_id": "INC-KTK-01",
        "dock_id": "kunthukal",
        "vessel": "Sethu Express",
        "type": "Shallow Reef Warning",
        "details": "Vessel near Mandapam channel shallow zone. Advised to stay in marked lane."
    },
    {
        "incident_id": "INC-PEDRO-02",
        "dock_id": "point_pedro",
        "vessel": "Northern Pearl",
        "type": "Cross-Border SOS / Engine Stall",
        "details": "Engine failure 1.5 NM off Northern Jaffna coast (9.8310° N, 80.2400° E). Tow boat dispatched."
    },
    {
        "incident_id": "INC-MDP-03",
        "dock_id": "mandapam",
        "vessel": "Rameswaram King",
        "type": "High Drift Warning",
        "details": "Drifting east toward international maritime line at 1.8 knots."
    }
]

# ---------------------------------------------------------
# API ENDPOINTS
# ---------------------------------------------------------
@router.post("/login")
def coastguard_login(payload: Dict[str, str]):
    dock_id = payload.get("dock_id", "").lower()
    password = payload.get("password", "")

    if dock_id not in DOCK_CREDENTIALS:
        raise HTTPException(status_code=400, detail="Unknown coastal dock authority selected.")

    if password == DOCK_CREDENTIALS[dock_id] or password == DOCK_CREDENTIALS["all"]:
        metadata = DOCK_METADATA.get(dock_id, {})
        return {
            "status": "authenticated",
            "dock_id": dock_id,
            "dock_name": metadata.get("name", dock_id.title()),
            "region": metadata.get("region", ""),
            "latitude": metadata.get("latitude", 0.0),
            "longitude": metadata.get("longitude", 0.0)
        }

    raise HTTPException(status_code=401, detail="Invalid security key for selected dock authority.")

@router.get("/fleet")
def get_dock_fleet(x_dock_id: Optional[str] = Header(None, alias="X-Dock-Id")):
    if not x_dock_id or x_dock_id == "all":
        return MOCK_FLEET_DATABASE
    
    return [vessel for vessel in MOCK_FLEET_DATABASE if vessel["dock_id"] == x_dock_id]

@router.get("/incidents")
def get_dock_incidents(x_dock_id: Optional[str] = Header(None, alias="X-Dock-Id")):
    if not x_dock_id or x_dock_id == "all":
        return MOCK_INCIDENTS_DATABASE

    return [inc for inc in MOCK_INCIDENTS_DATABASE if inc["dock_id"] == x_dock_id]

@router.get("/docks")
def list_all_docks():
    return DOCK_METADATA