from __future__ import annotations

import json
import math
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageStat


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
UPLOAD_DIR = PROJECT_ROOT / "uploads"
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_FILE = DATA_DIR / "reports.json"

UPLOAD_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

app = FastAPI(title="SyteScan API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


STYLE_KEYWORDS = {
    "modern": ["modern", "sleek", "contemporary"],
    "minimal": ["minimal", "minimalist", "simple", "clean"],
    "luxury": ["luxury", "premium", "high end", "high-end", "elegant"],
    "traditional": ["traditional", "classic", "wooden", "ethnic"],
    "industrial": ["industrial", "raw", "concrete", "metal"],
    "scandinavian": ["scandinavian", "nordic", "cozy"],
}

WORK_KEYWORDS = {
    "painting": ["paint", "painting", "wall color", "repaint"],
    "false ceiling": ["false ceiling", "ceiling", "gypsum", "pop"],
    "flooring": ["floor", "flooring", "tiles", "vinyl", "marble"],
    "lighting": ["light", "lighting", "led", "warm light", "spotlight"],
    "modular kitchen": ["modular kitchen", "kitchen cabinet", "countertop"],
    "wardrobe": ["wardrobe", "closet", "storage unit"],
    "furniture": ["furniture", "sofa", "bed", "table", "chair"],
    "electrical": ["electrical", "wiring", "switch", "socket"],
    "plumbing": ["plumbing", "sink", "tap", "pipe"],
    "wall treatment": ["wallpaper", "panel", "wall panel", "texture"],
    "storage": ["storage", "shelves", "shelving", "cabinet"],
}

ROOM_KEYWORDS = [
    "living room",
    "bedroom",
    "kitchen",
    "bathroom",
    "office",
    "study",
    "hall",
    "dining",
]

CONTRACTORS = [
    {
        "id": "c1",
        "name": "UrbanNest Interiors",
        "specializations": ["living room", "bedroom", "lighting", "furniture"],
        "rating": 4.7,
        "reviews": 128,
        "portfolio": "Modern apartments and compact family homes",
        "base_multiplier": 1.08,
    },
    {
        "id": "c2",
        "name": "KitchenCraft Studio",
        "specializations": ["kitchen", "modular kitchen", "storage", "countertop"],
        "rating": 4.8,
        "reviews": 96,
        "portfolio": "Modular kitchens and utility planning",
        "base_multiplier": 1.16,
    },
    {
        "id": "c3",
        "name": "SpaceLine Designs",
        "specializations": ["minimal", "wardrobe", "false ceiling", "lighting"],
        "rating": 4.5,
        "reviews": 74,
        "portfolio": "Minimal interiors with practical storage",
        "base_multiplier": 0.98,
    },
    {
        "id": "c4",
        "name": "BudgetHome Works",
        "specializations": ["painting", "flooring", "electrical", "wall treatment"],
        "rating": 4.2,
        "reviews": 211,
        "portfolio": "Budget renovations and quick-turnaround site work",
        "base_multiplier": 0.86,
    },
    {
        "id": "c5",
        "name": "Prime Habitat Co.",
        "specializations": ["luxury", "furniture", "lighting", "bedroom"],
        "rating": 4.9,
        "reviews": 58,
        "portfolio": "Premium residential interiors",
        "base_multiplier": 1.32,
    },
]


def read_reports() -> list[dict[str, Any]]:
    if not REPORTS_FILE.exists():
        return []
    return json.loads(REPORTS_FILE.read_text(encoding="utf-8"))


def write_reports(reports: list[dict[str, Any]]) -> None:
    REPORTS_FILE.write_text(json.dumps(reports, indent=2), encoding="utf-8")


def clamp(value: float, lower: int = 0, upper: int = 100) -> int:
    return max(lower, min(upper, round(value)))


def bucket_color(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    brightness = (r + g + b) / 3
    if brightness > 220:
        return "white"
    if brightness < 45:
        return "black"
    if abs(r - g) < 18 and abs(g - b) < 18:
        return "grey"
    if r > g + 35 and r > b + 35:
        return "red/terracotta"
    if g > r + 25 and g > b + 15:
        return "green"
    if b > r + 25 and b > g + 15:
        return "blue"
    if r > 145 and g > 95 and b < 95:
        return "wood/brown"
    if r > 180 and g > 160 and b < 120:
        return "cream/beige"
    return "mixed neutral"


def analyze_image(path: Path) -> dict[str, Any]:
    try:
        with Image.open(path) as image:
            image = image.convert("RGB")
            resized = image.resize((120, 120))
            stat = ImageStat.Stat(resized)
            channels = stat.mean
            brightness = sum(channels) / 3
            contrast = sum(stat.stddev) / 3
            color_counts = Counter(bucket_color(pixel) for pixel in resized.getdata())
            dominant_colors = [color for color, _ in color_counts.most_common(4)]
            width, height = image.size

            edge_score = estimate_edge_density(resized)
            lighting = (
                "well-lit"
                if brightness >= 170
                else "moderate"
                if brightness >= 95
                else "dim"
            )
            quality = "good" if width >= 900 and height >= 700 else "usable"
            if brightness < 55 or contrast < 18:
                quality = "needs clearer photo"

            material_hints = []
            if "wood/brown" in dominant_colors:
                material_hints.append("wooden laminates or furniture surfaces")
            if "grey" in dominant_colors:
                material_hints.append("painted wall, tile, or concrete-like surface")
            if "white" in dominant_colors or "cream/beige" in dominant_colors:
                material_hints.append("light wall finishes")
            if not material_hints:
                material_hints.append("mixed interior surfaces")

            return {
                "file": path.name,
                "url": f"/uploads/{path.name}",
                "resolution": {"width": width, "height": height},
                "lighting": lighting,
                "brightness": round(brightness, 1),
                "contrast": round(contrast, 1),
                "dominant_colors": dominant_colors,
                "layout_complexity": "high" if edge_score > 34 else "medium" if edge_score > 18 else "low",
                "edge_density": edge_score,
                "surface_material_hints": material_hints,
                "image_quality": quality,
            }
    except Exception as exc:  # pragma: no cover - defensive for corrupt uploads
        return {"file": path.name, "error": f"Could not analyze image: {exc}"}


def estimate_edge_density(image: Image.Image) -> int:
    pixels = image.load()
    width, height = image.size
    changes = 0
    samples = 0
    for y in range(1, height, 2):
        for x in range(1, width, 2):
            current = sum(pixels[x, y]) / 3
            left = sum(pixels[x - 1, y]) / 3
            top = sum(pixels[x, y - 1]) / 3
            if abs(current - left) > 28 or abs(current - top) > 28:
                changes += 1
            samples += 1
    return clamp((changes / max(samples, 1)) * 100)


def extract_requirements(description: str, room_type: str) -> dict[str, Any]:
    text = description.lower()
    styles = [
        style
        for style, keywords in STYLE_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    ]
    work_items = [
        item
        for item, keywords in WORK_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    ]
    rooms = [room for room in ROOM_KEYWORDS if room in text]
    if room_type and room_type.lower() not in rooms:
        rooms.insert(0, room_type.lower())

    urgency = "normal"
    if any(word in text for word in ["urgent", "asap", "immediately", "quick", "soon"]):
        urgency = "urgent"
    elif any(word in text for word in ["month", "later", "flexible"]):
        urgency = "flexible"

    priorities = []
    for priority in ["storage", "lighting", "budget", "premium", "space saving", "durable"]:
        if priority in text:
            priorities.append(priority)

    budget_mentions = re.findall(r"(?:under|below|around|within|upto|up to)?\s*(?:rs\.?|inr|₹)?\s*\d+(?:\.\d+)?\s*(?:lakh|lakhs|k|thousand)?", text)

    return {
        "detected_rooms": rooms[:4],
        "style_preferences": styles or ["not specified"],
        "work_items": work_items or ["general interior planning"],
        "priorities": priorities or ["scope clarity"],
        "timeline": urgency,
        "budget_mentions": [item.strip() for item in budget_mentions[:3]],
        "structured_summary": build_requirement_summary(rooms, styles, work_items, priorities),
    }


def build_requirement_summary(
    rooms: list[str], styles: list[str], work_items: list[str], priorities: list[str]
) -> str:
    room = rooms[0] if rooms else "interior space"
    style = styles[0] if styles else "functional"
    work = ", ".join(work_items[:4]) if work_items else "site planning"
    focus = ", ".join(priorities[:3]) if priorities else "clear project scope"
    return f"{style.title()} {room} project covering {work}, with focus on {focus}."


def analyze_budget(length: float, width: float, height: float, budget: float, work_count: int) -> dict[str, Any]:
    area = max(length * width, 0)
    wall_area = 2 * height * (length + width) if height > 0 else 0
    project_size = "compact" if area < 100 else "standard" if area < 220 else "large"
    budget_per_sqft = budget / area if area else 0

    if budget_per_sqft >= 1800:
        category = "premium"
    elif budget_per_sqft >= 900:
        category = "medium"
    elif budget_per_sqft > 0:
        category = "economy"
    else:
        category = "missing"

    scope_pressure = work_count * 12
    feasibility = clamp((budget_per_sqft / 18) - scope_pressure + 55)
    status = "strong" if feasibility >= 75 else "workable" if feasibility >= 48 else "tight"

    recommendation = {
        "strong": "Budget can support the selected scope with room for better finishes.",
        "workable": "Budget appears workable; finalize material grades before quotation.",
        "tight": "Budget is tight for the requested scope; prioritize must-have work items.",
    }[status]

    return {
        "area_sqft": round(area, 2),
        "wall_area_sqft": round(wall_area, 2),
        "project_size": project_size,
        "budget": round(budget, 2),
        "budget_per_sqft": round(budget_per_sqft, 2),
        "budget_category": category,
        "feasibility_score": feasibility,
        "feasibility": status,
        "recommendation": recommendation,
    }


def build_recommendations(
    image_results: list[dict[str, Any]],
    requirements: dict[str, Any],
    budget: dict[str, Any],
) -> list[str]:
    recommendations = [budget["recommendation"]]
    if any(result.get("lighting") == "dim" for result in image_results):
        recommendations.append("Add better lighting photos or inspect electrical points before final quote.")
    if any(result.get("image_quality") == "needs clearer photo" for result in image_results):
        recommendations.append("Upload clearer site photos for stronger contractor discovery confidence.")
    if "storage" in requirements["priorities"]:
        recommendations.append("Validate wall dimensions and usable depth before finalizing storage modules.")
    if "modular kitchen" in requirements["work_items"]:
        recommendations.append("Capture plumbing, electrical, and countertop wall photos before quote release.")
    if not image_results:
        recommendations.append("Add at least two room photos to improve visual analysis quality.")
    return recommendations[:5]


def discovery_confidence(
    image_results: list[dict[str, Any]],
    requirements: dict[str, Any],
    budget: dict[str, Any],
) -> dict[str, Any]:
    score = 42
    score += min(len(image_results) * 12, 30)
    score += 16 if requirements["work_items"] != ["general interior planning"] else 3
    score += 12 if budget["area_sqft"] > 0 and budget["budget"] > 0 else 0
    if any(result.get("image_quality") == "needs clearer photo" for result in image_results):
        score -= 12
    if budget["feasibility"] == "tight":
        score -= 8

    score = clamp(score)
    level = "high" if score >= 76 else "medium" if score >= 52 else "low"
    action = (
        "Ready for contractor shortlisting."
        if level == "high"
        else "Ask contractors for site validation before final quote."
        if level == "medium"
        else "Collect clearer geometry, photos, and budget details before quote release."
    )
    return {
        "signal": "Contractor Discovery Confidence",
        "score": score,
        "level": level,
        "impact": "Quoted scope quality drops when room constraints are inferred from sparse imagery.",
        "action": action,
    }


def rank_contractors(report: dict[str, Any]) -> list[dict[str, Any]]:
    requirements = report["requirements"]
    work_items = set(requirements["work_items"])
    styles = set(requirements["style_preferences"])
    rooms = set(requirements["detected_rooms"])
    budget = report["budget_analysis"]["budget"]
    area = max(report["budget_analysis"]["area_sqft"], 1)
    quote_base = max(budget * 0.92, area * 850)

    ranked = []
    for contractor in CONTRACTORS:
        specs = set(contractor["specializations"])
        overlap = len(specs & (work_items | styles | rooms))
        rating_points = (contractor["rating"] - 4) * 16
        match_score = clamp(48 + overlap * 11 + rating_points)
        estimate = round(quote_base * contractor["base_multiplier"] / 1000) * 1000
        ranked.append(
            {
                **contractor,
                "match_score": match_score,
                "estimated_quote": estimate,
                "quote_note": "Includes design consultation and scope validation.",
            }
        )
    return sorted(ranked, key=lambda item: item["match_score"], reverse=True)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "SyteScan API"}


@app.post("/api/analyze")
async def analyze_project(
    client_name: str = Form("Demo Client"),
    project_title: str = Form(...),
    room_type: str = Form(...),
    location: str = Form(""),
    length: float = Form(...),
    width: float = Form(...),
    height: float = Form(...),
    budget: float = Form(...),
    description: str = Form(...),
    photos: list[UploadFile] = File(default=[]),
) -> dict[str, Any]:
    if length <= 0 or width <= 0 or height <= 0:
        raise HTTPException(status_code=400, detail="Room dimensions must be positive.")
    if budget < 0:
        raise HTTPException(status_code=400, detail="Budget cannot be negative.")

    report_id = str(uuid4())
    saved_paths = []
    for photo in photos:
        if not photo.filename:
            continue
        suffix = Path(photo.filename).suffix.lower() or ".jpg"
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise HTTPException(status_code=400, detail=f"Unsupported image file: {photo.filename}")
        target = UPLOAD_DIR / f"{report_id}-{len(saved_paths) + 1}{suffix}"
        with target.open("wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        saved_paths.append(target)

    image_results = [analyze_image(path) for path in saved_paths]
    requirements = extract_requirements(description, room_type)
    budget_analysis = analyze_budget(
        length,
        width,
        height,
        budget,
        len(requirements["work_items"]),
    )
    recommendations = build_recommendations(image_results, requirements, budget_analysis)
    confidence = discovery_confidence(image_results, requirements, budget_analysis)

    report = {
        "id": report_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "client_name": client_name,
        "project_title": project_title,
        "room_type": room_type,
        "location": location,
        "description": description,
        "measurements": {
            "length_ft": length,
            "width_ft": width,
            "height_ft": height,
        },
        "image_analysis": image_results,
        "requirements": requirements,
        "budget_analysis": budget_analysis,
        "recommendations": recommendations,
        "contractor_discovery": confidence,
        "marketplace_listing": {
            "status": "conceptual listing generated",
            "visible_to_contractors": True,
            "quote_release_gate": "geometry validation recommended"
            if confidence["level"] != "high"
            else "ready for quote release",
        },
    }
    report["contractor_matches"] = rank_contractors(report)

    reports = read_reports()
    reports.insert(0, report)
    write_reports(reports[:25])
    return report


@app.get("/api/reports")
def list_reports() -> list[dict[str, Any]]:
    return read_reports()


@app.get("/api/reports/{report_id}")
def get_report(report_id: str) -> dict[str, Any]:
    for report in read_reports():
        if report["id"] == report_id:
            return report
    raise HTTPException(status_code=404, detail="Report not found.")


@app.get("/api/contractors")
def contractors() -> list[dict[str, Any]]:
    return CONTRACTORS


@app.post("/api/reports/{report_id}/quotes")
def generate_quotes(report_id: str) -> dict[str, Any]:
    report = get_report(report_id)
    return {
        "report_id": report_id,
        "quotes": report["contractor_matches"],
    }
