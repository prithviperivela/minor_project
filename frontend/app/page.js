"use client";

import { useMemo, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

const sampleDescription =
  "I need a modern living room with warm lighting, wall panels, storage, repainting, and durable furniture. Budget should stay controlled and the work should be completed soon.";

const initialForm = {
  client_name: "Demo Client",
  project_title: "Modern Living Room Upgrade",
  room_type: "Living Room",
  location: "Manipal",
  length: "14",
  width: "12",
  height: "10",
  budget: "180000",
  description: sampleDescription,
};

export default function Home() {
  const [form, setForm] = useState(initialForm);
  const [photos, setPhotos] = useState([]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const area = useMemo(() => {
    const length = Number(form.length);
    const width = Number(form.width);
    if (!length || !width) return 0;
    return length * width;
  }, [form.length, form.width]);

  function updateField(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  async function submitAnalysis(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    const payload = new FormData();
    Object.entries(form).forEach(([key, value]) => payload.append(key, value));
    Array.from(photos).forEach((photo) => payload.append("photos", photo));

    try {
      const response = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        body: payload,
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || "Analysis failed");
      }
      const data = await response.json();
      setReport(data);
      window.setTimeout(() => {
        document.getElementById("report")?.scrollIntoView({ behavior: "smooth" });
      }, 80);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <section className="hero">
        <div className="heroText">
          <p className="eyebrow">Multimodal interior planning prototype</p>
          <h1>SyteScan</h1>
          <p>
            Collect room data, analyze photos and requirements, generate an interior
            site report, then preview contractor discovery and quotations.
          </p>
        </div>
        <div className="heroStats" aria-label="prototype capabilities">
          <div>
            <strong>CV</strong>
            <span>Lighting, color, quality, layout complexity</span>
          </div>
          <div>
            <strong>NLP</strong>
            <span>Style, work items, priorities, timeline</span>
          </div>
          <div>
            <strong>IR</strong>
            <span>Contractor matching and quote ranking</span>
          </div>
        </div>
      </section>

      <section className="workspace">
        <form className="panel inputPanel" onSubmit={submitAnalysis}>
          <div className="sectionTitle">
            <p>Site data collection</p>
            <h2>New Analysis</h2>
          </div>

          <div className="grid two">
            <label>
              Client name
              <input name="client_name" value={form.client_name} onChange={updateField} />
            </label>
            <label>
              Project title
              <input name="project_title" value={form.project_title} onChange={updateField} required />
            </label>
          </div>

          <div className="grid two">
            <label>
              Room type
              <select name="room_type" value={form.room_type} onChange={updateField}>
                <option>Living Room</option>
                <option>Bedroom</option>
                <option>Kitchen</option>
                <option>Bathroom</option>
                <option>Office</option>
                <option>Dining</option>
              </select>
            </label>
            <label>
              Location
              <input name="location" value={form.location} onChange={updateField} />
            </label>
          </div>

          <div className="dimensionGrid">
            <label>
              Length ft
              <input name="length" type="number" min="1" value={form.length} onChange={updateField} required />
            </label>
            <label>
              Width ft
              <input name="width" type="number" min="1" value={form.width} onChange={updateField} required />
            </label>
            <label>
              Height ft
              <input name="height" type="number" min="1" value={form.height} onChange={updateField} required />
            </label>
          </div>

          <div className="computedRow">
            <span>Computed floor area</span>
            <strong>{area ? `${area.toFixed(0)} sq ft` : "Enter dimensions"}</strong>
          </div>

          <label>
            Budget INR
            <input name="budget" type="number" min="0" value={form.budget} onChange={updateField} required />
          </label>

          <label>
            Site photos
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              multiple
              onChange={(event) => setPhotos(event.target.files || [])}
            />
          </label>

          <label>
            Free-text requirements
            <textarea
              name="description"
              value={form.description}
              onChange={updateField}
              rows={7}
              required
            />
          </label>

          {error ? <p className="error">{error}</p> : null}

          <button className="primaryButton" disabled={loading}>
            {loading ? "Analyzing..." : "Generate Interior Site Report"}
          </button>
        </form>

        <aside className="panel pipelinePanel">
          <div className="sectionTitle">
            <p>Methodology pipeline</p>
            <h2>Prototype Flow</h2>
          </div>
          {[
            "Upload site photos and enter measurements",
            "Analyze visual quality, lighting, color, and complexity",
            "Extract style, work items, priorities, and timeline",
            "Score budget feasibility and geometry readiness",
            "Generate report and conceptual marketplace listing",
          ].map((item, index) => (
            <div className="pipelineStep" key={item}>
              <span>{index + 1}</span>
              <p>{item}</p>
            </div>
          ))}
          <div className="signalBox">
            <span>Signal</span>
            <strong>Contractor Discovery Confidence</strong>
            <p>Used to decide whether the report is ready for quote release.</p>
          </div>
        </aside>
      </section>

      {report ? <ReportView report={report} /> : <EmptyReport />}
    </main>
  );
}

function EmptyReport() {
  return (
    <section className="emptyReport">
      <div>
        <p className="eyebrow">Waiting for analysis</p>
        <h2>Generated report and contractor matches will appear here.</h2>
      </div>
    </section>
  );
}

function ReportView({ report }) {
  return (
    <section className="report" id="report">
      <div className="reportHeader">
        <div>
          <p className="eyebrow">Interior Site Report</p>
          <h2>{report.project_title}</h2>
          <p>
            {report.room_type} · {report.location || "Location not specified"} ·{" "}
            {new Date(report.created_at).toLocaleString()}
          </p>
        </div>
        <div className={`confidence ${report.contractor_discovery.level}`}>
          <span>{report.contractor_discovery.signal}</span>
          <strong>{report.contractor_discovery.score}/100</strong>
          <small>{report.contractor_discovery.level}</small>
        </div>
      </div>

      <div className="reportGrid">
        <Metric label="Area" value={`${report.budget_analysis.area_sqft} sq ft`} />
        <Metric label="Budget category" value={report.budget_analysis.budget_category} />
        <Metric label="Feasibility" value={report.budget_analysis.feasibility} />
        <Metric label="Quote gate" value={report.marketplace_listing.quote_release_gate} />
      </div>

      <div className="contentGrid">
        <article className="panel">
          <div className="sectionTitle">
            <p>NLP processing</p>
            <h3>Requirement Extraction</h3>
          </div>
          <p className="summary">{report.requirements.structured_summary}</p>
          <TagGroup title="Work items" items={report.requirements.work_items} />
          <TagGroup title="Style preferences" items={report.requirements.style_preferences} />
          <TagGroup title="Priorities" items={report.requirements.priorities} />
          <div className="miniRow">
            <span>Timeline</span>
            <strong>{report.requirements.timeline}</strong>
          </div>
        </article>

        <article className="panel">
          <div className="sectionTitle">
            <p>Structured data</p>
            <h3>Budget & Measurements</h3>
          </div>
          <div className="detailsList">
            <span>Length</span>
            <strong>{report.measurements.length_ft} ft</strong>
            <span>Width</span>
            <strong>{report.measurements.width_ft} ft</strong>
            <span>Height</span>
            <strong>{report.measurements.height_ft} ft</strong>
            <span>Budget per sq ft</span>
            <strong>₹{Math.round(report.budget_analysis.budget_per_sqft).toLocaleString()}</strong>
          </div>
          <p className="summary">{report.budget_analysis.recommendation}</p>
        </article>
      </div>

      <article className="panel imagePanel">
        <div className="sectionTitle">
          <p>Computer vision</p>
          <h3>Site Photograph Analysis</h3>
        </div>
        {report.image_analysis.length ? (
          <div className="imageGrid">
            {report.image_analysis.map((image) => (
              <div className="imageCard" key={image.file}>
                <img src={`${API_BASE}${image.url}`} alt={`Site upload ${image.file}`} />
                <div>
                  <strong>{image.lighting} lighting</strong>
                  <p>
                    {image.image_quality} · {image.layout_complexity} complexity ·{" "}
                    {image.resolution?.width}x{image.resolution?.height}
                  </p>
                  <TagGroup title="Dominant colors" items={image.dominant_colors || []} compact />
                  <TagGroup title="Material hints" items={image.surface_material_hints || []} compact />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="summary">No photos were uploaded. The report still uses text, measurement, and budget data.</p>
        )}
      </article>

      <div className="contentGrid">
        <article className="panel">
          <div className="sectionTitle">
            <p>Actionable output</p>
            <h3>Recommendations</h3>
          </div>
          <ul className="recommendations">
            {report.recommendations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="panel">
          <div className="sectionTitle">
            <p>Marketplace listing</p>
            <h3>Discovery Signal</h3>
          </div>
          <p className="summary">{report.contractor_discovery.impact}</p>
          <p className="summary strong">{report.contractor_discovery.action}</p>
        </article>
      </div>

      <article className="panel">
        <div className="sectionTitle">
          <p>Contractor discovery</p>
          <h3>Quote Comparison</h3>
        </div>
        <div className="contractorTable">
          <div className="tableHead">
            <span>Contractor</span>
            <span>Match</span>
            <span>Rating</span>
            <span>Estimated quote</span>
          </div>
          {report.contractor_matches.map((contractor) => (
            <div className="tableRow" key={contractor.id}>
              <div>
                <strong>{contractor.name}</strong>
                <p>{contractor.portfolio}</p>
              </div>
              <span>{contractor.match_score}%</span>
              <span>{contractor.rating} / 5</span>
              <span>₹{contractor.estimated_quote.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function TagGroup({ title, items, compact = false }) {
  return (
    <div className={compact ? "tagGroup compact" : "tagGroup"}>
      <span>{title}</span>
      <div>
        {items.map((item) => (
          <small key={item}>{item}</small>
        ))}
      </div>
    </div>
  );
}
