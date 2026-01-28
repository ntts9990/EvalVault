import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { Layout } from "../components/Layout";
import { MarkdownContent } from "../components/MarkdownContent";
import { AnalysisNodeOutputs } from "../components/AnalysisNodeOutputs";

import { fetchRuns, runAnalysis, fetchAnalysisIntents } from "../services/api";

import type { AnalysisResult, RunSummary, AnalysisIntentInfo } from "../services/api";

export type AnalysisCategory =
  | "statistical"
  | "timeseries"
  | "network"
  | "hypothesis";

export interface MenuItem {
  id: string;
  label: string;
  icon: string;
  category: AnalysisCategory;
  intent: string;
  description: string;
  parameters: ParameterConfig[];
  nodes?: AnalysisIntentInfo["nodes"];
}

export type ParameterValue = string | number | boolean | null;

export interface ParameterConfig {
  name: string;
  type: "text" | "number" | "select" | "boolean" | "run-select";
  label: string;
  description?: string;
  default?: ParameterValue;
  min?: number;
  max?: number;
  step?: number;
  options?: { value: string; label: string }[];
  required?: boolean;
}

const ANALYSIS_MENU_ITEMS: MenuItem[] = [
  {
    id: "stat_summary",
    label: "기술 통계량",
    icon: "",
    category: "statistical",
    intent: "analyze_statistical",
    description: "메트릭별 평균, 표준편차, 최솟값, 최댓값, 중앙값 등 기초 통계량 계산",
    parameters: [
      {
        name: "run_id",
        type: "run-select",
        label: "평가 실행",
        description: "분석할 평가 실행 선택",
        required: true,
      },
      {
        name: "metrics",
        type: "text",
        label: "메트릭 필터",
        description: "쉼표로 구분된 메트릭 목록 (비워두면 전체)",
        default: "",
      },
    ],
  },
  {
    id: "nlp_analysis",
    label: "NLP 분석",
    icon: "",
    category: "statistical",
    intent: "analyze_nlp",
    description: "질문/답변 텍스트 통계, 키워드 추출 및 유형 분석",
    parameters: [
      {
        name: "run_id",
        type: "run-select",
        label: "평가 실행",
        required: true,
      },
    ],
  },
  {
    id: "dataset_features",
    label: "데이터셋 특성 분석",
    icon: "",
    category: "statistical",
    intent: "analyze_dataset_features",
    description: "텍스트/컨텍스트 특성 및 메트릭 상관·중요도를 분석",
    parameters: [
      {
        name: "run_id",
        type: "run-select",
        label: "평가 실행",
        required: true,
      },
      {
        name: "min_samples",
        type: "number",
        label: "최소 샘플 수",
        description: "상관/중요도 계산에 필요한 최소 샘플 수",
        default: 5,
        min: 3,
        max: 100,
        step: 1,
      },
      {
        name: "max_graph_nodes",
        type: "number",
        label: "그래프 노드 상한",
        description: "엔티티 그래프 최대 노드 수",
        default: 50,
        min: 10,
        max: 200,
        step: 10,
      },
      {
        name: "max_graph_edges",
        type: "number",
        label: "그래프 엣지 상한",
        description: "엔티티 그래프 최대 엣지 수",
        default: 200,
        min: 20,
        max: 500,
        step: 20,
      },
      {
        name: "include_vectors",
        type: "boolean",
        label: "특성 벡터 포함",
        description: "개별 샘플의 특성 벡터를 결과에 포함",
        default: false,
      },
    ],
  },
  {
    id: "causal_analysis",
    label: "인과 분석",
    icon: "",
    category: "statistical",
    intent: "analyze_causal",
    description: "요인별 영향도 분석 및 근본 원인 도출",
    parameters: [
      {
        name: "run_id",
        type: "run-select",
        label: "평가 실행",
        required: true,
      },
    ],
  },
  {
    id: "playbook_analysis",
    label: "개선 플레이북",
    icon: "",
    category: "statistical",
    intent: "analyze_playbook",
    description: "플레이북 기반 진단 및 개선 가이드 생성",
    parameters: [
      {
        name: "run_id",
        type: "run-select",
        label: "평가 실행",
        required: true,
      },
      {
        name: "enable_llm",
        type: "boolean",
        label: "LLM 심층 분석",
        description: "LLM을 사용하여 상세 인사이트 생성",
        default: false,
      },
    ],
  },
  {
    id: "ts_anomaly",
    label: "이상 탐지",
    icon: "",
    category: "timeseries",
    intent: "detect_anomalies",
    description: "STOMP 알고리즘 기반 성능 이상 패턴 탐지",
    parameters: [
      {
        name: "run_id",
        type: "run-select",
        label: "평가 실행",
        required: true,
      },
      {
        name: "window_size",
        type: "number",
        label: "윈도우 크기",
        description: "이상 탐지 윈도우 크기",
        default: 200,
        min: 50,
        max: 500,
        step: 50,
      },
    ],
  },
  {
    id: "ts_forecast",
    label: "성능 예측",
    icon: "",
    category: "timeseries",
    intent: "forecast_performance",
    description: "지수 평활 기반 미래 성능 예측",
    parameters: [
      {
        name: "run_id",
        type: "run-select",
        label: "평가 실행",
        required: true,
      },
      {
        name: "forecast_horizon",
        type: "number",
        label: "예측 기간",
        description: "앞으로 예측할 실행 횟수",
        default: 3,
        min: 1,
        max: 10,
        step: 1,
      },
    ],
  },
  {
    id: "net_analysis",
    label: "메트릭 네트워크",
    icon: "",
    category: "network",
    intent: "analyze_network",
    description: "메트릭 간 상관관계 네트워크 분석 및 시각화",
    parameters: [
      {
        name: "run_id",
        type: "run-select",
        label: "평가 실행",
        required: true,
      },
      {
        name: "min_correlation",
        type: "number",
        label: "최소 상관계수",
        description: "네트워크 에지 생성 최소 상관계수 절대값",
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.1,
      },
    ],
  },
  {
    id: "hyp_generate",
    label: "가설 생성",
    icon: "",
    category: "hypothesis",
    intent: "generate_hypotheses",
    description: "HypoGeniC 기반 자동 가설 생성",
    parameters: [
      {
        name: "run_id",
        type: "run-select",
        label: "평가 실행",
        required: true,
      },
      {
        name: "method",
        type: "select",
        label: "생성 방법",
        options: [
          { value: "heuristic", label: "Heuristic (데이터 기반)" },
          { value: "hyporefine", label: "HypoRefine (문헌 통합)" },
          { value: "union", label: "Union Methods (하이브리드)" },
        ],
        default: "heuristic",
      },
      {
        name: "num_hypotheses",
        type: "number",
        label: "가설 개수",
        description: "생성할 가설의 개수",
        default: 5,
        min: 1,
        max: 20,
        step: 1,
      },
    ],
  },
];

