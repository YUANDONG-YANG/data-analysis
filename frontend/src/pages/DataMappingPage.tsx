import { useCallback, useEffect, useMemo, useState } from "react";
import Papa from "papaparse";
import yaml from "js-yaml";

type CommunityMapping = {
  variant: string;
  canonical: string;
  source: "config" | "detected" | "auto-suggested";
  count: number;
  samples: string[];
  confidence?: "high" | "medium" | "low";
};

function suggestCanonicalName(variant: string): { canonical: string; confidence: "high" | "medium" | "low" } {
  const normalized = variant
    .replace(/\s*-\s*Phase\s+\d+/gi, "")
    .replace(/\s+TH$/i, " Townhomes")
    .replace(/\s+Est\.?$/i, " Estates")
    .replace(/[-_]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const titleCased = normalized
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");

  let confidence: "high" | "medium" | "low" = "high";
  if (variant !== normalized) {
    confidence = variant.includes("Phase") || variant.includes("TH") || variant.includes("Est") ? "high" : "medium";
  }
  if (variant === titleCased) {
    confidence = "low";
  }

  return { canonical: titleCased, confidence };
}

type ConfigData = {
  community_names?: {
    aliases?: Record<string, string>;
    path_slugs?: string[];
  };
};

function previewMatchesSearch(row: Record<string, unknown>, rawQuery: string): boolean {
  const q = rawQuery.trim().toLowerCase();
  if (!q) return true;

  const parts: string[] = [
    String(row.community_name_original ?? ""),
    String(row.community_name_mapped ?? ""),
    row.is_mapped ? "mapped" : "unchanged",
  ];
  for (const [key, val] of Object.entries(row)) {
    if (key === "community_name_original" || key === "community_name_mapped" || key === "is_mapped") {
      continue;
    }
    if (val != null && typeof val !== "object") {
      parts.push(String(val));
    }
  }
  const haystack = parts.join(" ").toLowerCase();
  return haystack.includes(q);
}

export function DataMappingPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [configMappings, setConfigMappings] = useState<Record<string, string>>({});
  const [detectedVariants, setDetectedVariants] = useState<Map<string, number>>(new Map());
  const [userMappings, setUserMappings] = useState<Record<string, string>>({});
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [previewPage, setPreviewPage] = useState(1);
  const [previewSearchQuery, setPreviewSearchQuery] = useState("");
  const [configPage, setConfigPage] = useState(1);
  const previewPageSize = 20;
  const configPageSize = 10;

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);

      try {
        // Load config.yaml
        const configResponse = await fetch("/config.yaml");
        if (!configResponse.ok) throw new Error("Failed to load config.yaml");
        const configText = await configResponse.text();
        const config = yaml.load(configText) as ConfigData;
        const aliases = config.community_names?.aliases || {};
        setConfigMappings(aliases);

        // Initialize user mappings with config
        setUserMappings({ ...aliases });

        // Load and analyze sales data
        const salesResponse = await fetch("/api/final-data.csv");
        if (!salesResponse.ok) {
          // Fallback to bronze layer
          const bronzeA = await fetch("/data/bronze/sales_builder_a.csv");
          const bronzeB = await fetch("/data/bronze/sales_builder_b.csv");
          
          if (bronzeA.ok && bronzeB.ok) {
            const textA = await bronzeA.text();
            const textB = await bronzeB.text();
            
            const parsedA = Papa.parse<Record<string, string>>(textA, { header: true });
            const parsedB = Papa.parse<Record<string, string>>(textB, { header: true });
            
            const allData = [...parsedA.data, ...parsedB.data];
            setPreviewData(allData.slice(0, 20));
            
            // Count variants
            const variantCounts = new Map<string, number>();
            allData.forEach((row) => {
              const name = row.community_name;
              if (name) {
                variantCounts.set(name, (variantCounts.get(name) || 0) + 1);
              }
            });
            setDetectedVariants(variantCounts);
          }
        } else {
          const text = await salesResponse.text();
          const parsed = Papa.parse<Record<string, string>>(text, { header: true });
          setPreviewData(parsed.data.slice(0, 20));
          
          // Count variants from processed data
          const variantCounts = new Map<string, number>();
          parsed.data.forEach((row) => {
            const name = row.community_name;
            if (name) {
              variantCounts.set(name, (variantCounts.get(name) || 0) + 1);
            }
          });
          setDetectedVariants(variantCounts);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }

    void loadData();
  }, []);

  // Generate mapping list with smart suggestions
  const mappingList = useMemo<CommunityMapping[]>(() => {
    const result: CommunityMapping[] = [];
    const processedVariants = new Set<string>();

    // Add configured mappings
    Object.entries(configMappings).forEach(([variant, canonical]) => {
      processedVariants.add(variant);
      result.push({
        variant,
        canonical: userMappings[variant] || canonical,
        source: "config",
        count: detectedVariants.get(variant) || 0,
        samples: [],
      });
    });

    // Add detected but unmapped variants with smart suggestions
    detectedVariants.forEach((count, variant) => {
      if (!processedVariants.has(variant)) {
        const suggestion = suggestCanonicalName(variant);
        result.push({
          variant,
          canonical: userMappings[variant] || suggestion.canonical,
          source: userMappings[variant] ? "detected" : "auto-suggested",
          count,
          samples: [],
          confidence: suggestion.confidence,
        });
      }
    });

    return result.sort((a, b) => b.count - a.count);
  }, [configMappings, detectedVariants, userMappings]);

  // Preview data with applied mappings
  const previewWithMappings = useMemo(() => {
    return previewData.map((row) => {
      const original = row.community_name;
      const mapped = userMappings[original] || original;
      return {
        ...row,
        community_name_original: original,
        community_name_mapped: mapped,
        is_mapped: original !== mapped,
      };
    });
  }, [previewData, userMappings]);

  const previewFiltered = useMemo(() => {
    return previewWithMappings.filter((row) =>
      previewMatchesSearch(row as Record<string, unknown>, previewSearchQuery),
    );
  }, [previewWithMappings, previewSearchQuery]);

  useEffect(() => {
    setPreviewPage(1);
  }, [previewSearchQuery]);

  // Paginated preview (after search filter)
  const totalPreviewPages = Math.max(1, Math.ceil(previewFiltered.length / previewPageSize));
  const safePreviewPage = Math.min(previewPage, totalPreviewPages);
  const paginatedPreview = useMemo(() => {
    const start = (safePreviewPage - 1) * previewPageSize;
    return previewFiltered.slice(start, start + previewPageSize);
  }, [previewFiltered, safePreviewPage, previewPageSize]);

  // Paginated config list
  const totalConfigPages = Math.max(1, Math.ceil(mappingList.length / configPageSize));
  const safeConfigPage = Math.min(configPage, totalConfigPages);
  const paginatedMappingList = useMemo(() => {
    const start = (safeConfigPage - 1) * configPageSize;
    return mappingList.slice(start, start + configPageSize);
  }, [mappingList, safeConfigPage, configPageSize]);

  // Group similar variants for bulk mapping
  const variantGroups = useMemo(() => {
    const groups = new Map<string, string[]>();
    
    detectedVariants.forEach((_, variant) => {
      const suggestion = suggestCanonicalName(variant);
      const canonical = suggestion.canonical;
      
      if (!groups.has(canonical)) {
        groups.set(canonical, []);
      }
      groups.get(canonical)!.push(variant);
    });

    // Only return groups with multiple variants
    return Array.from(groups.entries())
      .filter(([_, variants]) => variants.length > 1)
      .map(([canonical, variants]) => ({
        canonical,
        variants,
        totalCount: variants.reduce((sum, v) => sum + (detectedVariants.get(v) || 0), 0),
      }))
      .sort((a, b) => b.totalCount - a.totalCount);
  }, [detectedVariants]);

  const handleMappingChange = useCallback((variant: string, canonical: string) => {
    setUserMappings((prev) => ({
      ...prev,
      [variant]: canonical,
    }));
  }, []);

  const handleResetMapping = useCallback((variant: string) => {
    setUserMappings((prev) => {
      const next = { ...prev };
      delete next[variant];
      return next;
    });
  }, []);

  const handleApplyAllSuggestions = useCallback(() => {
    const newMappings: Record<string, string> = { ...userMappings };
    detectedVariants.forEach((_, variant) => {
      if (!configMappings[variant] && !userMappings[variant]) {
        const suggestion = suggestCanonicalName(variant);
        newMappings[variant] = suggestion.canonical;
      }
    });
    setUserMappings(newMappings);
  }, [configMappings, detectedVariants, userMappings]);

  const handleApplyHighConfidence = useCallback(() => {
    const newMappings: Record<string, string> = { ...userMappings };
    detectedVariants.forEach((_, variant) => {
      if (!configMappings[variant] && !userMappings[variant]) {
        const suggestion = suggestCanonicalName(variant);
        if (suggestion.confidence === "high") {
          newMappings[variant] = suggestion.canonical;
        }
      }
    });
    setUserMappings(newMappings);
  }, [configMappings, detectedVariants, userMappings]);

  const handleBulkMap = useCallback((variants: string[], canonical: string) => {
    const newMappings: Record<string, string> = { ...userMappings };
    variants.forEach((variant) => {
      newMappings[variant] = canonical;
    });
    setUserMappings(newMappings);
  }, [userMappings]);

  const handleAcceptSuggestion = useCallback((variant: string) => {
    const suggestion = suggestCanonicalName(variant);
    setUserMappings((prev) => ({
      ...prev,
      [variant]: suggestion.canonical,
    }));
  }, []);

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const saveConfig = useCallback(async () => {
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      const response = await fetch("/api/save-config", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          community_names: {
            aliases: userMappings,
          },
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: "Failed to save configuration" }));
        throw new Error(error.message || "Failed to save configuration");
      }

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save configuration");
    } finally {
      setSaving(false);
    }
  }, [userMappings]);

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl">
        <div className="flex h-64 items-center justify-center">
          <p className="text-ink-muted">Loading data mappings...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-6xl">
        <div className="rounded-2xl border border-red-500/20 bg-red-950/30 p-6">
          <p className="text-red-200">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <article className="mx-auto max-w-6xl">
      <header className="border-b border-white/[0.06] pb-8">
        <p className="text-[0.65rem] font-semibold uppercase tracking-[0.35em] text-accent">
          Data Management
        </p>
        <h1 className="mt-2 text-balance font-sans text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
          Community Name Mapping Configuration
        </h1>
        <p className="mt-4 max-w-3xl text-lg leading-relaxed text-ink-muted">
          Review detected community name variants from source data, configure canonical mappings, and
          preview the standardization effects in real-time. Click "Save Configuration" to apply changes
          to the system - no coding required!
        </p>

        {/* Workflow Guide */}
        <div className="mt-6 rounded-2xl border border-accent/20 bg-accent/5 p-5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-accent-glow">
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Quick Start Workflow
          </h3>
          <ol className="space-y-2 text-sm text-ink-muted">
            <li className="flex items-start gap-2">
              <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-accent/20 text-xs font-semibold text-accent">1</span>
              <span>
                Use <strong className="text-ink">Bulk mapping</strong> to align similar community names
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-accent/20 text-xs font-semibold text-accent">2</span>
              <span>Click <strong className="text-ink">"Apply High Confidence"</strong> to auto-apply reliable suggestions</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-accent/20 text-xs font-semibold text-accent">3</span>
              <span>Manually review and adjust remaining mappings in the configuration panel</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-accent/20 text-xs font-semibold text-accent">4</span>
              <span>Check <strong className="text-ink">Preview</strong> panel to verify mapping effects</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-accent/20 text-xs font-semibold text-accent">5</span>
              <span>Click <strong className="text-ink">"💾 Save Configuration"</strong> to apply changes</span>
            </li>
          </ol>
        </div>
      </header>

      {variantGroups.length > 0 && (
        <section className="mt-8 rounded-2xl border border-white/[0.06] bg-canvas-elevated/50 p-6 shadow-card">
          <h2 className="mb-4 text-xl font-semibold text-ink">Bulk mapping</h2>
          <p className="mb-4 text-sm text-ink-muted">
            System detected variants that can be mapped to the same canonical name. Review and apply in bulk.
          </p>
          <div className="space-y-3">
            {variantGroups.map((group) => (
              <div
                key={group.canonical}
                className="rounded-xl border border-white/[0.06] bg-canvas/60 p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-ink">→ {group.canonical}</p>
                      <span className="rounded-full bg-accent/10 px-2 py-0.5 text-xs text-accent">
                        {group.totalCount} records
                      </span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {group.variants.map((variant) => (
                        <span
                          key={variant}
                          className="rounded-lg bg-white/[0.03] px-2 py-1 font-mono text-xs text-ink-muted"
                        >
                          {variant}
                        </span>
                      ))}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleBulkMap(group.variants, group.canonical)}
                    className="whitespace-nowrap rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-sm font-medium text-emerald-200 transition hover:bg-emerald-500/15"
                  >
                    Apply Group
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        {/* Mapping Configuration Panel */}
        <section className="rounded-2xl border border-white/[0.06] bg-canvas-elevated/50 p-6 shadow-card">
          <div className="mb-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-ink">Mapping Configuration</h2>
                <p className="mt-1 text-xs text-ink-faint">
                  Page {safeConfigPage} of {totalConfigPages} ({mappingList.length} total variants)
                </p>
              </div>
            </div>
            <div className="mt-4 flex gap-3">
              <button
                type="button"
                onClick={handleApplyHighConfidence}
                className="flex-1 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-sm font-medium text-emerald-200 transition hover:bg-emerald-500/15 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={saving}
              >
                Apply High Confidence
              </button>
              <button
                type="button"
                onClick={handleApplyAllSuggestions}
                className="flex-1 rounded-lg border border-violet-500/30 bg-violet-500/10 px-4 py-2.5 text-sm font-medium text-violet-200 transition hover:bg-violet-500/15 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={saving}
              >
                Apply All Suggestions
              </button>
              <button
                type="button"
                onClick={saveConfig}
                disabled={saving}
                className="flex-1 rounded-lg border border-accent/30 bg-accent/10 px-4 py-2.5 text-sm font-semibold text-accent-glow transition hover:bg-accent/15 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {saving ? "Saving..." : "💾 Save Configuration"}
              </button>
            </div>
          </div>

          {saveSuccess && (
            <div className="mb-4 rounded-xl border border-emerald-500/20 bg-emerald-950/30 p-4">
              <div className="flex items-center gap-3">
                <svg className="h-5 w-5 flex-shrink-0 text-emerald-200" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <p className="text-sm font-medium text-emerald-100">
                  Configuration saved successfully! Changes will take effect on the next pipeline run.
                </p>
              </div>
            </div>
          )}

          {saveError && (
            <div className="mb-4 rounded-xl border border-red-500/20 bg-red-950/30 p-4">
              <div className="flex items-start gap-3">
                <svg className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-200" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-100">Failed to save configuration</p>
                  <p className="mt-1 text-xs text-red-200/80">{saveError}</p>
                </div>
              </div>
            </div>
          )}

          {mappingList.filter((m) => m.source === "auto-suggested").length > 0 && (
            <div className="mb-4 rounded-xl border border-amber-500/20 bg-amber-950/20 p-4">
              <div className="flex items-start gap-3">
                <svg className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-200" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div className="flex-1">
                  <p className="text-sm font-medium text-amber-100">Suggestions available</p>
                  <p className="mt-1 text-xs leading-relaxed text-amber-200/80">
                    {mappingList.filter((m) => m.source === "auto-suggested").length} unmapped variant(s) detected. 
                    The system has suggested canonical names based on common patterns. Review and apply or modify as needed.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="data-preview-scroll max-h-[600px] space-y-3 overflow-y-auto pr-2">
            {paginatedMappingList.map((mapping) => (
              <div
                key={mapping.variant}
                className="rounded-xl border border-white/[0.06] bg-canvas/60 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-mono text-sm text-ink">{mapping.variant}</p>
                      {mapping.source === "config" && (
                        <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-200">
                          ✓ configured
                        </span>
                      )}
                      {mapping.source === "detected" && (
                        <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-xs text-amber-200">
                          detected
                        </span>
                      )}
                      {mapping.source === "auto-suggested" && (
                        <span className="rounded-full bg-violet-500/10 px-2 py-0.5 text-xs text-violet-200">
                          ✨ auto-suggested
                        </span>
                      )}
                      {mapping.confidence && mapping.source === "auto-suggested" && (
                        <span className={`text-xs ${
                          mapping.confidence === "high" ? "text-emerald-300" :
                          mapping.confidence === "medium" ? "text-amber-300" :
                          "text-ink-faint"
                        }`}>
                          {mapping.confidence === "high" ? "high confidence" :
                           mapping.confidence === "medium" ? "medium confidence" :
                           "low confidence"}
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-ink-faint">
                      Found in {mapping.count} record{mapping.count !== 1 ? "s" : ""}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleResetMapping(mapping.variant)}
                    className="text-xs text-ink-faint hover:text-accent"
                  >
                    Reset
                  </button>
                </div>

                <div className="mt-3">
                  <label className="block text-xs font-medium text-ink-muted">
                    Maps to (canonical name):
                  </label>
                  <div className="mt-1.5 flex gap-2">
                    <input
                      type="text"
                      value={mapping.canonical}
                      onChange={(e) => handleMappingChange(mapping.variant, e.target.value)}
                      className="flex-1 rounded-lg border border-white/10 bg-canvas px-3 py-2 text-sm text-ink placeholder-ink-faint focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/50"
                      placeholder="Enter canonical community name"
                    />
                    {mapping.source === "auto-suggested" && (
                      <button
                        type="button"
                        onClick={() => handleAcceptSuggestion(mapping.variant)}
                        className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs font-medium text-emerald-200 transition hover:bg-emerald-500/15"
                        title="Accept smart suggestion"
                      >
                        ✓ Accept
                      </button>
                    )}
                  </div>
                </div>

                {mapping.variant !== mapping.canonical && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-emerald-200">
                    <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span>Will be standardized</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {mappingList.length === 0 && (
            <p className="py-8 text-center text-sm text-ink-faint">No mappings detected</p>
          )}

          {/* Pagination Controls */}
          {mappingList.length > configPageSize && (
            <div className="mt-4 flex items-center justify-between gap-4 border-t border-white/[0.06] pt-4">
              <span className="text-xs text-ink-faint">
                Showing {(safeConfigPage - 1) * configPageSize + 1}-
                {Math.min(safeConfigPage * configPageSize, mappingList.length)} of {mappingList.length}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setConfigPage(1)}
                  disabled={safeConfigPage === 1}
                  className="rounded-lg border border-white/10 bg-canvas px-3 py-1.5 text-xs font-medium text-ink-muted transition hover:bg-white/[0.05] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  First
                </button>
                <button
                  type="button"
                  onClick={() => setConfigPage((p) => Math.max(1, p - 1))}
                  disabled={safeConfigPage === 1}
                  className="rounded-lg border border-white/10 bg-canvas px-3 py-1.5 text-xs font-medium text-ink-muted transition hover:bg-white/[0.05] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setConfigPage((p) => Math.min(totalConfigPages, p + 1))}
                  disabled={safeConfigPage === totalConfigPages}
                  className="rounded-lg border border-white/10 bg-canvas px-3 py-1.5 text-xs font-medium text-ink-muted transition hover:bg-white/[0.05] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next
                </button>
                <button
                  type="button"
                  onClick={() => setConfigPage(totalConfigPages)}
                  disabled={safeConfigPage === totalConfigPages}
                  className="rounded-lg border border-white/10 bg-canvas px-3 py-1.5 text-xs font-medium text-ink-muted transition hover:bg-white/[0.05] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Last
                </button>
              </div>
            </div>
          )}
        </section>

        {/* Preview Panel */}
        <section className="rounded-2xl border border-white/[0.06] bg-canvas-elevated/50 p-6 shadow-card">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-ink">Preview</h2>
              <p className="mt-1 text-xs text-ink-faint">
                {previewWithMappings.length} record{previewWithMappings.length === 1 ? "" : "s"} loaded
                {previewSearchQuery.trim() ? (
                  <>
                    {" "}
                    · <span className="text-accent-glow">{previewFiltered.length}</span> shown
                  </>
                ) : null}
              </p>
            </div>
            <span className="text-xs text-ink-faint">
              Page {safePreviewPage} of {totalPreviewPages}
            </span>
          </div>

          {previewWithMappings.length > 0 ? (
            <div className="mb-4">
              <label htmlFor="preview-search" className="sr-only">
                Search preview rows
              </label>
              <div className="relative">
                <span
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint"
                  aria-hidden
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </span>
                <input
                  id="preview-search"
                  type="search"
                  value={previewSearchQuery}
                  onChange={(e) => setPreviewSearchQuery(e.target.value)}
                  placeholder="Search preview rows…"
                  autoComplete="off"
                  className="w-full rounded-xl border border-white/[0.08] bg-canvas/80 py-2.5 pl-10 pr-10 text-sm text-ink placeholder:text-ink-faint/80 shadow-inner transition focus:border-accent/40 focus:outline-none focus:ring-1 focus:ring-accent/30"
                />
                {previewSearchQuery ? (
                  <button
                    type="button"
                    onClick={() => setPreviewSearchQuery("")}
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg px-2 py-1 text-xs text-ink-faint transition hover:bg-white/[0.06] hover:text-ink"
                    aria-label="Clear search"
                  >
                    Clear
                  </button>
                ) : null}
              </div>
            </div>
          ) : null}

          {previewWithMappings.length === 0 ? (
            <p className="py-8 text-center text-sm text-ink-faint">No preview data available</p>
          ) : previewFiltered.length === 0 ? (
            <p className="py-8 text-center text-sm text-ink-faint">
              No rows match “{previewSearchQuery.trim()}”. Try a shorter phrase or clear the search.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    <th className="pb-2 pr-3 text-left text-xs font-medium text-ink-faint">
                      Original
                    </th>
                    <th className="pb-2 pr-3 text-left text-xs font-medium text-ink-faint">
                      Mapped
                    </th>
                    <th className="pb-2 text-left text-xs font-medium text-ink-faint">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedPreview.map((row, idx) => (
                    <tr key={idx} className="border-b border-white/[0.03]">
                      <td className="py-2 pr-3 font-mono text-xs text-ink-muted">
                        {row.community_name_original}
                      </td>
                      <td className="py-2 pr-3 font-mono text-xs text-ink">
                        {row.community_name_mapped}
                      </td>
                      <td className="py-2">
                        {row.is_mapped ? (
                          <span className="inline-flex items-center gap-1 text-xs text-emerald-200">
                            <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                              <path
                                fillRule="evenodd"
                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                clipRule="evenodd"
                              />
                            </svg>
                            Mapped
                          </span>
                        ) : (
                          <span className="text-xs text-ink-faint">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {previewWithMappings.length === 0 ? null : previewFiltered.length === 0 ? null : (
            <div className="mt-4 flex items-center justify-between gap-4">
              <span className="text-xs text-ink-faint">
                Showing {(safePreviewPage - 1) * previewPageSize + 1}-
                {Math.min(safePreviewPage * previewPageSize, previewFiltered.length)} of{" "}
                {previewFiltered.length}
                {previewSearchQuery.trim() ? ` (filtered from ${previewWithMappings.length})` : ""}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setPreviewPage(1)}
                  disabled={safePreviewPage === 1}
                  className="rounded-lg border border-white/10 bg-canvas px-3 py-1.5 text-xs font-medium text-ink-muted transition hover:bg-white/[0.05] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  First
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewPage((p) => Math.max(1, p - 1))}
                  disabled={safePreviewPage === 1}
                  className="rounded-lg border border-white/10 bg-canvas px-3 py-1.5 text-xs font-medium text-ink-muted transition hover:bg-white/[0.05] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewPage((p) => Math.min(totalPreviewPages, p + 1))}
                  disabled={safePreviewPage === totalPreviewPages}
                  className="rounded-lg border border-white/10 bg-canvas px-3 py-1.5 text-xs font-medium text-ink-muted transition hover:bg-white/[0.05] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewPage(totalPreviewPages)}
                  disabled={safePreviewPage === totalPreviewPages}
                  className="rounded-lg border border-white/10 bg-canvas px-3 py-1.5 text-xs font-medium text-ink-muted transition hover:bg-white/[0.05] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Last
                </button>
              </div>
            </div>
          )}
        </section>
      </div>

      {/* Statistics Summary */}
      <section className="mt-6 rounded-2xl border border-white/[0.06] bg-canvas-elevated/50 p-6 shadow-card">
        <h2 className="mb-4 text-xl font-semibold text-ink">Mapping Statistics</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-white/[0.06] bg-canvas/60 p-4">
            <p className="text-2xl font-semibold text-ink">{mappingList.length}</p>
            <p className="mt-1 text-sm text-ink-muted">Total Variants</p>
          </div>
          <div className="rounded-xl border border-white/[0.06] bg-canvas/60 p-4">
            <p className="text-2xl font-semibold text-emerald-200">
              {mappingList.filter((m) => m.source === "config").length}
            </p>
            <p className="mt-1 text-sm text-ink-muted">Configured Mappings</p>
          </div>
          <div className="rounded-xl border border-white/[0.06] bg-canvas/60 p-4">
            <p className="text-2xl font-semibold text-violet-200">
              {mappingList.filter((m) => m.source === "auto-suggested").length}
            </p>
            <p className="mt-1 text-sm text-ink-muted">Auto-Suggested</p>
          </div>
        </div>
      </section>
    </article>
  );
}