const CATEGORY_LABELS: Record<AnalysisCategory, { label: string; icon: string }> = {
  statistical: { label: "기술통계", icon: "" },
  timeseries: { label: "시계열 분석", icon: "" },
  network: { label: "네트워크 분석", icon: "" },
  hypothesis: { label: "가설 생성", icon: "" },
};

export default function ComprehensiveAnalysis() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [intents, setIntents] = useState<AnalysisIntentInfo[]>([]);
  const [selectedMenuItem, setSelectedMenuItem] = useState<MenuItem | null>(null);
  const [parameterValues, setParameterValues] = useState<Record<string, ParameterValue>>({});
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<AnalysisCategory>>(
    new Set(["statistical"])
  );

  useEffect(() => {
    const loadData = async () => {
      try {
        const [runsData, intentsData] = await Promise.all([
          fetchRuns(),
          fetchAnalysisIntents()
        ]);
        setRuns(runsData);
        setIntents(intentsData);
      } catch (err) {
        console.error("데이터 로드 실패:", err);
      }
    };
    loadData();
  }, []);

  const dynamicMenuItems = useMemo(() => {
    if (intents.length === 0) return ANALYSIS_MENU_ITEMS;

    const mergedItems: MenuItem[] = [];
    const existingIntents = new Set(ANALYSIS_MENU_ITEMS.map(item => item.intent));

    for (const item of ANALYSIS_MENU_ITEMS) {
      const apiIntent = intents.find(i => i.intent === item.intent);
      if (apiIntent) {
        mergedItems.push({
          ...item,
          label: apiIntent.label || item.label,
          description: apiIntent.description || item.description,
          nodes: apiIntent.nodes
        });
      } else {
        mergedItems.push(item);
      }
    }

    for (const intent of intents) {
      if (!existingIntents.has(intent.intent)) {
        let category: AnalysisCategory = "statistical";
        if (intent.category && ["statistical", "timeseries", "network", "hypothesis"].includes(intent.category)) {
            category = intent.category as AnalysisCategory;
        }

        mergedItems.push({
          id: intent.intent,
          label: intent.label,
          icon: "",
          category: category,
          intent: intent.intent,
          description: intent.description,
          nodes: intent.nodes,
          parameters: [
            {
              name: "run_id",
              type: "run-select",
              label: "평가 실행",
              description: "분석할 평가 실행 선택",
              required: true,
            }
          ]
        });
      }
    }

    return mergedItems;
  }, [intents]);

  const handleMenuItemClick = useCallback((item: MenuItem) => {
    setSelectedMenuItem(item);
    setAnalysisResult(null);
    setError(null);

    const defaultValues: Record<string, ParameterValue> = {};
    for (const param of item.parameters) {
      defaultValues[param.name] = param.default ?? "";
    }
    setParameterValues(defaultValues);
    setSelectedRunId("");
  }, []);

  const toggleCategory = useCallback((category: AnalysisCategory) => {
    setExpandedCategories((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(category)) {
        newSet.delete(category);
      } else {
        newSet.add(category);
      }
      return newSet;
    });
  }, []);

  const handleParameterChange = useCallback((name: string, value: ParameterValue) => {
    setParameterValues((prev) => ({
      ...prev,
      [name]: value,
    }));
  }, []);

  const handleRunAnalysis = useCallback(async () => {
    if (!selectedMenuItem) return;

    for (const param of selectedMenuItem.parameters) {
      if (param.required && !parameterValues[param.name]) {
        setError(`${param.label}은(는) 필수 항목입니다.`);
        return;
      }
    }

    setIsLoading(true);
    setError(null);

    try {
      const queryValue = parameterValues.query;
      const runValue = parameterValues.run_id;
      const queryText = typeof queryValue === "string" ? queryValue : "";
      const runId = typeof runValue === "string" && runValue ? runValue : selectedRunId;
      const result = await runAnalysis(queryText, runId, selectedMenuItem.intent, parameterValues);
      setAnalysisResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "분석 실패");
      console.error("분석 오류:", err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedMenuItem, parameterValues, selectedRunId]);

  const menuItemsByCategory = useMemo(() => {
    const grouped: Record<AnalysisCategory, MenuItem[]> = {
      statistical: [],
      timeseries: [],
      network: [],
      hypothesis: [],
    };
    for (const item of dynamicMenuItems) {
      if (grouped[item.category]) {
        grouped[item.category].push(item);
      } else {
        if (!grouped["statistical"]) grouped["statistical"] = [];
        grouped["statistical"].push(item);
      }
    }
    return grouped;
  }, [dynamicMenuItems]);

  return (
    <>
      <Layout>
        <div className="container mx-auto px-4">
          <div className="mb-6">
            <Link
              to="/analysis"
              className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800"
            >
              <svg
                className="mr-2"
                width="20"
                height="20"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
              </svg>
              <span className="ml-2 font-medium">통합 분석</span>
            </Link>
          </div>

          <div className="flex gap-6 h-[calc(100vh-180px)]">
            <aside className="w-72 bg-white rounded-lg shadow flex flex-col overflow-hidden">
              <div className="p-4 border-b bg-gray-50">
                <h1 className="text-lg font-bold text-gray-800">분석 메뉴</h1>
                <p className="text-xs text-gray-500 mt-1">기능을 선택하여 분석을 시작하세요</p>
              </div>

              <div className="flex-1 overflow-y-auto p-2">
                {Object.entries(menuItemsByCategory).map(([category, items]) => {
                  const cat = category as AnalysisCategory;
                  const catInfo = CATEGORY_LABELS[cat];
                  const isExpanded = expandedCategories.has(cat);

                  return (
                    <div key={category} className="mb-2">
                      <button
                        onClick={() => toggleCategory(cat)}
                        className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                      >
                        <span className="flex items-center gap-2">
                          {catInfo.icon && <span>{catInfo.icon}</span>}
                          <span>{catInfo.label}</span>
                        </span>
                        <svg
                          className={`w-4 h-4 transition-transform ${
                            isExpanded ? "rotate-90" : ""
                          }`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 5l7 7-7 7"
                          />
                        </svg>
                      </button>

                      {isExpanded && (
                        <div className="ml-4 mt-1 space-y-1">
                          {items.map((item) => (
                            <button
                              key={item.id}
                              onClick={() => handleMenuItemClick(item)}
                              className={`w-full flex items-start gap-2 px-3 py-2 text-sm rounded-md transition-colors ${
                                selectedMenuItem?.id === item.id
                                  ? "bg-blue-100 text-blue-800 font-medium"
                                  : "text-gray-600 hover:bg-gray-50"
                              }`}
                            >
                              {item.icon && <span className="mt-0.5">{item.icon}</span>}
                              <div className="text-left">
                                <div>{item.label}</div>
                              </div>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </aside>

            <main className="flex-1 flex flex-col gap-4 overflow-hidden">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold mb-2">
                  {selectedMenuItem ? (
                    <>
                      {selectedMenuItem.label}
                    </>
                  ) : (
                    "분석 메뉴를 선택하세요"
                  )}
                </h2>
                {selectedMenuItem && (
                  <p className="text-sm text-gray-600 mb-4">
                    {selectedMenuItem.description}
                  </p>
                )}

                {selectedMenuItem ? (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      {selectedMenuItem.parameters.map((param) => (
                        <ParameterInput
                          key={param.name}
                          config={param}
                          value={parameterValues[param.name]}
                          runs={runs}
                          onValueChange={(value) => handleParameterChange(param.name, value)}
                        />
                      ))}
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={handleRunAnalysis}
                        disabled={isLoading}
                        className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                      >
                        {isLoading ? "분석 중..." : "분석 실행"}
                      </button>
                      <button
                        onClick={() => {
                          setSelectedMenuItem(null);
                          setAnalysisResult(null);
                          setError(null);
                          setParameterValues({});
                          setSelectedRunId("");
                        }}
                        className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                      >
                        초기화
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <p>좌측 메뉴에서 분석 기능을 선택하세요.</p>
                  </div>
                )}
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start gap-2">
                    <div className="flex-1">
                      <h3 className="font-medium text-red-800">오류</h3>
                      <p className="text-sm text-red-600 mt-1">{error}</p>
                    </div>
                    <button
                      onClick={() => setError(null)}
                      className="text-red-500 hover:text-red-700"
                    >
                      X
                    </button>
                  </div>
                </div>
              )}

              {analysisResult && (
                <div className="flex-1 bg-white rounded-lg shadow p-6 overflow-y-auto">
                  <h3 className="text-lg font-bold mb-4">분석 결과</h3>
                  <AnalysisResultDisplay
                    result={analysisResult}
                    nodeDefinitions={selectedMenuItem?.nodes}
                  />
                </div>
              )}
            </main>
          </div>
        </div>
      </Layout>
    </>
  );
}

interface ParameterInputProps {
  config: ParameterConfig;
  value: ParameterValue;
  runs: RunSummary[];
  onValueChange: (value: ParameterValue) => void;
}

function ParameterInput({ config, value, runs, onValueChange }: ParameterInputProps) {
  const renderInput = () => {
    switch (config.type) {
      case "run-select":
        return (
          <select
            className={`w-full p-2 border rounded-md bg-white ${
              config.required && !value ? "border-red-300" : "border-gray-300"
            }`}
            value={typeof value === "string" ? value : ""}
            onChange={(e) => onValueChange(e.target.value)}
            required={config.required}
          >
            <option value="">-- 실행을 선택하세요 --</option>
            {runs.map((run) => (
              <option key={run.run_id} value={run.run_id}>
                {run.run_id.slice(0, 12)}... ({run.model_name}) -{" "}
                {new Date(run.started_at).toLocaleDateString("ko-KR")}
              </option>
            ))}
          </select>
        );

      case "select":
        return (
          <select
            className="w-full p-2 border border-gray-300 rounded-md bg-white"
            value={typeof value === "string" ? value : ""}
            onChange={(e) => onValueChange(e.target.value)}
          >
            {config.options?.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        );

      case "boolean":
        return (
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              className="w-4 h-4"
              checked={Boolean(value)}
              onChange={(e) => onValueChange(e.target.checked)}
            />
            <span className="text-sm text-gray-700">활성화</span>
          </label>
        );

      case "number":
        return (
          <input
            type="number"
            className="w-full p-2 border border-gray-300 rounded-md bg-white"
            value={typeof value === "number" ? value : ""}
            onChange={(e) => onValueChange(Number(e.target.value))}
            min={config.min}
            max={config.max}
            step={config.step}
          />
        );

      case "text":
      default:
        return (
          <input
            type="text"
            className="w-full p-2 border border-gray-300 rounded-md bg-white"
            value={typeof value === "string" ? value : ""}
            onChange={(e) => onValueChange(e.target.value)}
          />
        );
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {config.label}
        {config.required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {renderInput()}
      {config.description && (
        <p className="text-xs text-gray-500 mt-1">{config.description}</p>
      )}
    </div>
  );
}

interface AnalysisResultDisplayProps {
  result: AnalysisResult;
  nodeDefinitions?: AnalysisIntentInfo["nodes"];
}

function AnalysisResultDisplay({ result, nodeDefinitions }: AnalysisResultDisplayProps) {
  const finalOutput = result.final_output || {};
  const nodeResults = result.node_results || {};
  const markdown = typeof finalOutput.markdown === "string" ? finalOutput.markdown : null;

  return (
    <div className="space-y-6">
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-600">Intent:</span>{" "}
            <span className="text-gray-900">{result.intent}</span>
          </div>
          <div>
            <span className="font-medium text-gray-600">완료:</span>{" "}
            <span className={result.is_complete ? "text-green-600" : "text-yellow-600"}>
              {result.is_complete ? "완료" : "진행 중"}
            </span>
          </div>
          {result.duration_ms && (
            <div>
              <span className="font-medium text-gray-600">소요 시간:</span>{" "}
              <span className="text-gray-900">{(result.duration_ms / 1000).toFixed(2)}초</span>
            </div>
          )}
        </div>
      </div>

      {Object.keys(finalOutput).length > 0 && (
        <div>
          <h4 className="text-md font-bold mb-3">최종 결과</h4>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <pre className="text-sm overflow-auto max-h-96">
              {JSON.stringify(finalOutput, null, 2)}
            </pre>
          </div>
        </div>
      )}

      <div>
        <AnalysisNodeOutputs
          nodeResults={nodeResults}
          nodeDefinitions={nodeDefinitions}
          title="노드별 상세 결과"
        />
      </div>

      {markdown && (
        <div>
          <h4 className="text-md font-bold mb-3">보고서</h4>
          <div className="border border-gray-200 rounded-lg p-4">
            <MarkdownContent text={markdown} />
          </div>
        </div>
      )}
    </div>
  );
}
